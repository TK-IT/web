import io
import random
from decimal import Decimal
from collections import defaultdict

from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.db.models import F, Min
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.views.generic import FormView

from regnskab.models import (
    Session, Purchase, Transaction, Sheet, PurchaseKind,
    tk_prefix, compute_balance, get_default_prices,
    get_profiles_title_status,
)
from regnskab.forms import BalancePrintForm
from regnskab.texrender import tex_to_pdf, RenderError, pdfnup
from .auth import regnskab_permission_required_method

try:
    from uniprint.api import print_new_document
except ImportError:
    from regnskab.texrender import print_new_document


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
\setulmarginsandblock{.8cm}{*}{1}
\setlrmarginsandblock{.7cm}{*}{1}
\setlength{\headheight}{0pt}
\setlength{\headsep}{0pt}
\setlength{\footskip}{0pt}
\checkandfixthelayout
\pagestyle{empty}
\begin{document}
\strut \hfill \today\\
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
    r'\multirow{2}{6cm}{%(name)-30s} & %(last)s &\\',
    r'& %(total)s & \hfill %(hl)s{\num{%(balance).2f}}\\'])


class BalancePrint(FormView):
    form_class = BalancePrintForm
    template_name = 'regnskab/balance_print_form.html'

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        self.regnskab_session = get_object_or_404(
            Session.objects, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_tex_source(self, threshold):
        period = self.regnskab_session.period

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
            (o.sheet_id, o.name): o.unit_price
            for o in PurchaseKind.objects.all()}

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
            if session_id == self.regnskab_session.id:
                cur_counts[profile_id, real_name] += real_count

        transaction_qs = Transaction.objects.all()
        period_start_time, = (
            Sheet.objects.filter(period=period).aggregate(Min('start_date')).values())
        transaction_qs = transaction_qs.filter(time__gte=period_start_time)
        for o in transaction_qs:
            if o.kind == Transaction.PAYMENT:
                real_name = 'betalt'
                amount = -o.amount
            else:
                real_name = 'andet'
                amount = o.amount
            counts[o.profile_id, real_name] += amount
            if o.session_id == self.regnskab_session.id:
                cur_counts[o.profile_id, real_name] += amount

        context = {}
        for name, unit_price in prices.items():
            context['price_%s' % name] = unit_price

        keys = 'ølkasse guldøl øl sodavand andet betalt'.split()
        for k in keys:
            context['total_%s' % k] = context['last_%s' % k] = Decimal()
        context['total_balance'] = Decimal()

        time = self.regnskab_session.send_time
        profiles = get_profiles_title_status(period=period, time=time)
        if period == 2016 and timezone.now().year == 2016:
            hængere = [i for i in range(len(profiles))
                       if not profiles[i].title]
            best = {profiles[i].title.root: i
                    for i in range(len(profiles))
                    if profiles[i].title and
                    profiles[i].title.period == 2016}
            assert best['FORM'] < best['NF']
            nf = profiles[best['NF']]
            del profiles[best['NF']]
            nf.name = 'Taberen'
            nf.title = None
            profiles.insert(random.choice(hængere), nf)
            FORM = profiles[best['FORM']]
            del profiles[best['FORM']]
            profiles.insert(0, FORM)
            FORM.name = 'Vinderen'
            FORM.title = None
        balances = compute_balance()

        rows = []
        for p in profiles:
            context['total_balance'] += balances.get(p.id, 0)
            for k in keys:
                context['total_%s' % k] += counts[p.id, k]
                context['last_%s' % k] += cur_counts[p.id, k]
            p_context = {}
            if p.title:
                age = p.title.age(period)
                if age > 4:
                    tex_prefix = 'T$^{%s}$O' % (age - 3)
                else:
                    tex_prefix = tk_prefix(age)
                if p.title.root == 'KASS':
                    root = 'KA\\$\\$'
                else:
                    root = p.title.root
                p_context['name'] = '%s%s %s' % (tex_prefix, root, p.name)
            else:
                p_context['name'] = p.name
            FMT = dict(betalt='\\hfill \\num{%.2f}', andet='\\hfill \\num{%.2f}',
                       ølkasse='\\hfill \\num{%.1f}')
            p_context['last'] = ' & '.join(
                FMT.get(k, '\\hfill \\num{%g}') % cur_counts.get((p.id, k), 0)
                for k in keys)
            p_context['total'] = ' & '.join(
                FMT.get(k, '\\hfill \\num{%g}') % counts.get((p.id, k), 0)
                for k in keys)
            p_context['balance'] = balances[p.id]
            p_context['hl'] = '\\hl' if balances[p.id] > threshold else ''
            if not p.status or p.status.end_time is not None:
                continue
            rows.append(BALANCE_ROW % p_context)

        context['personer'] = '\n'.join(rows)

        tex_source = BALANCE_PRINT_TEX % context

        return tex_source

    def form_valid(self, form):
        mode = form.cleaned_data['mode']
        should_highlight = form.cleaned_data['highlight']
        threshold = 250 if should_highlight else float('inf')

        tex_source = self.get_tex_source(threshold=threshold)
        if mode == BalancePrintForm.SOURCE:
            return HttpResponse(tex_source,
                                content_type='text/plain; charset=utf8')

        try:
            pdf = tex_to_pdf(tex_source)
        except RenderError as exn:
            form.add_error(None, str(exn))
            return self.form_invalid(form)

        try:
            pdf = pdfnup(pdf)
        except RenderError as exn:
            form.add_error(None, str(exn))
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
                                        duplex=False, fake=fake)
        except Exception as exn:
            form.add_error(None, str(exn))
            return self.form_invalid(form)

        url = reverse('session_update',
                      kwargs=dict(pk=self.regnskab_session.id))
        return HttpResponseRedirect(url + '?print=success')
