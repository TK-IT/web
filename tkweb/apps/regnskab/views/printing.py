import io
import re
import random
import logging
import datetime
from decimal import Decimal
from collections import defaultdict
from constance import config

from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.db.models import F, Min
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.views.generic import FormView

import tktitler as tk

from tkweb.apps.regnskab.models import (
    Session, Purchase, Transaction, Sheet, PurchaseKind,
    compute_balance, get_profiles_title_status,
)
from tkweb.apps.regnskab.rules import get_max_debt, get_default_prices
from tkweb.apps.regnskab.forms import BalancePrintForm
from tkweb.apps.regnskab.texrender import tex_to_pdf, RenderError, pdfnup
from .auth import regnskab_permission_required_method

try:
    from tkweb.apps.uniprint.api import print_new_document
except ImportError:
    from tkweb.apps.regnskab.texrender import print_new_document

logger = logging.getLogger('regnskab')


BALANCE_PRINT_TEX = r"""
\documentclass[danish,a4paper,12pt]{memoir}
\usepackage[utf8]{inputenc}
\usepackage[danish]{babel}
\usepackage{siunitx}
\usepackage{a4}
\usepackage{multirow}
\usepackage{longtable}
\usepackage{xcolor}
\usepackage{colortbl}
\sisetup{output-decimal-marker={,}}
\setulmarginsandblock{17mm}{27mm}{*}
\setlrmarginsandblock{9mm}{5mm}{*}
\setlength{\headheight}{0pt}
\setlength{\headsep}{0pt}
\setlength{\footskip}{0pt}
\checkandfixthelayout
\pagestyle{empty}
\begin{document}
\strut \hfill \today\\[2mm]
\definecolor{pink}{rgb}{1,0.80,0.88}
\renewcommand{\hl}{\cellcolor{pink}}

\begin{longtable}{|p{6.3cm}|p{1.2cm}p{1.1cm}p{1.1cm}p{1.1cm}p{1.7cm}p{1.9cm}|p{1.7cm}|}
\hline
Siden sidste regning & Kasser & Guldøl & Øl & Vand & Diverse & Betalt & Gæld\\
År til dato & \num{%(price_ølkasse).2f} & \num{%(price_guldøl).2f} & \num{%(price_øl).2f} & \num{%(price_sodavand).2f} & & &\\
%(personer)s\hline
\end{longtable}
\newpage\phantom{A}\newpage
\begin{longtable}{|p{6.3cm}|p{1.2cm}p{1.1cm}p{1.1cm}p{1.1cm}p{1.7cm}p{1.9cm}|p{1.7cm}|}
\hline
Siden sidste regning & Kasser & Guldøl & Øl & Vand & Diverse & Betalt & Gæld\\
År til dato & \num{%(price_ølkasse).2f} & \num{%(price_guldøl).2f} & \num{%(price_øl).2f} & \num{%(price_sodavand).2f} & & &\\
\hline
Månedstotal & \hfill \num{%(last_ølkasse).2f} & \hfill \num{%(last_guldøl)d} & \hfill \num{%(last_øl)d} & \hfill \num{%(last_sodavand)d} & \hfill \num{%(last_andet).2f} & \hfill \num{%(last_betalt).2f} &\\
Årstotal & \hfill \num{%(total_ølkasse).2f} & \hfill \num{%(total_guldøl)d} & \hfill \num{%(total_øl)d} & \hfill \num{%(total_sodavand)d} & \hfill \num{%(total_andet).2f} & \hfill \num{%(total_betalt).2f} & \hfill \num{%(total_balance).2f}\\
\hline
\end{longtable}
\end{document}
"""

BALANCE_ROW = '\n'.join([
    r'\hline',
    r'\multirow{2}{6cm}{%(name)s} & %(last)s &\\',
    r'& %(total)s & \hfill %(hl)s{\num{%(balance).2f}}\\'])


def title_to_tex(s):
    tokens = [
        ('pow', r'\^[a-z]|\^[0-9]+', lambda s: '$^{%s}$' % s[1:]),
        ('hat', r'\^', lambda s: '\\' + s + '{}'),
        ('escape', r'[$^\\{}]', lambda s: '\\' + s),
    ]
    pattern = '|'.join('(%s)' % pattern for name, pattern, r in tokens)

    def repl(mo):
        name, pattern, r = tokens[mo.lastindex - 1]
        return r(mo.group())

    return re.sub(pattern, repl, s)


class BalancePrint(FormView):
    form_class = BalancePrintForm
    template_name = 'regnskab/balance_print_form.html'

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        self.regnskab_session = get_object_or_404(
            Session.objects, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def get_tex_context_data(
        period=None, time=None, current_session_id=None, threshold=None
    ):
        if threshold is None:
            threshold = float('inf')
        if period is None:
            period = config.GFYEAR
        if time is None:
            time = timezone.now()

        purchase_qs = Purchase.objects.all().order_by().filter(
            row__sheet__period=period)
        purchase_qs = purchase_qs.annotate(
            name=F('kind__name'),
            sheet_id=F('row__sheet_id'),
            profile_id=F('row__profile_id'),
            session_id=F('row__sheet__session_id'))
        purchase_qs = purchase_qs.values_list(
            'sheet_id', 'name', 'profile_id', 'session_id', 'count')

        kinds = {
            (sheet_id, o.name): o.unit_price
            for o in PurchaseKind.objects.all()
            for sheet_id in o.sheets.all().values_list('id', flat=True)
        }

        kind_last_sheet = {}
        for sheet_id, name in kinds.keys():
            ex = kind_last_sheet.setdefault(name, sheet_id)
            if ex < sheet_id:
                kind_last_sheet[name] = sheet_id
        prices = {name: kinds[sheet_id, name]
                  for name, sheet_id in kind_last_sheet.items()}
        if not prices:
            prices = get_default_prices()

        counts = defaultdict(Decimal)
        cur_counts = defaultdict(Decimal)

        for sheet_id, name, profile_id, session_id, count in purchase_qs:
            if name in ('guldølkasse', 'sodavandkasse'):
                real_name = 'ølkasse'
                real_count = count * (kinds[sheet_id, name] /
                                      kinds[sheet_id, 'ølkasse'])
            elif name in ('ølkasse', 'ølkasser'):
                real_name = 'ølkasse'
                real_count = count
            else:
                real_name, real_count = name, count
            counts[profile_id, real_name] += real_count
            if session_id == current_session_id:
                cur_counts[profile_id, real_name] += real_count

        transaction_qs = Transaction.objects.all()
        period_start_date, = (
            Sheet.objects.filter(period=period).aggregate(Min('start_date')).values())
        period_start_time = timezone.get_current_timezone().localize(
            datetime.datetime.combine(period_start_date, datetime.time()))
        transaction_qs = transaction_qs.filter(time__gte=period_start_time)
        for o in transaction_qs:
            if o.kind == Transaction.PAYMENT:
                real_name = 'betalt'
                amount = -o.amount
            else:
                real_name = 'andet'
                amount = o.amount
            counts[o.profile_id, real_name] += amount
            if o.session_id == current_session_id:
                cur_counts[o.profile_id, real_name] += amount

        context = {}
        for name, unit_price in prices.items():
            context['price_%s' % name] = unit_price

        keys = 'ølkasse guldøl øl sodavand andet betalt'.split()
        for k in keys:
            context['total_%s' % k] = context['last_%s' % k] = Decimal()
        context['total_balance'] = Decimal()

        profiles = get_profiles_title_status(period=period, time=time)
        balances = compute_balance()

        context['personer'] = []
        for p in profiles:
            for k in keys:
                context['total_%s' % k] += counts[p.id, k]
                context['last_%s' % k] += cur_counts[p.id, k]
            p_context = {}
            p_context['balance'] = balances.get(p.id, 0)
            context['total_balance'] += p_context['balance']
            if p.title:
                if p.title.period is None:
                    title_str = title_to_tex(p.title.root)
                else:
                    title_str = tk.prefix(p.title, period, type='tex')
                p_context['alias'] = title_str
                p_context['name'] = '%s %s' % (title_str, p.name)
            else:
                p_context['alias'] = p_context['name'] = p.name
            p_context['last'] = {
                k: cur_counts.get((p.id, k), 0) for k in keys
            }
            p_context['total'] = {
                k: counts.get((p.id, k), 0) for k in keys
            }
            p_context['hl'] = p_context['balance'] > threshold
            if not p.status or p.status.end_time is not None:
                continue
            context['personer'].append(p_context)

        return context

    def get_tex_source(self, threshold):
        period = self.regnskab_session.period
        time = self.regnskab_session.send_time
        context = self.get_tex_context_data(
            period, time, self.regnskab_session.id, threshold
        )

        rows = []
        keys = 'ølkasse guldøl øl sodavand andet betalt'.split()
        FMT = dict(betalt='\\hfill \\num{%.2f}', andet='\\hfill \\num{%.2f}',
                   ølkasse='\\hfill \\num{%.1f}')
        for p_context in context['personer']:
            p_context['last'] = ' & '.join(
                FMT.get(k, '\\hfill \\num{%g}') % p_context['last'][k]
                for k in keys)
            p_context['total'] = ' & '.join(
                FMT.get(k, '\\hfill \\num{%g}') % p_context['total'][k]
                for k in keys)
            p_context['hl'] = '\\hl' if p_context['hl'] else ''
            rows.append(BALANCE_ROW % p_context)

        context['personer'] = '\n'.join(rows)

        tex_source = BALANCE_PRINT_TEX % context

        return tex_source

    def form_valid(self, form):
        mode = form.cleaned_data['mode']
        should_highlight = form.cleaned_data['highlight']
        threshold = get_max_debt() if should_highlight else None

        tex_source = self.get_tex_source(threshold=threshold)
        if mode == BalancePrintForm.SOURCE:
            return HttpResponse(tex_source,
                                content_type='text/plain; charset=utf8')

        try:
            pdf = tex_to_pdf(tex_source)
        except RenderError as exn:
            form.add_error(None, str(exn) + ': ' + exn.output)
            return self.form_invalid(form)

        try:
            pdf = pdfnup(pdf)
        except RenderError as exn:
            form.add_error(None, str(exn) + ': ' + exn.output)
            return self.form_invalid(form)

        if mode == BalancePrintForm.PDF:
            return HttpResponse(pdf, content_type='application/pdf')

        if mode != BalancePrintForm.PRINT:
            raise ValueError(mode)

        filename = 'regnskab_%s.pdf' % self.regnskab_session.pk
        username = self.request.user.username
        fake = settings.DEBUG
        try:
            output = print_new_document(io.BytesIO(pdf),
                                        filename=filename,
                                        username=username,
                                        printer='A2',
                                        duplex=False, fake=fake)
        except Exception as exn:
            if settings.DEBUG and not isinstance(exn, ValidationError):
                raise
            form.add_error(None, str(exn))
            return self.form_invalid(form)

        logger.info("%s: Udskriv opgørelse id=%s på A2",
                    self.request.user, self.regnskab_session.pk)

        url = reverse('regnskab:session_update',
                      kwargs=dict(pk=self.regnskab_session.id),
                      current_app=self.request.resolver_match.namespace)
        return HttpResponseRedirect(url + '?print=success')
