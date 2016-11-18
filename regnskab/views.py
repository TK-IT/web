import itertools
from decimal import Decimal
import json

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Value
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required
from django.template.defaultfilters import floatformat
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import (
    TemplateView, FormView, ListView, CreateView, UpdateView, DetailView,
)
from regnskab.forms import (
    SheetCreateForm, EmailTemplateForm, EmailBatchForm,
)
from regnskab.models import (
    Sheet, SheetRow, SheetStatus, parse_bestfu_alias, Profile, Alias, Title,
    EmailTemplate, EmailBatch, Email,
    Purchase, Payment,
    compute_balance,
    config,
)


regnskab_permission_required = permission_required(
    'regnskab.add_sheetrow', raise_exception=True)


def get_profiles(only_current):
    current_qs = SheetStatus.objects.filter(end_time=None)
    current = set(current_qs.values_list('profile_id', flat=True))

    qs = Profile.objects.all()
    if only_current:
        qs = qs.filter(id__in=current)
    qs = qs.prefetch_related('title_set')
    TITLE_ORDER = dict(BEST=0, FU=1, EFU=2)

    def title_key(t):
        return (-t.period, TITLE_ORDER[t.kind], t.root)

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
    for profile in qs:
        titles = list(profile.title_set.all())
        if titles:
            profile.title = max(titles, key=lambda t: t.period)
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
                  period=data['period'])
        s.save()
        for i, kind in enumerate(data['kinds']):
            s.purchasekind_set.create(
                name=kind['name'],
                position=i + 1,
                price=kind['price'])
        return redirect('sheet', pk=s.pk)


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
        return super().dispatch(request, *args, **kwargs)

    def get_sheet(self):
        return get_object_or_404(Sheet.objects, pk=self.kwargs['pk'])

    def get_profiles(self):
        profiles = get_profiles(only_current=False)
        alias_qs = Alias.objects.filter(end_time=None)
        aliases = {}
        for a in alias_qs:
            aliases.setdefault(a.profile_id, []).append(a)

        TITLE_ORDER = dict(BEST=0, FU=1, EFU=2)
        GFYEAR = config.GFYEAR

        for i, profile in enumerate(profiles):
            titles = []
            for title in p.title_set.all():
                titles.append(title)
            for title in aliases.get(p.id, ()):
                titles.append(title)
            title_input = [t.input_title(GFYEAR) for t in titles]
            profiles.append(dict(titles=title_input, sort_key=i, name=p.name,
                                 id=p.pk, in_current=p.in_current))
        return profiles

    def get_context_data(self, **kwargs):
        context_data = super(SheetRowUpdate, self).get_context_data(**kwargs)
        sheet = context_data['sheet'] = self.get_sheet()
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

        return context_data

    def post_invalid(self, request, message):
        return self.render_to_response(
            self.get_context_data(error=message, rows_json=request.POST['data']))

    def clean(self, data_json):
        sheet = self.get_sheet()
        kinds = list(sheet.purchasekind_set.all())
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

        sheet = self.get_sheet()
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
        return self.render_to_response(
            self.get_context_data(saved=True))


class EmailTemplateList(ListView):
    template_name = 'regnskab/email_template_list.html'
    queryset = EmailTemplate.objects.all()

    @method_decorator(regnskab_permission_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class EmailTemplateUpdate(UpdateView):
    template_name = 'regnskab/email_template_form.html'
    queryset = EmailTemplate.objects.all()
    form_class = EmailTemplateForm

    @method_decorator(regnskab_permission_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class EmailTemplateCreate(CreateView):
    template_name = 'regnskab/email_template_form.html'
    queryset = EmailTemplate.objects.all()
    form_class = EmailTemplateForm

    @method_decorator(regnskab_permission_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class EmailBatchList(ListView):
    template_name = 'regnskab/email_batch_list.html'
    queryset = EmailBatch.objects.all()

    @method_decorator(regnskab_permission_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class EmailBatchUpdate(UpdateView):
    template_name = 'regnskab/email_batch_form.html'
    queryset = EmailBatch.objects.all()
    form_class = EmailBatchForm

    @method_decorator(regnskab_permission_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save()
        self.object.regenerate_emails()
        context_data = self.get_context_data(
            form=form,
            success=True,
        )
        return self.render_to_response(context_data)


class EmailDetail(DetailView):
    template_name = 'regnskab/email_detail.html'

    @method_decorator(regnskab_permission_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return get_object_or_404(
            Email,
            batch_id=self.kwargs['pk'],
            profile_id=self.kwargs['profile'])


class ProfileList(TemplateView):
    template_name = 'regnskab/profile_list.html'

    @method_decorator(regnskab_permission_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super(ProfileList, self).get_context_data(**kwargs)
        title_qs = Title.objects.all().order_by('period')
        titles = {}
        for t in title_qs:
            # Override any older profiles
            titles[t.profile_id] = t
        qs = Profile.objects.all()
        qs = qs.prefetch_related('sheetstatus_set')
        profiles = list(qs)
        balances = compute_balance()
        for p in profiles:
            p.balance = balances.get(p.id)
            now = timezone.now()
            statuses = sorted(p.sheetstatus_set.all(),
                              key=lambda s: (s.end_time or now))
            if statuses:
                p.status = statuses[-1]
            else:
                p.status = None
            p.title = titles.get(p.id)
        profiles.sort(
            key=lambda p: (p.status is None,
                           p.status and p.status.end_time is not None,
                           p.name if not p.status or p.status.end_time else
                           (p.title is None,
                            (-p.title.period, p.title.kind, p.title.root)
                            if p.title else p.name)))

        context_data['object_list'] = profiles
        return context_data


class ProfileDetail(TemplateView):
    template_name = 'regnskab/profile_detail.html'

    @method_decorator(regnskab_permission_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super(ProfileDetail, self).get_context_data(**kwargs)

        profile = get_object_or_404(Profile.objects, pk=self.kwargs['pk'])
        context_data['profile'] = profile

        purchase_qs = Purchase.objects.all()
        purchase_qs = purchase_qs.filter(row__profile=profile)
        purchase_qs = purchase_qs.annotate(amount=F('kind__price') * F('count'))
        purchase_qs = purchase_qs.annotate(balance_change=F('amount'))
        purchase_qs = purchase_qs.annotate(date=F('row__sheet__end_date'))
        purchase_qs = purchase_qs.annotate(sheet=F('row__sheet__pk'))
        purchase_qs = purchase_qs.values(
            'sheet', 'date', 'count', 'kind__name', 'amount', 'balance_change')
        purchases = list(purchase_qs)
        for o in purchases:
            o['name'] = '%s× %s' % (floatformat(o['count']), o['kind__name'])

        payment_qs = Payment.objects.all()
        payment_qs = payment_qs.filter(profile=profile)
        payment_qs = payment_qs.annotate(name=F('note'))
        payment_qs = payment_qs.annotate(balance_change=-1 * F('amount'))
        payment_qs = payment_qs.values('time', 'name', 'amount', 'balance_change')
        payments = list(payment_qs)
        for o in payments:
            o['date'] = o['time'].date()
            if not o['name']:
                o['name'] = 'Betaling'

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
