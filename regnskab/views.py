from decimal import Decimal
import json

from django.db import models
from django.db.models import F, Value
from django.db.models.functions import Concat
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import (
    TemplateView, FormView, ListView, CreateView, UpdateView, DetailView,
)
from regnskab.forms import (
    SheetCreateForm, EmailTemplateForm, EmailBatchForm,
)
from regnskab.models import (
    Sheet, SheetRow, SheetStatus, parse_bestfu_alias, Profile, Alias,
    EmailTemplate, EmailBatch, Email,
    Purchase, Payment,
)
from regnskab import config


class SheetCreate(FormView):
    form_class = SheetCreateForm
    template_name = 'regnskab/sheet_create.html'

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
        return dict(kinds='\n'.join('%s %s' % x for x in kinds))

    def form_valid(self, form):
        data = form.cleaned_data
        s = Sheet(name=data['name'],
                  start_date=data['start_date'],
                  end_date=data['end_date'])
        s.save()
        for i, kind in enumerate(data['kinds']):
            s.purchasekind_set.create(
                name=kind['name'],
                position=i + 1,
                price=kind['price'])
        return redirect('sheet', pk=s.pk)


class SheetDetail(TemplateView):
    template_name = 'regnskab/sheet_detail.html'

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

    def get_sheet(self):
        return get_object_or_404(Sheet.objects, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context_data = super(SheetRowUpdate, self).get_context_data(**kwargs)
        context_data['sheet'] = self.get_sheet()

        current_qs = SheetStatus.objects.filter(end_time=None)
        current = set(current_qs.values_list('profile_id', flat=True))
        profiles_qs = Profile.objects.all()
        profiles_qs = profiles_qs.prefetch_related('title_set')
        TITLE_ORDER = dict(BEST=0, FU=1, EFU=2)

        alias_qs = Alias.objects.filter(end_time=None)
        aliases = {}
        for a in alias_qs:
            aliases.setdefault(a.profile_id, []).append(a)

        profiles = []
        for p in profiles_qs:
            t = []
            in_current = 0 if p.id in current else 1
            k = (in_current, 3, p.name)
            for title in p.title_set.all():
                t_k = (in_current, TITLE_ORDER[title.kind], -title.period, title.root)
                k = min(k, t_k)
                t.append(title.input_title())
            for title in aliases.get(p.id, ()):
                try:
                    kind, root, period = parse_bestfu_alias(title.root, config.GFYEAR)
                except ValueError:
                    pass
                else:
                    t_k = (in_current, TITLE_ORDER[kind], -period, root)
                    k = min(k, t_k)
                t.append(title.root)
            profiles.append(dict(titles=t, sort_key=k, name=p.name, id=p.pk))
        profiles.sort(key=lambda x: x['sort_key'])
        for i, x in enumerate(profiles):
            x['sort_key'] = i
        context_data['profiles_json'] = json.dumps(profiles, indent=2)

        return context_data


class EmailTemplateList(ListView):
    template_name = 'regnskab/email_template_list.html'
    queryset = EmailTemplate.objects.all()


class EmailTemplateUpdate(UpdateView):
    template_name = 'regnskab/email_template_form.html'
    queryset = EmailTemplate.objects.all()
    form_class = EmailTemplateForm


class EmailTemplateCreate(CreateView):
    template_name = 'regnskab/email_template_form.html'
    queryset = EmailTemplate.objects.all()
    form_class = EmailTemplateForm


class EmailBatchList(ListView):
    template_name = 'regnskab/email_batch_list.html'
    queryset = EmailBatch.objects.all()


class EmailBatchUpdate(UpdateView):
    template_name = 'regnskab/email_batch_form.html'
    queryset = EmailBatch.objects.all()
    form_class = EmailBatchForm

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

    def get_object(self):
        return get_object_or_404(
            Email,
            batch_id=self.kwargs['pk'],
            profile_id=self.kwargs['profile'])


class ProfileDetail(TemplateView):
    template_name = 'regnskab/profile_detail.html'

    def get_context_data(self, **kwargs):
        context_data = super(ProfileDetail, self).get_context_data(**kwargs)

        profile = get_object_or_404(Profile.objects, pk=self.kwargs['pk'])
        context_data['profile'] = profile

        purchase_qs = Purchase.objects.all()
        purchase_qs = purchase_qs.filter(row__profile=profile)
        purchase_qs = purchase_qs.annotate(amount=F('kind__price') * F('count'))
        purchase_qs = purchase_qs.annotate(balance_change=F('amount'))
        purchase_qs = purchase_qs.annotate(
            name=Concat(F('count'), Value('x '), F('kind__name'),
                        output_field=models.CharField()))
        purchase_qs = purchase_qs.annotate(date=F('row__sheet__end_date'))
        purchase_qs = purchase_qs.values('date', 'name', 'amount', 'balance_change')
        purchases = list(purchase_qs)

        payment_qs = Payment.objects.all()
        payment_qs = payment_qs.filter(profile=profile)
        payment_qs = payment_qs.annotate(name=Value('betaling', output_field=models.CharField()))
        payment_qs = payment_qs.annotate(balance_change=-1 * F('amount'))
        payment_qs = payment_qs.values('time', 'name', 'amount', 'balance_change')
        payments = list(payment_qs)

        rows = payments + purchases
        for row in rows:
            if 'date' not in row:
                row['date'] = row['time'].date()
        rows.sort(key=lambda x: x['date'])
        balance = Decimal()
        for row in rows:
            balance += row['balance_change']
            row['balance'] = balance
        context_data['rows'] = rows
        return context_data
