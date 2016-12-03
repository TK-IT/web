import itertools
from decimal import Decimal
from collections import Counter, defaultdict
import json

from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.db.models import F, Min
from django.utils import timezone
from django.utils.decorators import method_decorator
import django.core.mail
from django.contrib.auth.decorators import permission_required
from django.template.defaultfilters import floatformat
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import (
    View, TemplateView, FormView, ListView, CreateView, UpdateView, DetailView,
)
from regnskab.forms import (
    SheetCreateForm, EmailTemplateForm, SessionForm,
    TransactionBatchForm, BalancePrintForm,
)
from regnskab.models import (
    Sheet, SheetRow, SheetStatus, Profile, Alias, Title,
    EmailTemplate, Session, Email, PurchaseKind,
    Transaction, Purchase,
    compute_balance, get_inka,
    config, tk_prefix,
)
from regnskab.texrender import tex_to_pdf, RenderError, pdfnup, run_lp


regnskab_permission_required = permission_required('regnskab.add_sheetrow')

TITLE_ORDER = dict(BEST=0, EFU=1, FU=2)
BEST_ORDER = dict(zip('FORM INKA KASS NF CERM SEKR PR VC'.split(), range(8)))


class Home(TemplateView):
    template_name = 'regnskab/home.html'

    @method_decorator(regnskab_permission_required)
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
        return context_data


class SessionCreate(TemplateView):
    template_name = 'regnskab/session_create.html'

    def post(self, request):
        try:
            email_template = EmailTemplate.objects.get(
                name='Standard')
        except EmailTemplate.DoesNotExist:
            email_template = None
        session = Session(created_by=self.request.user, period=config.GFYEAR,
                          email_template=email_template)
        session.save()
        if session.email_template:
            session.regenerate_emails()
        return redirect('session_update', pk=session.pk)


def get_profiles(only_current):
    current_qs = SheetStatus.objects.filter(end_time=None)
    current = set(current_qs.values_list('profile_id', flat=True))

    profile_qs = Profile.objects.all()
    if only_current:
        profile_qs = profile_qs.filter(id__in=current)
    title_qs = Title.objects.all()
    titles = {}
    for t in title_qs:
        titles.setdefault(t.profile_id, []).append(t)

    def title_key(t):
        return (-t.period, TITLE_ORDER[t.kind],
                BEST_ORDER.get(t.root, 0), t.root)

    def current_key(title, profile):
        if profile.title is None:
            return (1, profile.name)
        else:
            return (0, title_key(profile.title), profile.name)

    def key(profile):
        if profile.in_current:
            return (0, current_key(profile.title, profile))
        else:
            return (1, profile.name)

    profiles = []
    for profile in profile_qs:
        t = titles.get(profile.id)
        if t:
            profile.title = max(t, key=lambda t: t.period)
        else:
            profile.title = None
        profile.in_current = profile.id in current
        if only_current:
            assert profile.in_current
        profiles.append(profile)
    profiles.sort(key=key)
    return profiles


class SheetCreate(FormView):
    form_class = SheetCreateForm
    template_name = 'regnskab/sheet_create.html'

    @method_decorator(regnskab_permission_required)
    def dispatch(self, request, *args, **kwargs):
        self.regnskab_session = get_object_or_404(
            Session.objects, pk=kwargs['session'])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        vand_price = 8
        øl_price = 10
        guld_price = 13
        vandkasse_price = 25*vand_price
        ølkasse_price = 25*øl_price
        guldkasse_price = ølkasse_price + 30*(guld_price - øl_price)
        kinds = [
            ('øl', øl_price),
            ('ølkasse', ølkasse_price),
            ('guldøl', guld_price),
            ('guldølkasse', guldkasse_price),
            ('sodavand', vand_price),
            ('sodavandkasse', vandkasse_price),
        ]
        return dict(kinds='\n'.join('%s %s' % x for x in kinds),
                    period=config.GFYEAR)

    def form_valid(self, form):
        data = form.cleaned_data
        s = Sheet(name=data['name'],
                  start_date=data['start_date'],
                  end_date=data['end_date'],
                  period=data['period'],
                  created_by=self.request.user,
                  session=self.regnskab_session)
        s.save()
        for i, kind in enumerate(data['kinds']):
            s.purchasekind_set.create(
                name=kind['name'],
                position=i + 1,
                unit_price=kind['unit_price'])
        return redirect('sheet_update', pk=s.pk)


class SheetDetail(TemplateView):
    template_name = 'regnskab/sheet_detail.html'

    @method_decorator(regnskab_permission_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        s = self.get_sheet()
        qs = SheetRow.objects.filter(sheet=s)
        if not qs.exists():
            return redirect('sheet_update', pk=s.pk)
        else:
            return super().get(request, *args, **kwargs)

    def get_sheet(self):
        return get_object_or_404(Sheet.objects, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context_data = super(SheetDetail, self).get_context_data(**kwargs)
        context_data['sheet'] = self.get_sheet()
        return context_data


class SheetRowUpdate(TemplateView):
    template_name = 'regnskab/sheet_update.html'

    @method_decorator(regnskab_permission_required)
    def dispatch(self, request, *args, **kwargs):
        self.sheet = self.get_sheet()
        self.regnskab_session = self.sheet.session
        return super().dispatch(request, *args, **kwargs)

    def get_sheet(self):
        return get_object_or_404(Sheet.objects, pk=self.kwargs['pk'])

    def get_profiles(self):
        profiles = get_profiles(only_current=False)
        aliases = {}
        for o in Alias.objects.filter(end_time=None):
            aliases.setdefault(o.profile_id, []).append(o)
        for o in Title.objects.all():
            aliases.setdefault(o.profile_id, []).append(o)

        GFYEAR = config.GFYEAR

        result = []
        for i, profile in enumerate(profiles):
            titles = aliases.get(profile.id, ())
            titles_input = [t.input_title(GFYEAR) for t in titles]
            title_input = profile.title and profile.title.input_title(GFYEAR)
            title_name = ' '.join((title_input or '', profile.name)).strip()
            result.append(dict(
                titles=titles_input, title=title_input, sort_key=i,
                name=profile.name, title_name=title_name, id=profile.pk,
                in_current=profile.in_current))
        return result

    def get_context_data(self, **kwargs):
        context_data = super(SheetRowUpdate, self).get_context_data(**kwargs)
        sheet = context_data['sheet'] = self.sheet
        profiles = self.get_profiles()
        context_data['profiles_json'] = json.dumps(profiles, indent=2)
        if 'rows_json' not in context_data:
            row_objects = sheet.rows()
            row_data = []
            for r in row_objects:
                counts = []
                for k in r['kinds']:
                    counts.append(float(k.count) if k.id else None)

                row_data.append(dict(
                    profile_id=r['profile'].id,
                    name=r['name'],
                    counts=counts,
                ))
            context_data['rows_json'] = json.dumps(row_data, indent=2)

        context_data['session'] = self.regnskab_session

        return context_data

    def post_invalid(self, request, message):
        return self.render_to_response(
            self.get_context_data(error=message, rows_json=request.POST['data']))

    def clean(self, data_json):
        sheet = self.sheet
        kinds = list(sheet.columns())
        try:
            row_data = json.loads(data_json)
        except Exception as exn:
            raise ValidationError(str(exn))

        KEYS = {'profile_id', 'name', 'counts'}
        for row in row_data:
            if set(row.keys()) != KEYS:
                raise ValidationError("Invalid keys %s" % (set(row.keys()),))
            counts = row['counts']
            if not isinstance(counts, list):
                raise ValidationError("Wrong type of counts %s" % (counts,))
            if len(counts) != len(kinds):
                raise ValidationError("Wrong number of counts %s" % (counts,))
            if any(c is not None for c in counts):
                if not row['name']:
                    raise ValidationError("Name must not be empty")
                if not row['profile_id']:
                    raise ValidationError("Unknown name/profile")
                if not isinstance(row['profile_id'], int):
                    raise ValidationError("profile_id must be an int")

        profile_ids = set(row['profile_id'] for row in row_data
                          if any(c is not None for c in row['counts']))
        profiles = {
            p.id: p for p in Profile.objects.filter(id__in=sorted(profile_ids))
        }
        missing = profile_ids - set(profiles.keys())
        if missing:
            raise ValidationError("Unknown profile IDs %s" % (missing,))
        return [
            dict(profile=profiles[row['profile_id']],
                 name=row['name'],
                 position=i + 1,
                 kinds=[Purchase(kind=kind, count=c or 0)
                        for kind, c in zip(kinds, row['counts'])])
            for i, row in enumerate(row_data)
            if any(c is not None for c in row['counts'])
        ]

    def save_rows(self, rows):
        def data(r):
            return (r['profile'].id, r['name'], r['position'],
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

        save_rows = []
        save_purchases = []
        for o in save:
            save_rows.append(SheetRow(
                sheet=sheet, profile=o['profile'],
                name=o['name'], position=o['position']))
            for c in o['kinds']:
                if c.count:
                    c.row = save_rows[-1]
                    save_purchases.append(c)

        # print("Create %s, delete %s" % (len(save_rows), len(delete)))
        delete_ids = set(d['id'] for d in delete if d['id'])
        SheetRow.objects.filter(id__in=delete_ids).delete()
        for o in save_rows:
            o.save()
        for o in save_purchases:
            o.row = o.row  # Update o.row_id
        Purchase.objects.bulk_create(save_purchases)

    def post(self, request, *args, **kwargs):
        try:
            row_objects = self.clean(request.POST['data'])
        except ValidationError as exn:
            return self.post_invalid(request, str(exn))
        self.save_rows(row_objects)
        if self.regnskab_session.email_template:
            self.regnskab_session.regenerate_emails()
        return self.render_to_response(
            self.get_context_data(saved=True))


class EmailTemplateList(ListView):
    template_name = 'regnskab/email_template_list.html'
    queryset = EmailTemplate.objects.exclude(name='')

    def get_queryset(self):
        qs = list(super().get_queryset())
        sessions = Session.objects.all()
        sessions = sessions.exclude(send_time=None)
        sessions = sessions.order_by('email_template_id', '-send_time')
        groups = itertools.groupby(sessions, key=lambda s: s.email_template_id)
        latest = {k: next(g) for k, g in groups}
        for o in qs:
            o.latest_session = latest.get(o.id)
        return qs

    @method_decorator(regnskab_permission_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class EmailTemplateUpdate(UpdateView):
    template_name = 'regnskab/email_template_form.html'
    queryset = EmailTemplate.objects.exclude(name='')
    form_class = EmailTemplateForm

    def form_valid(self, form):
        qs = Session.objects.filter(email_template_id=self.kwargs['pk'])
        if qs.exists():
            backup = EmailTemplate(
                name='',
                subject=self.object.subject,
                body=self.object.body,
                format=self.object.format)
            backup.save()
            qs.update(email_template=backup)
        form.save()
        return redirect('email_template_list')

    @method_decorator(regnskab_permission_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class EmailTemplateCreate(CreateView):
    template_name = 'regnskab/email_template_form.html'
    form_class = EmailTemplateForm

    def get_initial(self):
        try:
            email_template = EmailTemplate.objects.get(
                name='Standard')
        except EmailTemplate.DoesNotExist:
            return dict(subject='[TK] Status på ølregningen')
        else:
            return dict(subject=email_template.subject,
                        body=email_template.body)

    def form_valid(self, form):
        form.save()
        return redirect('email_template_list')

    @method_decorator(regnskab_permission_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class SessionList(ListView):
    template_name = 'regnskab/session_list.html'
    queryset = Session.objects.all()

    @method_decorator(regnskab_permission_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class SessionUpdate(FormView):
    template_name = 'regnskab/session_form.html'
    form_class = SessionForm

    def get_object(self):
        return get_object_or_404(Session.objects, pk=self.kwargs['pk'])

    def get_initial(self):
        email_template = self.object.email_template
        if email_template:
            return dict(subject=email_template.subject,
                        body=email_template.body,
                        format=email_template.format)
        else:
            return dict(subject='',
                        body='',
                        format=EmailTemplate.POUND)

    @method_decorator(regnskab_permission_required)
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['object'] = self.object
        context_data['print'] = self.request.GET.get('print')
        context_data['print_form'] = BalancePrintForm()
        return context_data

    def form_valid(self, form):
        if not self.object.email_template:
            self.object.email_template = EmailTemplate()
            save_it = True
        else:
            if form.has_changed():
                qs = Session.objects.exclude(pk=self.object.pk)
                qs = qs.filter(email_template=self.object.email_template)
                if self.object.email_template.name or qs.exists():
                    self.object.email_template = EmailTemplate()
                save_it = True
            else:
                save_it = False

        self.object.email_template.name = ''
        self.object.email_template.subject = form.cleaned_data['subject']
        self.object.email_template.body = form.cleaned_data['body']
        self.object.email_template.format = form.cleaned_data['format']
        try:
            self.object.regenerate_emails()
        except ValidationError as exn:
            form.add_error(None, exn)
            return self.form_invalid(form)
        if save_it:
            self.object.email_template.save()
            # Update self.object.email_template_id
            self.object.email_template = self.object.email_template
            self.object.save()
        context_data = self.get_context_data(
            form=form,
            success=True,
        )
        return self.render_to_response(context_data)


class EmailList(ListView):
    template_name = 'regnskab/email_list.html'

    @method_decorator(regnskab_permission_required)
    def dispatch(self, request, *args, **kwargs):
        self.regnskab_session = get_object_or_404(
            Session.objects, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Email.objects.filter(session_id=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['session'] = self.regnskab_session
        context_data['editable'] = not self.regnskab_session.sent
        return context_data


class EmailDetail(DetailView):
    template_name = 'regnskab/email_detail.html'

    @method_decorator(regnskab_permission_required)
    def dispatch(self, request, *args, **kwargs):
        self.regnskab_session = get_object_or_404(
            Session.objects, pk=self.kwargs['pk'])
        self.profile = get_object_or_404(
            Profile.objects, pk=self.kwargs['profile'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['session'] = self.regnskab_session
        context_data['profile'] = self.profile
        return context_data

    def get_object(self):
        return get_object_or_404(
            Email.objects,
            session_id=self.kwargs['pk'],
            profile_id=self.kwargs['profile'])


class EmailSend(View):
    @method_decorator(regnskab_permission_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk, profile=None):
        regnskab_session = get_object_or_404(Session.objects, pk=pk)
        if profile is None:
            qs = Email.objects.filter(session=regnskab_session)
        else:
            p = get_object_or_404(Profile.objects, pk=profile)
            qs = Email.objects.filter(session=regnskab_session, profile=p)

        emails = list(qs)
        if not emails:
            raise Http404()

        messages = [e.to_message() for e in emails]
        override_recipient = (len(messages) == 1 and
                              self.request.POST.get('override_recipient'))
        if override_recipient:
            for m in messages:
                m.to = [override_recipient]
        email_backend = django.core.mail.get_connection()
        email_backend.send_messages(messages)
        if override_recipient:
            return redirect('email_list', pk=emails[0].session_id)
        else:
            regnskab_session.send_time = timezone.now()
            regnskab_session.save()
            return redirect('home')


def get_profiles_title_status():
    title_qs = Title.objects.all().order_by('period')
    titles = {}
    for t in title_qs:
        # Override any older profiles
        titles[t.profile_id] = t

    qs = Profile.objects.all()

    status_qs = SheetStatus.objects.all().order_by('profile_id')
    groups = itertools.groupby(status_qs, key=lambda s: s.profile_id)
    now = timezone.now()
    statuses = {pk: sorted(s, key=lambda s: (s.end_time or now))[-1]
                for pk, s in groups}

    profiles = list(qs)
    for p in profiles:
        p.status = statuses.get(p.id)
        p.title = titles.get(p.id)
    profiles.sort(
        key=lambda p: (p.status is None,
                       p.status and p.status.end_time is not None,
                       p.name if not p.status or p.status.end_time else
                       (p.title is None,
                        (-p.title.period, p.title.kind,
                         BEST_ORDER.get(p.title.root, 10),
                         p.title.root)
                        if p.title else p.name)))
    return profiles


class ProfileList(TemplateView):
    template_name = 'regnskab/profile_list.html'

    @method_decorator(regnskab_permission_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super(ProfileList, self).get_context_data(**kwargs)
        profiles = get_profiles_title_status()
        balances = compute_balance()
        for p in profiles:
            p.balance = balances.get(p.id)
        context_data['object_list'] = profiles
        return context_data


class ProfileDetail(TemplateView):
    template_name = 'regnskab/profile_detail.html'

    @method_decorator(regnskab_permission_required)
    def dispatch(self, request, *args, **kwargs):
        self.profile = get_object_or_404(Profile.objects, pk=self.kwargs['pk'])
        try:
            self.sheetstatus = SheetStatus.objects.get(
                profile=self.profile, end_time=None)
        except SheetStatus.DoesNotExist:
            self.sheetstatus = None
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if self.sheetstatus:
            self.sheetstatus.end_time = timezone.now()
            self.sheetstatus.save()
            self.sheetstatus = None
        else:
            self.sheetstatus = SheetStatus.objects.create(
                profile=self.profile,
                start_time=timezone.now(),
                created_by=self.request.user)
        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        context_data = super(ProfileDetail, self).get_context_data(**kwargs)

        profile = context_data['profile'] = self.profile
        context_data['sheetstatus'] = self.sheetstatus

        purchase_qs = Purchase.objects.all()
        purchase_qs = purchase_qs.filter(row__profile=profile)
        purchase_qs = purchase_qs.annotate(
            amount=F('kind__unit_price') * F('count'))
        purchase_qs = purchase_qs.annotate(balance_change=F('amount'))
        purchase_qs = purchase_qs.annotate(date=F('row__sheet__end_date'))
        purchase_qs = purchase_qs.annotate(sheet=F('row__sheet__pk'))
        purchase_qs = purchase_qs.values(
            'sheet', 'date', 'count', 'kind__name', 'amount', 'balance_change')
        purchases = list(purchase_qs)
        for o in purchases:
            o['name'] = '%s× %s' % (floatformat(o['count']), o['kind__name'])

        payment_qs = Transaction.objects.all()
        payment_qs = payment_qs.filter(profile=profile)
        payment_qs = payment_qs.annotate(balance_change=F('amount'))
        payment_qs = payment_qs.values('kind', 'time', 'note', 'amount', 'balance_change')
        payments = list(payment_qs)
        for o in payments:
            kind = o.pop('kind')
            note = o.pop('note')
            o['date'] = o['time'].date()

            t = Transaction(kind=kind, note=note)
            o['name'] = t.get_kind_display()

        row_data = payments + purchases

        def key(x):
            return (x['date'], 'sheet' in x, x.get('sheet'))

        row_data.sort(key=key)
        row_iter = itertools.groupby(row_data, key=key)
        rows = []
        balance = Decimal()
        for (date, b, sheet), xs in row_iter:
            if sheet:
                xs = list(xs)
                amount = sum(x['balance_change'] for x in xs)
                balance += sum(x['balance_change'] for x in xs)
                rows.append(dict(
                    date=date,
                    sheet=sheet,
                    name=', '.join(x['name'] for x in xs),
                    amount=floatformat(amount, 2),
                    balance=floatformat(balance, 2),
                ))
            else:
                for x in xs:
                    amount = x['balance_change']
                    balance += amount
                    rows.append(dict(
                        date=date,
                        sheet=sheet,
                        name=x['name'],
                        amount=floatformat(amount, 2),
                        balance=floatformat(balance, 2),
                    ))
        context_data['rows'] = rows
        return context_data


class TransactionBatchCreateBase(FormView):
    form_class = TransactionBatchForm
    template_name = 'regnskab/transaction_batch_create.html'

    save_label = 'Gem'
    header = None
    sign = +1

    @method_decorator(regnskab_permission_required)
    def dispatch(self, request, *args, **kwargs):
        self.regnskab_session = self.get_regnskab_session()
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

    def get_profiles(self):
        return get_profiles(only_current=True)

    def get_initial_amounts(self, profiles):
        raise ImproperlyConfigured(
            "TransactionBatchCreateBase subclass must define " +
            "get_initial_amounts.")

    def get_existing(self):
        existing_qs = Transaction.objects.filter(
            session=self.regnskab_session, kind=self.get_transaction_kind())
        return existing_qs

    def get_success_view(self):
        return redirect('session_update', pk=self.regnskab_session.pk)

    def get_profile_data(self):
        profiles = self.get_profiles()
        amounts = self.get_initial_amounts(profiles)
        existing_qs = self.get_existing()
        existing = {o.profile_id: o for o in existing_qs}
        for p in profiles:
            amount = amounts[p.id]
            try:
                o = existing[p.id]
            except KeyError:
                selected = False
            else:
                amount = self.sign * o.amount
                selected = True
            yield (p, amount, selected)

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
                    kind=self.get_transaction_kind(),
                    profile=profile, time=now, amount=self.sign * amount,
                    created_by=self.request.user, created_time=now,
                    note=self.get_note(),
                    session=self.regnskab_session)
                if profile.id in existing:
                    o.id = existing[profile.id].id
                    save.append(o)
                else:
                    new.append(o)
            elif profile.id in existing:
                delete.append(existing[profile.id])

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

    def get_initial_amounts(self, profiles):
        return compute_balance(
            profile_ids={p.id for p in profiles},
            created_before=self.regnskab_session.created_time)


class PurchaseNoteList(TemplateView):
    template_name = 'regnskab/purchase_note_list.html'
    save_label = 'Gem diverse køb'

    @method_decorator(regnskab_permission_required)
    def dispatch(self, request, *args, **kwargs):
        self.regnskab_session = get_object_or_404(
            Session.objects, pk=kwargs['pk'])
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

    @method_decorator(regnskab_permission_required)
    def dispatch(self, request, *args, **kwargs):
        try:
            self.note = request.GET['note']
        except KeyError:
            return redirect(
                'purchase_note_list', pk=self.get_regnskab_session().pk)
        return super().dispatch(request, *args, **kwargs)

    def get_note(self):
        return self.note

    def get_header(self):
        return 'Indtast "%s"' % self.note

    def get_existing(self):
        return super().get_existing().filter(note=self.note)

    def get_initial_amounts(self, profiles):
        try:
            a = float(self.request.GET['amount'])
        except (ValueError, KeyError):
            a = 0
        return {p.id: a for p in profiles}


class PaymentPurchaseList(TemplateView):
    template_name = 'regnskab/payment_purchase_list.html'

    @method_decorator(regnskab_permission_required)
    def dispatch(self, request, *args, **kwargs):
        self.regnskab_session = get_object_or_404(
            Session.objects, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

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
            p.sheets = [
                (sheets[s_id], ', '.join(map(str, purchases)))
                for s_id, purchases in profile_sheets.get(p.id, {}).items()]
            if not p.sheets:
                continue
            # TODO make 250 configurable
            p.warn = 250 < p.b0 and 0 < p.b1 and p.sheets
            rows.append(p)

        context_data['object_list'] = rows
        return context_data


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

    @method_decorator(regnskab_permission_required)
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

        profiles = get_profiles_title_status()
        if period == 2016 and timezone.now().year == 2016:
            best = {profiles[i].title.root: i
                    for i in range(len(profiles))
                    if profiles[i].title and
                    profiles[i].title.period == 2016}
            assert best['FORM'] < best['NF']
            nf = profiles[best['NF']]
            del profiles[best['NF']]
            nf.name = 'Taberen'
            nf.title = None
            profiles.append(nf)
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

        try:
            output = run_lp(pdf, duplex=False)
        except RenderError as exn:
            form.add_error(None, str(exn))
            return self.form_invalid(form)

        url = reverse('session_update',
                      kwargs=dict(pk=self.regnskab_session.id))
        return HttpResponseRedirect(url + '?print=success')
