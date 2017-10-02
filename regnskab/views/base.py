import difflib
import logging
import operator
import itertools
from decimal import Decimal
from collections import Counter
import json

from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import HttpResponse
from django.db.models import F, Sum
from django.utils import timezone
from django.utils.html import format_html, format_html_join
from django.template.defaultfilters import floatformat
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import (
    TemplateView, FormView, View,
)
from django.template.response import TemplateResponse
from regnskab.forms import (
    SheetCreateForm, AnonymousEmailTemplateForm, SheetRowForm,
    TransactionBatchForm, BalancePrintForm,
    ProfileListForm,
)
from regnskab.models import (
    Sheet, SheetRow, SheetStatus, Profile, Alias, Title, Email,
    EmailTemplate, Session, PurchaseKind,
    Transaction, Purchase,
    compute_balance, get_inka,
    config, get_profiles_title_status,
)
from regnskab.rules import (
    get_max_debt, get_max_debt_after_payment, get_default_prices,
)
from .auth import regnskab_permission_required_method
from regnskab.utils import sum_matrix

import tktitler as tk

logger = logging.getLogger('regnskab')


class Home(TemplateView):
    template_name = 'regnskab/home.html'

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        try:
            latest_session = Session.objects.latest()
        except Session.DoesNotExist:
            latest_session = None
        context_data['latest_session'] = latest_session
        context_data['inka'] = get_inka()
        try:
            email_template = EmailTemplate.objects.get(
                name='Standard')
        except EmailTemplate.DoesNotExist:
            email_template = None
        context_data['email_template'] = email_template
        return context_data


class Log(View):
    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        filename = logger.handlers[0].stream.name
        with open(filename, encoding='utf8') as fp:
            s = fp.read()
        return HttpResponse(s, content_type='text/plain; charset=utf8')


def already_sent_view(request, regnskab_session):
    context = dict(session=regnskab_session)
    return TemplateResponse(
        request, 'regnskab/already_sent.html', context=context)


class SessionCreate(TemplateView):
    template_name = 'regnskab/session_create.html'

    @regnskab_permission_required_method
    def post(self, request):
        try:
            email_template = EmailTemplate.objects.get(
                name='Standard')
        except EmailTemplate.DoesNotExist:
            email_template = None
        session = Session(created_by=self.request.user, period=config.GFYEAR,
                          email_template=email_template)
        session.save()
        logger.info("%s: Opret ny opgørelse id=%s",
                    self.request.user, session.pk)
        if session.email_template:
            session.regenerate_emails()
        return redirect('regnskab:session_update', pk=session.pk)


class SheetCreate(FormView):
    form_class = SheetCreateForm
    template_name = 'regnskab/sheet_create.html'

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        self.regnskab_session = get_object_or_404(
            Session.objects, pk=kwargs['session'])
        if not self.regnskab_session or self.regnskab_session.sent:
            return already_sent_view(request, self.regnskab_session)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['session'] = self.regnskab_session
        return context_data

    def get_initial(self):
        kinds = get_default_prices()
        return dict(kinds='\n'.join('%s %s' % x for x in kinds),
                    period=config.GFYEAR)

    def form_valid(self, form):
        from regnskab.images.extract import extract_images

        data = form.cleaned_data
        sheet = Sheet(name=data['name'],
                      start_date=data['start_date'],
                      end_date=data['end_date'],
                      period=data['period'],
                      created_by=self.request.user,
                      session=self.regnskab_session,
                      image_file=data['image_file'])
        kinds = [
            PurchaseKind.get_or_create(
                name=kind['name'],
                position=i + 1,
                unit_price=kind['unit_price'])
            for i, kind in enumerate(data['kinds'])]
        if data['image_file']:
            # extract_images sets sheet.row_image
            try:
                images, rows, purchases = extract_images(sheet, kinds)
            except Exception as exn:
                if settings.DEBUG and not isinstance(exn, ValidationError):
                    raise
                form.add_error(None, exn)
                return self.form_invalid(form)
        else:
            images, rows, purchases = [], [], []
        sheet.save()
        for o in images + rows:
            o.sheet = o.sheet  # Update sheet_id
        for o in images + rows:
            o.save()
        for o in kinds:
            o.sheets.add(sheet)
        for o in purchases:
            o.row = o.row  # Update row_id
        Purchase.objects.bulk_create(purchases)
        logger.info("%s: Opret ny krydsliste id=%s i opgørelse=%s " +
                    "med priser %s",
                    self.request.user, sheet.pk, self.regnskab_session.pk,
                    ' '.join('%s=%s' % (k['name'], k['unit_price'])
                             for k in data['kinds']))
        return redirect('regnskab:sheet_update', pk=sheet.pk)


class SheetDetail(TemplateView):
    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        if self.get_sheet().legacy_style():
            return ['regnskab/sheet_legacy.html']
        else:
            return ['regnskab/sheet_detail.html']

    def get(self, request, *args, **kwargs):
        s = self.get_sheet()  # type: Sheet
        qs = SheetRow.objects.filter(sheet=s)
        if not qs.exists():
            return redirect('regnskab:sheet_update', pk=s.pk)
        else:
            return super().get(request, *args, **kwargs)

    def get_sheet(self):
        return get_object_or_404(Sheet.objects, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context_data = super(SheetDetail, self).get_context_data(**kwargs)
        sheet = context_data['sheet'] = self.get_sheet()
        context_data['sheet_images'] = list(sheet.sheetimage_set.all())
        try:
            context_data['highlight_profile'] = int(
                self.request.GET['highlight_profile'])
        except (KeyError, ValueError):
            # Make highlight_profile something that does not
            # compare equal to a missing profile.
            context_data['highlight_profile'] = object()
        return context_data


def auto_prefix(t, period):
    return tk.prefix(t, period) if t.period else t.root


class SheetRowUpdate(FormView):
    template_name = 'regnskab/sheet_update.html'
    form_class = SheetRowForm

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        self.sheet = self.get_sheet()
        self.regnskab_session = self.sheet.session
        if not self.regnskab_session or self.regnskab_session.sent:
            return already_sent_view(request, self.regnskab_session)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        return dict(start_date=self.sheet.start_date,
                    end_date=self.sheet.end_date,
                    data=self.get_initial_data())

    def get_sheet(self):
        return get_object_or_404(Sheet.objects, pk=self.kwargs['pk'])

    def get_profiles(self):
        period = self.get_sheet().period

        profiles = get_profiles_title_status(period=period)
        aliases = {}
        for o in Alias.objects.filter(end_time=None):
            aliases.setdefault(o.profile_id, []).append(o)
        for o in Title.objects.all():
            aliases.setdefault(o.profile_id, []).append(o)

        result = []
        for i, profile in enumerate(profiles):
            titles = aliases.get(profile.id, ())
            titles_input = [auto_prefix(t, period) for t in titles]
            title_input = profile.title and auto_prefix(profile.title, period)
            result.append(dict(
                titles=titles_input, title=title_input, sort_key=i,
                name=profile.name, title_name=profile.title_name,
                id=profile.pk, in_current=profile.in_current))
        return result

    def get_initial_data(self):
        row_objects = self.sheet.rows()
        row_data = []
        for r in row_objects:
            counts = []
            for k in r['kinds']:
                counts.append(float(k.count) if k.id else None)

            row_data.append(dict(
                profile_id=r['profile'] and r['profile'].id,
                name=r['name'] or '',
                counts=counts,
                image=r['image'],
            ))
        return json.dumps(row_data, indent=2)

    def get_context_data(self, **kwargs):
        context_data = super(SheetRowUpdate, self).get_context_data(**kwargs)
        context_data['sheet'] = self.sheet
        profiles = self.get_profiles()
        context_data['profiles_json'] = json.dumps(profiles, indent=2)
        context_data['session'] = self.regnskab_session
        return context_data

    def clean(self, data_json):
        sheet = self.sheet
        kinds = list(sheet.columns())
        try:
            row_data = json.loads(data_json)
        except Exception as exn:
            raise ValidationError(str(exn))

        KEYS = {'profile_id', 'name', 'counts', 'image'}
        for row in row_data:
            if set(row.keys()) != KEYS:
                raise ValidationError("Invalid keys %s" % (set(row.keys()),))
            counts = row['counts']
            if not isinstance(counts, list):
                raise ValidationError("Wrong type of counts %s" % (counts,))
            if len(counts) != len(kinds):
                raise ValidationError("Wrong number of counts %s" % (counts,))
            p_id = row['profile_id']
            if p_id is not None and not isinstance(p_id, int):
                raise ValidationError("profile_id must be an int")

        profile_ids = set(row['profile_id'] for row in row_data
                          if row['profile_id'])
        profiles = {
            p.id: p for p in Profile.objects.filter(id__in=sorted(profile_ids))
        }
        missing = profile_ids - set(profiles.keys())
        if missing:
            raise ValidationError("Unknown profile IDs %s" % (missing,))
        return [
            dict(profile=row['profile_id'] and profiles[row['profile_id']],
                 name=row['name'],
                 position=i + 1,
                 image_start=row['image'] and row['image']['start'],
                 image_stop=row['image'] and row['image']['stop'],
                 kinds=[Purchase(kind=kind, count=c or 0)
                        for kind, c in zip(kinds, row['counts'])])
            for i, row in enumerate(row_data)
            if any(c is not None for c in row['counts']) or row['image']
        ]

    def save_rows(self, rows):
        def data(r):
            return (r['profile'] and r['profile'].id, r['name'], r['position'],
                    [(p.kind_id, p.count) for p in r['kinds']])

        sheet = self.sheet
        existing = sheet.rows()

        delete = []
        save = []

        for r_new, r_old in zip(rows, existing):
            if data(r_new) != data(r_old):
                delete.append(r_old)
                save.append(r_new)
        delete.extend(existing[len(rows):])
        save.extend(rows[len(existing):])

        for row in delete:
            logger.info("%s: Slet række %s i krydsliste %s: %r %r %s",
                        self.request.user, row['position'], sheet.pk,
                        row['name'], str(row['profile']),
                        ' '.join('%s=%s' % (c.kind.name, c.count)
                                 for c in row['kinds']))

        save_rows = []
        save_purchases = []
        for o in save:
            save_rows.append(SheetRow(
                sheet=sheet, profile=o['profile'],
                name=o['name'], position=o['position'],
                image_start=o['image_start'], image_stop=o['image_stop'],
            ))
            for c in o['kinds']:
                if c.count:
                    c.row = save_rows[-1]
                    save_purchases.append(c)
            logger.info("%s: Gem række %s i krydsliste %s: %r %r %s",
                        self.request.user, o['position'], sheet.pk,
                        o['name'], str(o['profile']),
                        ' '.join('%s=%s' % (c.kind.name, c.count)
                                 for c in o['kinds']))

        # print("Create %s, delete %s" % (len(save_rows), len(delete)))
        delete_ids = set(d['id'] for d in delete if d['id'])
        SheetRow.objects.filter(id__in=delete_ids).delete()
        for o in save_rows:
            o.save()
        for o in save_purchases:
            o.row = o.row  # Update o.row_id
        Purchase.objects.bulk_create(save_purchases)

    def form_valid(self, form):
        try:
            row_objects = self.clean(form.cleaned_data['data'])
        except ValidationError as exn:
            form.add_error(None, exn)
            return self.form_invalid(form)
        self.sheet.start_date = form.cleaned_data['start_date']
        self.sheet.end_date = form.cleaned_data['end_date']
        self.sheet.save()
        self.save_rows(row_objects)
        if self.regnskab_session.email_template:
            self.regnskab_session.regenerate_emails()
        return self.render_to_response(
            self.get_context_data(form=form, saved=True))


class Sortable:
    '''
    >>> s = Sortable('foo,-bar', {'foo', 'bar', 'baz'})
    >>> s.key_func({'foo': 1, 'bar': 2, 'baz': 3})
    [1, -2]
    >>> s.change_order_key('foo')
    '-foo,-bar'
    >>> s.change_order_key('bar')
    '-bar,foo'
    >>> s.change_order_key('baz')
    '-baz,foo,-bar'
    >>> s.default_sign = 1
    >>> s.change_order_key('baz')
    'baz,foo,-bar'
    '''

    default_sign = -1

    def __init__(self, sort_order_input, valid_keys):
        self.keys = []
        self.signs = []
        sort_order_list = (
            sort_order_input.split(',') if sort_order_input else ())
        for v in sort_order_list:
            if v.startswith('-'):
                v = v[1:]
                self.signs.append(-1)
            else:
                self.signs.append(1)
            self.keys.append(v)

        chosen_keys = set(self.keys)
        if len(chosen_keys) != len(self.keys):
            raise ValueError('duplicate keys')
        if not chosen_keys.issubset(valid_keys):
            raise ValueError('invalid keys')

    def key_func(self, value):
        return [s * (value.get(k) or 0)
                for k, s in zip(self.keys, self.signs)]

    def change_order_key(self, key):
        new_sign = self.default_sign
        keys = list(self.keys)
        signs = list(self.signs)
        try:
            i = keys.index(key)
        except ValueError:
            pass
        else:
            keys.pop(i)
            old_sign = signs.pop(i)
            if i == 0:
                new_sign = -old_sign
        keys.insert(0, key)
        signs.insert(0, new_sign)
        return ','.join(('-' if s == -1 else '') + k
                        for k, s in zip(keys, signs))


class PurchaseStatsTable:
    purchase_columns = (
        ('ølkasser', 'kasser', 1),
        ('øl', 'Øl', 0),
        ('ølkasse', 'ks', 1),
        ('guldøl', 'Guld', 0),
        ('guldølkasse', 'ks', 1),
        ('sodavand', 'Vand', 0),
        ('sodavandkasse', 'ks', 1),
        (Transaction.PURCHASE, 'Diverse', 2),
        (Transaction.PAYMENT, 'Betalt', 2),
    )
    columns_before = ()
    columns_after = ()

    hide_empty_columns = True
    html_class = 'tabular purchase-stats'
    sort_key = None
    sorter = None

    def __init__(self, request):
        self.request = request
        self.empty_columns = set(c for c, l, n in self.purchase_columns)
        self.rows = []

    @staticmethod
    def transpose_sparse(matrix):
        transpose = {}
        for k1, kvs in matrix.items():
            for k2, v in kvs.items():
                transpose.setdefault(k2, {})[k1] = v
        return transpose

    def add_data(self, matrix_columns, row_keys=None):
        matrix_rows = self.transpose_sparse(matrix_columns)
        if row_keys is None:
            row_keys = {k: k for k in matrix_rows}
        self.empty_columns -= matrix_columns.keys()
        rows = []
        for dict_key, row_key in sorted(row_keys.items()):
            row = matrix_rows.get(dict_key, {})
            row['key'] = row_key
            rows.append(row)
        self.rows.extend(rows)
        return rows

    def all_columns(self):
        return itertools.chain(self.columns_before,
                               self.purchase_columns,
                               self.columns_after)

    def get_header(self):
        keys_places = []
        labels = []
        for key, label, places in self.all_columns():
            if self.hide_empty_columns and key in self.empty_columns:
                continue
            keys_places.append((key, places))
            labels.append(label)
        return keys_places, labels

    def sortable(self, request_params, key='o'):
        sort_order_input = request_params.get(key) or ''
        valid_keys = set(k if isinstance(n, int) else n
                         for k, l, n in self.all_columns()
                         if n is not None)
        try:
            self.sorter = Sortable(sort_order_input, valid_keys)
        except ValueError:
            self.sorter = Sortable('', valid_keys)
        self.sorter_key = key

    def __str__(self):
        keys_places, labels = self.get_header()
        html_rows = []
        if self.sorter and self.sorter.keys:
            self.rows.sort(key=self.sorter.key_func)
        elif self.sort_key:
            if isinstance(self.sort_key, str):
                sort_key = [self.sort_key]
            else:
                sort_key = self.sort_key
            self.rows.sort(key=operator.itemgetter(*sort_key))

        if self.sorter is None:
            header = format_html_join('\n', '<th>{}</th>', zip(labels))
        else:
            fmt = '<th class="{c}"><a href="?{qs}">{h}</a></th>'
            header_cells = []
            for (key, places), label in zip(keys_places, labels):
                if places is None:
                    header_cells.append(format_html('<th>{}</th>', label))
                else:
                    if isinstance(places, int):
                        v = self.sorter.change_order_key(key)
                    else:
                        v = self.sorter.change_order_key(places)
                    qs = self.request.GET.copy()
                    qs[self.sorter_key] = v
                    header_cells.append(format_html(
                        fmt, qs=qs.urlencode(),
                        c=key, h=label))
            header = format_html_join('\n', '{}', zip(header_cells))

        for r in self.rows:
            html_row = []
            for key, places in keys_places:
                value = r.get(key)
                if isinstance(places, int):
                    if value is None:
                        value = '\N{EM DASH}'
                    else:
                        if key == Transaction.PAYMENT:
                            value = -value
                        value = floatformat(value, places)
                html_row.append((key, value))
            html_rows.append(format_html_join(
                '\n', '<td class="{}">{}</td>', html_row))
        body = format_html_join('\n', '<tr>\n{}\n</tr>', zip(html_rows))
        return format_html(
            '<table class="{html_class}">\n' +
            '<thead>\n<tr>\n{header}\n</tr>\n</thead>\n' +
            '<tbody>\n{body}\n</tbody>\n</table>',
            html_class=self.html_class,
            header=header, body=body)


class SessionList(TemplateView):
    template_name = 'regnskab/session_list.html'

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def transpose_sparse(matrix):
        transpose = {}
        for k1, kvs in matrix.items():
            for k2, v in kvs.items():
                transpose.setdefault(k2, {})[k1] = v
        return transpose

    @staticmethod
    def merge_legacy_data(by_sheet_time, by_sheet, period):
        if not by_sheet_time:
            return
        date_to_sheet = dict(
            Sheet.objects.filter(session=None, period=period).values_list(
                'end_date', 'id'))
        for col_key, column in by_sheet_time.items():
            output = by_sheet.setdefault(col_key, {})
            for time, v in column.items():
                sheet_id = date_to_sheet[time.date()]
                output[sheet_id] = v

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        try:
            period = int(self.request.GET['year'])
        except (ValueError, KeyError):
            period = config.GFYEAR

        by_year = sum_matrix(
            Purchase.objects.all(),
            'kind__name', 'row__sheet__period', 'count')
        by_year.update(sum_matrix(
            Transaction.objects.all(), 'kind', 'period', 'amount'))
        period_table = PurchaseStatsTable(self.request)
        period_table.columns_before = (('period', 'Årgang', 'key'),)
        period_table.sortable(self.request.GET, 'y')
        for r in period_table.add_data(by_year):
            r['period'] = format_html(
                '<a href="?year={0}">{0}</a>', r['key'])

        purchases_by_session_qs = Purchase.objects.filter(
            row__sheet__session__period=period)
        by_session = sum_matrix(
            purchases_by_session_qs,
            'kind__name', 'row__sheet__session_id', 'count')
        purchases_by_sheet_qs = Purchase.objects.filter(
            row__sheet__session=None,
            row__sheet__period=period)
        by_sheet = sum_matrix(
            purchases_by_sheet_qs,
            'kind__name', 'row__sheet_id', 'count')

        transactions_by_session_qs = Transaction.objects.filter(
            session__period=period)
        by_session.update(sum_matrix(
            transactions_by_session_qs, 'kind', 'session_id', 'amount'))
        transactions_by_sheet_qs = Transaction.objects.filter(
            session=None, period=period)
        by_sheet_time = sum_matrix(
            transactions_by_sheet_qs, 'kind', 'time', 'amount')
        self.merge_legacy_data(by_sheet_time, by_sheet, period)

        session_table = PurchaseStatsTable(self.request)
        session_table.columns_before = (('date', 'Dato', 'raw_date'),)
        session_table.sort_key = 'raw_date'
        session_table.sortable(self.request.GET)
        sheets = {s.pk: s for s in
                  Sheet.objects.filter(session=None, period=period)}
        for row in session_table.add_data(by_sheet, sheets):
            sheet = row['key']
            href = reverse('regnskab:sheet_detail',
                           kwargs=dict(pk=sheet.id))
            row['raw_date'] = sheet.end_date.toordinal()
            row['date'] = format_html(
                '<a href="{}">Udsendt {}</a>',
                href, sheet.end_date)

        sessions = {s.pk: s for s in Session.objects.filter(period=period)}
        for row in session_table.add_data(by_session, sessions):
            session = row['key']
            href = reverse('regnskab:session_update',
                           kwargs=dict(pk=session.id))
            if session.sent:
                s = 'Udsendt'
                date = session.send_time.date()
            else:
                s = 'Oprettet'
                date = session.created_time.date()
            row['raw_date'] = date.toordinal()
            row['date'] = format_html(
                '<a href="{}">{} {}</a>',
                href, s, date)

        context_data['session_table'] = session_table
        context_data['period_table'] = period_table
        context_data['period'] = period

        return context_data


class SessionUpdate(FormView):
    template_name = 'regnskab/session_form.html'
    form_class = AnonymousEmailTemplateForm

    def get_object(self):
        return get_object_or_404(Session.objects, pk=self.kwargs['pk'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.object.email_template
        return kwargs

    def get_initial(self):
        email_template = self.object.email_template
        # AnonymousEmailTemplateForm.__init__ sets initial body
        if email_template:
            return dict(subject=email_template.subject,
                        format=email_template.format,
                        markup=email_template.markup)
        else:
            return dict(subject='',
                        format=EmailTemplate.POUND,
                        markup=EmailTemplate.PLAIN)

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get_sheets(self):
        purchases_by_sheet_qs = Purchase.objects.filter(
            row__sheet__session=self.object)
        by_sheet = sum_matrix(
            purchases_by_sheet_qs,
            'kind__name', 'row__sheet_id', 'count')
        table = PurchaseStatsTable(self.request)
        table.columns_before = (('date', 'Dato', 'pk'),)
        table.sortable(self.request.GET)
        sheets = {s.pk: s for s in self.object.sheet_set.all()}
        for row in table.add_data(by_sheet, sheets):
            pk = row['pk'] = row['key'].pk
            if self.object.sent:
                href = reverse('regnskab:sheet_detail', kwargs=dict(pk=pk))
            else:
                href = reverse('regnskab:sheet_update', kwargs=dict(pk=pk))
            row['date'] = format_html('<a href="{}">{}</a>', href, row['key'])
        return table

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['session'] = context_data['object'] = self.object
        context_data['sheets'] = self.get_sheets()
        context_data['print'] = self.request.GET.get('print')
        context_data['print_form'] = BalancePrintForm()
        context_data['max_debt'] = get_max_debt()
        payments = self.object.transaction_set.filter(kind=Transaction.PAYMENT)
        payment_sum, = payments.aggregate(Sum('amount')).values()
        context_data['payment_sum'] = -(payment_sum or 0)
        context_data['payment_count'] = payments.count()
        return context_data

    def form_valid(self, form):
        if self.object.sent:
            return already_sent_view(self.request, self.regnskab_session)
        if not self.object.email_template:
            self.object.email_template = EmailTemplate()
            save_it = True
        else:
            if form.has_changed():
                if self.object.email_template.refcount() > 1:
                    # Don't modify the current EmailTemplate,
                    # but create a new one instead.
                    self.object.email_template = EmailTemplate()
                save_it = True
            else:
                save_it = False

        assert save_it is False or self.object.email_template.name == ''
        self.object.email_template.name = ''
        self.object.email_template.subject = form.cleaned_data['subject']
        self.object.email_template.body = form.cleaned_data['body']
        self.object.email_template.format = form.cleaned_data['format']
        self.object.email_template.markup = form.cleaned_data['markup']
        try:
            self.object.email_template.clean()
            self.object.regenerate_emails()
        except ValidationError as exn:
            form.add_error(None, exn)
            return self.form_invalid(form)
        if save_it:
            self.object.email_template.save()
            # Update self.object.email_template_id
            self.object.email_template = self.object.email_template
            self.object.save()
            logger.info("%s: Ret emailskabelon %s for opgørelse %s",
                        self.request.user,
                        self.object.email_template_id, self.object.pk)

        # Redisplay an unbound form without redirecting
        # so we can display a success message.
        # TODO: Use django.contrib.messages instead?
        fresh_form = self.get_form()
        fresh_form.is_bound = False  # As if a GET request
        fresh_form.data = {}  # As if a GET request
        fresh_form.files = {}  # As if a GET request
        context_data = self.get_context_data(
            form=fresh_form,
            success=True,
        )
        return self.render_to_response(context_data)


class ProfileList(TemplateView):
    template_name = 'regnskab/profile_list.html'

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_filter_form(self):
        return ProfileListForm(data=self.request.GET)

    def get_context_data(self, **kwargs):
        context_data = super(ProfileList, self).get_context_data(**kwargs)
        context_data['form'] = form = self.get_filter_form()
        if form.is_valid():
            purchases_after = form.cleaned_data['purchases_after']
        else:
            purchases_after = None
        profiles = get_profiles_title_status()
        for i, p in enumerate(profiles):
            p.table_position = i
        profile_dict = {p.id: p for p in profiles}

        balances, purchases = compute_balance(
            output_matrix=True, purchases_after=purchases_after)
        table = PurchaseStatsTable(self.request)
        table.columns_before = (('name', 'Navn', 'position'),
                                ('status', 'På krydslisten', None))
        table.columns_after = (('balance', 'Balance', 2),)
        table.sortable(self.request.GET)
        table.sort_key = 'position'
        for row in table.add_data(purchases, profile_dict):
            p = row['key']
            row['name'] = format_html(
                '<a class="profile-link" ' +
                'href="{}">{}</a>',
                reverse('regnskab:profile_detail', kwargs=dict(pk=p.pk)),
                p.title_name)
            row['status'] = p.status.since() if p.status else ''
            row['balance'] = balances.get(p.id)
            row['position'] = p.table_position
        context_data['table'] = table
        return context_data


class ProfileDetail(TemplateView):
    template_name = 'regnskab/profile_detail.html'
    REMOVE_ALIAS = 'remove_'

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        self.profile = get_object_or_404(Profile.objects, pk=self.kwargs['pk'])
        try:
            self.sheetstatus = SheetStatus.objects.get(
                profile=self.profile, end_time=None)
        except SheetStatus.DoesNotExist:
            self.sheetstatus = None
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        response = None
        if 'remove_status' in self.request.POST:
            response = self.post_action_remove_status()
        elif 'add_status' in self.request.POST:
            response = self.post_action_add_status()
        elif 'add_alias' in self.request.POST:
            self.post_action_add_alias()
        elif 'set_primary_alias' in self.request.POST:
            response = self.post_action_set_primary_alias()
        else:
            self.post_default()

        if response is None:
            response = self.render_to_response(self.get_context_data())
        return response

    def post_action_remove_status(self):
        if not self.sheetstatus:
            return self.post_error(
                'Personen allerede fjernet fra krydslisten')
        logger.info("%s: Fjern %s fra krydslisten",
                    self.request.user, self.profile)
        self.sheetstatus.end_time = timezone.now()
        self.sheetstatus.save()
        self.sheetstatus = None

    def post_action_add_status(self):
        if self.sheetstatus:
            return self.post_error(
                'Personen allerede tilføjet til krydslisten')
        logger.info("%s: Tilføj %s til krydslisten",
                    self.request.user, self.profile)
        self.sheetstatus = SheetStatus.objects.create(
            profile=self.profile,
            start_time=timezone.now(),
            created_by=self.request.user)

    def post_action_add_alias(self):
        s = self.request.POST.get('alias')
        if s:
            logger.info("%s: Tilføj alias %r til %s",
                        self.request.user, s, self.profile)
            Alias.objects.create(profile=self.profile,
                                 root=s,
                                 start_time=timezone.now(),
                                 created_by=self.request.user)

    def post_action_set_primary_alias(self):
        k, current_alias = self.get_alias_data()
        if k == 'real_title':
            return self.post_error('Kan ikke ændre vist titel for ' +
                                   'person med rigtig titel')
        s = self.request.POST.get('primary_alias') or ''
        current_alias_display = str(current_alias or '')
        if s == current_alias_display:
            # No change
            pass
        else:
            now = timezone.now()
            if current_alias:
                logger.info("%s: Fjern primær alias %r fra %s",
                            self.request.user, current_alias_display,
                            self.profile)
                # Deactivate current_alias and create new current_alias
                # without is_title.
                current_alias.end_time = now
                current_alias.save()
                Alias.objects.create(profile=self.profile,
                                     root=current_alias.root,
                                     is_title=False,
                                     start_time=now,
                                     created_by=self.request.user)
            if s:
                logger.info("%s: Tilføj primær alias %r til %s",
                            self.request.user, s, self.profile)
                existing_same = Alias.objects.filter(
                    profile=self.profile,
                    root=s,
                    end_time=None)
                existing_same.update(end_time=now)
                Alias.objects.create(profile=self.profile,
                                     root=s,
                                     is_title=True,
                                     start_time=now,
                                     created_by=self.request.user)

    def post_default(self):
        for k in self.request.POST:
            if k.startswith(self.REMOVE_ALIAS):
                pk = k[len(self.REMOVE_ALIAS):]
                try:
                    o = Alias.objects.get(profile=self.profile,
                                          pk=pk)
                except Alias.DoesNotExist:
                    pass
                else:
                    o.end_time = timezone.now()
                    o.save()
                    logger.info("%s: Fjern alias %r fra %s",
                                self.request.user, o.root, self.profile)

    def post_error(self, msg):
        return self.render_to_response(self.get_context_data(error=msg))

    def get_sheets(self):
        qs = Purchase.objects.all()
        qs = qs.filter(row__profile=self.profile)
        qs = qs.annotate(
            amount=F('kind__unit_price') * F('count'))
        qs = qs.annotate(date=F('row__sheet__end_date'))
        qs = qs.annotate(sheet=F('row__sheet_id'))
        qs = qs.annotate(session=F('row__sheet__session_id'))
        qs = qs.values(
            'sheet', 'date', 'count', 'kind__name', 'amount',
            'session')
        qs = qs.order_by('date', 'sheet')
        groups = itertools.groupby(qs, key=lambda o: o['sheet'])
        result = []
        session_start = {}
        for sheet_id, xs in groups:
            xs = list(xs)
            href = (
                '%s?highlight_profile=%s' %
                (reverse('regnskab:sheet_detail', kwargs=dict(pk=sheet_id)),
                 self.profile.id))
            session, = set(x['session'] for x in xs)
            date, = set(x['date'] for x in xs)
            if session:
                session_start.setdefault(session, date)
            assert all(x['amount'] is not None for x in xs)
            amount = sum(x['amount'] for x in xs)
            name = ', '.join(
                '%s× %s' % (floatformat(o['count']), o['kind__name'])
                for o in xs
            )
            result.append((date, href, amount, name))
        return result, session_start

    def get_transactions(self, session_start):
        qs = Transaction.objects.all()
        qs = qs.filter(profile=self.profile)
        qs = qs.values_list('kind', 'time', 'note', 'amount', 'session_id')
        for kind, time, note, amount, session in qs:
            name = Transaction(kind=kind, note=note).get_kind_display()
            href = None
            if kind == Transaction.PAYMENT:
                date = session_start.get(session, time.date())
            else:
                date = time.date()
            yield date, href, amount, name

    def get_emails(self):
        qs = Email.objects.all()
        qs = qs.filter(profile=self.profile)
        qs = qs.exclude(session__send_time=None)
        qs = qs.annotate(time=F('session__send_time'))
        qs = qs.values('session_id', 'time')
        emails = list(qs)
        for o in emails:
            href = reverse('regnskab:email_detail',
                           kwargs=dict(pk=o['session_id'],
                                       profile=self.profile.id))
            amount = None
            date = o['time'].date()
            name = 'Email'
            yield date, href, amount, name

    def get_rows(self):
        sheets, session_start = self.get_sheets()
        transactions = list(self.get_transactions(session_start))
        emails = list(self.get_emails())
        # TODO: List SheetStatus, Alias, Title
        return sorted(transactions + sheets + emails, key=lambda x: x[0])

    @tk.set_gfyear(lambda: config.GFYEAR)
    def get_names(self):
        names = []
        for o in self.profile.title_set.all():
            names.append(dict(
                name=tk.prefix(o),
                since='Titel siden %s/%02d' % (o.period, (o.period+1) % 100),
                period=o.period,
                remove=None,
            ))
        for o in self.profile.alias_set.all():
            start = o.start_time.date() if o.start_time else 'altid'
            end = o.end_time.date() if o.end_time else 'altid'
            name = tk.prefix(o, type='unicode') if o.period else o.root
            if o.end_time is None:
                names.append(dict(
                    name=name,
                    since='Siden %s' % start,
                    remove=self.REMOVE_ALIAS + str(o.pk),
                    is_title=o.is_title,
                ))
            else:
                names.append(dict(
                    name=name,
                    since='Fra %s til %s' % (start, end),
                    remove=None,
                ))
        return names

    def get_alias_data(self):
        title_qs = Title.objects.filter(profile=self.profile)
        title_qs = title_qs.order_by('-period')
        if title_qs:
            return ('real_title',
                    tk.prefix(title_qs[0], config.GFYEAR, type='unicode'))
        alias_qs = Alias.objects.filter(profile=self.profile)
        alias_qs = alias_qs.filter(is_title=True, end_time=None)
        alias_qs = alias_qs.order_by()
        if alias_qs:
            assert len(alias_qs) == 1
            assert alias_qs[0].period is None
            return ('primary_alias', alias_qs[0])
        return ('primary_alias', None)

    def get_context_data(self, **kwargs):
        context_data = super(ProfileDetail, self).get_context_data(**kwargs)

        context_data['profile'] = self.profile
        context_data['sheetstatus'] = self.sheetstatus

        rows = []
        balance = Decimal()
        for date, href, amount, name in self.get_rows():
            if amount is not None:
                balance += amount
            rows.append(dict(
                date=date,
                href=href,
                name=name,
                amount=floatformat(amount, 2) if amount is not None else '',
                balance=floatformat(balance, 2),
            ))

        context_data['rows'] = rows
        context_data['names'] = self.get_names()
        alias_key, alias_value = self.get_alias_data()
        context_data[alias_key] = alias_value
        return context_data


class ProfileSearch(TemplateView):
    template_name = 'regnskab/profile_search.html'

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @tk.set_gfyear(lambda: config.GFYEAR)
    def get_results(self, q, only_current):
        if not q:
            return

        results = []

        matcher = difflib.SequenceMatcher()
        matcher.set_seq2(q.lower())
        alias_qs = Alias.objects.all()
        if only_current:
            alias_qs = alias_qs.filter(end_time=None)
            alias_qs = alias_qs.exclude(profile__sheetstatus=None)
            alias_qs = alias_qs.filter(profile__sheetstatus__end_time=None)
        for o in alias_qs:
            input_title = tk.prefix(o) if o.period else o.root
            if input_title.lower() == q.lower():
                sort_key = (4, o.profile_id)
            else:
                matcher.set_seq1(input_title.lower())
                sort_key = (0, matcher.ratio(), input_title, o.pk)
            value = (input_title, o.profile)
            results.append((sort_key, value))

        title_qs = Title.objects.all()
        if only_current:
            title_qs = title_qs.exclude(profile__sheetstatus=None)
            title_qs = title_qs.filter(profile__sheetstatus__end_time=None)
        for o in title_qs:
            input_title = tk.prefix(o) if o.period else o.root
            if q.upper().replace('$', 'S') == input_title.replace('$', 'S'):
                sort_key = (4, o.profile_id)
                value = (input_title, o.profile)
                results.append((sort_key, value))
            elif o.kind == Title.FU and q.upper() == o.root != 'FUAN':
                sort_key = (3, o.profile_id)
                value = (input_title, o.profile)
                results.append((sort_key, value))

        profile_qs = Profile.objects.all()
        if only_current:
            profile_qs = profile_qs.exclude(sheetstatus=None)
            profile_qs = profile_qs.filter(sheetstatus__end_time=None)
        for o in profile_qs:
            if q.lower() in o.name.lower().split():
                sort_key = (3, o.name, o.pk)
            elif q.lower() in o.name.lower():
                sort_key = (2, o.name, o.pk)
            else:
                matcher.set_seq1(o.name.lower())
                sort_key = (0, matcher.ratio(), o.name, o.pk)
            value = (o.name, o)
            results.append((sort_key, value))

        results.sort(reverse=True)
        results = results[:50]
        results = [value for sort_key, value in results]
        return results

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        query = self.request.GET.get('q')
        current = query is None or bool(self.request.GET.get('c'))
        context_data['q'] = query or ''
        context_data['c'] = current
        context_data['results'] = self.get_results(query, current)
        return context_data


class TransactionBatchCreateBase(FormView):
    form_class = TransactionBatchForm
    template_name = 'regnskab/transaction_batch_create.html'

    save_label = 'Gem'
    header = None
    sign = +1

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        self.regnskab_session = self.get_regnskab_session()
        if not self.regnskab_session or self.regnskab_session.sent:
            return already_sent_view(request, self.regnskab_session)
        return super().dispatch(request, *args, **kwargs)

    def get_save_label(self):
        return self.save_label

    def get_header(self):
        return self.header

    def get_regnskab_session(self):
        return get_object_or_404(
            Session.objects, pk=self.kwargs['pk'])

    def get_transaction_kind(self):
        try:
            return self.transaction_kind
        except AttributeError:
            raise ImproperlyConfigured(
                "TransactionBatchCreateBase subclass must define " +
                "transaction_kind.")

    def get_success_view(self):
        return redirect('regnskab:session_update', pk=self.regnskab_session.pk)

    def get_form_kwargs(self, **kwargs):
        r = super().get_form_kwargs(**kwargs)
        r['profiles'] = self.get_profile_data()
        return r

    def get_note(self):
        return ''

    def form_valid(self, form):
        existing_qs = self.get_existing()
        existing = {o.profile_id: o for o in existing_qs}

        save = []
        new = []
        delete = []

        now = timezone.now()
        for profile, amount, selected in form.profile_data():
            if selected:
                o = Transaction(
                    period=self.regnskab_session.period,
                    kind=self.get_transaction_kind(),
                    profile=profile, time=now, amount=self.sign * amount,
                    created_by=self.request.user, created_time=now,
                    note=self.get_note(),
                    session=self.regnskab_session)
                logger.info("%s: Sæt %r for %s i opgørelse %s til %s",
                            self.request.user, o.get_kind_display(),
                            profile, self.regnskab_session.pk,
                            o.amount)
                if profile.id in existing:
                    o.id = existing[profile.id].id
                    save.append(o)
                else:
                    new.append(o)
            elif profile.id in existing:
                e = existing[profile.id]
                logger.info("%s: Fjern %r for %s i opgørelse %s",
                            self.request.user, e.get_kind_display(),
                            profile, self.regnskab_session.pk)
                delete.append(e)

        Transaction.objects.bulk_create(new)
        for o in save:
            o.save()
        delete_ids = [o.id for o in delete]
        Transaction.objects.filter(id__in=delete_ids).delete()

        if self.regnskab_session.email_template:
            self.regnskab_session.regenerate_emails()
        return self.get_success_view()

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['session'] = self.regnskab_session
        context_data['header'] = self.get_header()
        context_data['save_label'] = self.get_save_label()
        return context_data


class PaymentBatchCreate(TransactionBatchCreateBase):
    transaction_kind = Transaction.PAYMENT
    save_label = 'Gem betalinger'
    header = 'Indtast betalinger'
    sign = -1

    def get_existing(self):
        existing_qs = Transaction.objects.filter(
            session=self.regnskab_session, kind=self.get_transaction_kind())
        return existing_qs

    def get_profile_data(self):
        amounts = compute_balance(
            created_before=self.regnskab_session.created_time)
        existing_qs = self.get_existing()
        existing = {o.profile_id: o for o in existing_qs}
        for p in get_profiles_title_status(period=config.GFYEAR - 1, time=self.regnskab_session.created_time):
            try:
                o = existing[p.id]
            except KeyError:
                amount = amounts.get(p.id, 0)
                selected = False
            else:
                amount = self.sign * o.amount
                selected = True
            if selected or p.in_current or amount != 0:
                yield (p, amount, selected)


class PurchaseNoteList(TemplateView):
    template_name = 'regnskab/purchase_note_list.html'
    save_label = 'Gem diverse køb'

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        self.regnskab_session = get_object_or_404(
            Session.objects, pk=kwargs['pk'])
        if not self.regnskab_session or self.regnskab_session.sent:
            return already_sent_view(request, self.regnskab_session)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        existing = self.regnskab_session.transaction_set.all()
        existing = existing.filter(kind=Transaction.PURCHASE)
        existing = existing.exclude(note='')
        existing = existing.values_list('note', 'amount')
        note_amounts = {}
        for note, amount in existing:
            note_amounts.setdefault(note, []).append(amount)
        notes = []
        for note in sorted(note_amounts.keys()):
            counter = Counter(note_amounts[note])
            max_count = max(counter.values())
            amount = next(a for a, c in counter.items()
                          if c == max_count)
            notes.append((note, amount))
        context_data['notes'] = notes
        context_data['session'] = self.regnskab_session
        return context_data


class PurchaseBatchCreate(TransactionBatchCreateBase):
    transaction_kind = Transaction.PURCHASE

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        try:
            self.note = request.GET['note']
        except KeyError:
            return redirect('regnskab:purchase_note_list',
                            pk=self.get_regnskab_session().pk)
        return super().dispatch(request, *args, **kwargs)

    def get_note(self):
        return self.note

    def get_header(self):
        return 'Indtast "%s"' % self.note

    def get_existing(self):
        existing_qs = Transaction.objects.filter(
            session=self.regnskab_session, kind=self.get_transaction_kind())
        existing_qs = existing_qs.filter(note=self.note)
        return existing_qs

    def get_profile_data(self):
        try:
            initial_amount = float(self.request.GET['amount'])
        except (ValueError, KeyError):
            initial_amount = 0

        profiles = get_profiles_title_status()
        existing_qs = self.get_existing()
        existing = {o.profile_id: o for o in existing_qs}
        for p in profiles:
            try:
                o = existing[p.id]
            except KeyError:
                if not p.in_current and not self.request.GET.get('all'):
                    continue
                amount = initial_amount
                selected = False
            else:
                amount = self.sign * o.amount
                selected = True
            yield (p, amount, selected)


class PaymentPurchaseList(TemplateView):
    template_name = 'regnskab/payment_purchase_list.html'

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        self.regnskab_session = get_object_or_404(
            Session.objects, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['session'] = self.regnskab_session
        context_data['max_debt'] = get_max_debt()
        context_data['max_debt_paid'] = get_max_debt_after_payment()

        payments = {}
        payment_qs = Transaction.objects.filter(
            session=self.regnskab_session,
            kind=Transaction.PAYMENT).order_by()
        for p_id, amount in payment_qs.values_list('profile_id', 'amount'):
            # Note: Payments in the database have negative sign.
            payments[p_id] = payments.get(p_id, Decimal()) - amount
        # payments[p_id] is the sum of payment amounts

        profile_sheets = {}
        purchase_qs = Purchase.objects.filter(
            row__sheet__session=self.regnskab_session)
        purchase_qs = purchase_qs.annotate(
            amount=F('kind__unit_price') * F('count'))
        purchase_qs = purchase_qs.annotate(
            profile_id=F('row__profile_id'))
        purchase_qs = purchase_qs.annotate(
            sheet_id=F('row__sheet_id'))

        for o in purchase_qs:
            p_id = o.profile_id
            x = profile_sheets.setdefault(p_id, {})
            x.setdefault(o.sheet_id, []).append(o)

        profile_ids = set(payments.keys()) | set(profile_sheets.keys())
        initial_balances = compute_balance(
            profile_ids=profile_ids,
            created_before=self.regnskab_session.created_time)

        sheet_ids = set(s_id for p_id, sheets in profile_sheets.items()
                        for s_id in sheets.keys())
        sheets = {o.id: o for o in Sheet.objects.filter(id__in=sheet_ids)}

        profiles = get_profiles_title_status()
        rows = []
        for p in profiles:
            p.b0 = initial_balances.get(p.id, Decimal())
            p.b1 = p.b0 - payments.get(p.id, Decimal())
            p.sheets = []
            for s_id, purchases in profile_sheets.get(p.id, {}).items():
                purchases_str = self.describe_purchases(purchases)
                n_rows = len(set(p.row_id for p in purchases))
                p.sheets.append(
                    (sheets[s_id], purchases_str, n_rows, n_rows > 1))
            if not p.sheets:
                continue

            max_debt = get_max_debt()
            max_debt_paid = get_max_debt_after_payment()

            p.warn = max_debt < p.b0 and max_debt_paid < p.b1 and p.sheets
            rows.append(p)

        context_data['object_list'] = rows
        return context_data

    @staticmethod
    def describe_purchases(purchases):
        sheet_rows = set(p.row_id for p in purchases)
        result = []
        for i in sorted(sheet_rows):
            single = {}
            kasse = {}
            for p in purchases:
                if p.row_id != i:
                    continue
                if p.kind.name.endswith('kasse'):
                    kind = p.kind.name[:-5]
                    kasse[kind] = kasse.get(kind, Decimal()) + p.count
                else:
                    kind = p.kind.name
                    single[kind] = single.get(kind, Decimal()) + p.count
            order = ['øl', 'guldøl', 'sodavand']
            x = []
            for k in order:
                s = single.pop(k, 0)
                k = kasse.pop(k, None)
                x.append('%g' % s if k is None else '%g+%gks' % (s, k))
            result.append('(%s)' % ', '.join(x))
        return ' '.join(result)
