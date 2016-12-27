import difflib
import logging
import itertools
from decimal import Decimal
from collections import Counter
import json

from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.conf import settings
from django.http import HttpResponse
from django.db.models import F
from django.utils import timezone
from django.template.defaultfilters import floatformat
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import (
    TemplateView, FormView, ListView, View,
)
from django.template.response import TemplateResponse
from regnskab.forms import (
    SheetCreateForm, SessionForm,
    TransactionBatchForm, BalancePrintForm,
)
from regnskab.models import (
    Sheet, SheetRow, SheetStatus, Profile, Alias, Title,
    EmailTemplate, Session, SheetImage, PurchaseKind,
    Transaction, Purchase,
    compute_balance, get_inka, get_default_prices,
    config, get_profiles_title_status,
)
from regnskab.images.extract import extract_images
from .auth import regnskab_permission_required_method

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

    def get_initial(self):
        kinds = get_default_prices()
        return dict(kinds='\n'.join('%s %s' % x for x in kinds),
                    period=config.GFYEAR)

    def form_valid(self, form):
        data = form.cleaned_data
        sheet = Sheet(name=data['name'],
                      start_date=data['start_date'],
                      end_date=data['end_date'],
                      period=data['period'],
                      created_by=self.request.user,
                      session=self.regnskab_session,
                      image_file=data['image_file'])
        kinds = [
            PurchaseKind(
                sheet=sheet,
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
        sheet.save()
        if data['image_file']:
            for o in images + rows + kinds:
                o.sheet = o.sheet  # Update sheet_id
            for o in images + rows + kinds:
                o.save()
            for o in purchases:
                o.row = o.row  # Update row_id
                o.kind = o.kind  # Update kind_id
            Purchase.objects.bulk_create(purchases)
        logger.info("%s: Opret ny krydsliste id=%s i opgørelse=%s " +
                    "med priser %s",
                    self.request.user, sheet.pk, self.regnskab_session.pk,
                    ' '.join('%s=%s' % (k['name'], k['unit_price'])
                             for k in data['kinds']))
        return redirect('regnskab:sheet_update', pk=sheet.pk)


class SheetDetail(TemplateView):
    template_name = 'regnskab/sheet_detail.html'

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        s = self.get_sheet()
        qs = SheetRow.objects.filter(sheet=s)
        if not qs.exists():
            return redirect('regnskab:sheet_update', pk=s.pk)
        else:
            return super().get(request, *args, **kwargs)

    def get_sheet(self):
        return get_object_or_404(Sheet.objects, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context_data = super(SheetDetail, self).get_context_data(**kwargs)
        context_data['sheet'] = self.get_sheet()
        try:
            context_data['highlight_profile'] = int(
                self.request.GET['highlight_profile'])
        except (KeyError, ValueError):
            pass
        return context_data


class SheetRowUpdate(TemplateView):
    template_name = 'regnskab/sheet_update.html'

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        self.sheet = self.get_sheet()
        self.regnskab_session = self.sheet.session
        if not self.regnskab_session or self.regnskab_session.sent:
            return already_sent_view(request, self.regnskab_session)
        return super().dispatch(request, *args, **kwargs)

    def get_sheet(self):
        return get_object_or_404(Sheet.objects, pk=self.kwargs['pk'])

    def get_profiles(self):
        profiles = get_profiles_title_status()
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
                    profile_id=r['profile'] and r['profile'].id,
                    name=r['name'] or '',
                    counts=counts,
                    image=r['image'],
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
                          if any(c is not None for c in row['counts'])
                          and row['profile_id'])
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


class SessionList(ListView):
    template_name = 'regnskab/session_list.html'
    queryset = Session.objects.all()

    @regnskab_permission_required_method
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

    @regnskab_permission_required_method
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
            logger.info("%s: Ret emailskabelon %s for opgørelse %s",
                        self.request.user,
                        self.object.email_template_id, self.object.pk)
        context_data = self.get_context_data(
            form=form,
            success=True,
        )
        return self.render_to_response(context_data)


class ProfileList(TemplateView):
    template_name = 'regnskab/profile_list.html'

    @regnskab_permission_required_method
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
        if self.sheetstatus and 'remove_status' in self.request.POST:
            logger.info("%s: Fjern %s fra krydslisten",
                        self.request.user, self.profile)
            self.sheetstatus.end_time = timezone.now()
            self.sheetstatus.save()
            self.sheetstatus = None
        elif not self.sheetstatus and 'add_status' in self.request.POST:
            logger.info("%s: Tilføj %s til krydslisten",
                        self.request.user, self.profile)
            self.sheetstatus = SheetStatus.objects.create(
                profile=self.profile,
                start_time=timezone.now(),
                created_by=self.request.user)
        elif 'add_alias' in self.request.POST:
            s = self.request.POST.get('alias')
            if s:
                logger.info("%s: Tilføj alias %r til %s",
                            self.request.user, s, self.profile)
                Alias.objects.create(profile=self.profile,
                                     root=s,
                                     start_time=timezone.now(),
                                     created_by=request.user)
        else:
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
        return self.render_to_response(self.get_context_data())

    def get_purchases(self):
        qs = Purchase.objects.all()
        qs = qs.filter(row__profile=self.profile)
        qs = qs.annotate(
            amount=F('kind__unit_price') * F('count'))
        qs = qs.annotate(balance_change=F('amount'))
        qs = qs.annotate(date=F('row__sheet__end_date'))
        qs = qs.annotate(sheet=F('row__sheet__pk'))
        qs = qs.values(
            'sheet', 'date', 'count', 'kind__name', 'amount', 'balance_change')
        purchases = list(qs)
        for o in purchases:
            o['name'] = '%s× %s' % (floatformat(o['count']), o['kind__name'])
        return purchases

    def get_transactions(self):
        qs = Transaction.objects.all()
        qs = qs.filter(profile=self.profile)
        qs = qs.annotate(balance_change=F('amount'))
        qs = qs.values('kind', 'time', 'note', 'amount', 'balance_change')
        transactions = list(qs)
        for o in transactions:
            kind = o.pop('kind')
            note = o.pop('note')
            o['date'] = o['time'].date()

            t = Transaction(kind=kind, note=note)
            o['name'] = t.get_kind_display()
        return transactions

    def get_rows(self):
        purchases = self.get_purchases()
        transactions = self.get_transactions()
        data = transactions + purchases

        def key(x):
            return (x['date'], 'sheet' in x, x.get('sheet'))

        data.sort(key=key)
        groups = itertools.groupby(data, key=key)
        for (date, has_sheet, sheet), xs in groups:
            if has_sheet:
                xs = list(xs)
                amount = sum(x['balance_change'] for x in xs)
                name = ', '.join(x['name'] for x in xs)
                yield date, sheet, amount, name
            else:
                for x in xs:
                    yield date, sheet, x['balance_change'], x['name']

    def get_names(self):
        names = []
        for o in self.profile.title_set.all():
            names.append(dict(
                name=o.display_title(),
                since='Titel siden %s/%02d' % (o.period, (o.period+1) % 100),
                remove=None,
            ))
        for o in self.profile.alias_set.all():
            start = o.start_time.date() if o.start_time else 'altid'
            end = o.end_time.date() if o.end_time else 'altid'
            if o.end_time is None:
                names.append(dict(
                    name=o.display_title(),
                    since='Siden %s' % start,
                    remove=self.REMOVE_ALIAS + str(o.pk),
                ))
            else:
                names.append(dict(
                    name=o.display_title(),
                    since='Fra %s til %s' % (start, end),
                    remove=None,
                ))
        return names

    def get_context_data(self, **kwargs):
        context_data = super(ProfileDetail, self).get_context_data(**kwargs)

        profile = context_data['profile'] = self.profile
        context_data['sheetstatus'] = self.sheetstatus

        rows = []
        balance = Decimal()
        for date, sheet, amount, name in self.get_rows():
            balance += amount
            rows.append(dict(
                date=date,
                sheet=sheet,
                name=name,
                amount=floatformat(amount, 2),
                balance=floatformat(balance, 2),
            ))

        context_data['rows'] = rows
        context_data['names'] = self.get_names()
        return context_data


class ProfileSearch(TemplateView):
    template_name = 'regnskab/profile_search.html'

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

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
            if o.input_title().lower() == q.lower():
                sort_key = (4, o.profile_id)
            else:
                matcher.set_seq1(o.input_title().lower())
                sort_key = (0, matcher.ratio(), o.input_title(), o.pk)
            value = (o.input_title(), o.profile)
            results.append((sort_key, value))

        title_qs = Title.objects.all()
        if only_current:
            title_qs = title_qs.exclude(profile__sheetstatus=None)
            title_qs = title_qs.filter(profile__sheetstatus__end_time=None)
        for o in title_qs:
            if q.upper() == o.input_title():
                sort_key = (4, o.profile_id)
                value = (o.input_title(), o.profile)
                results.append((sort_key, value))
            elif o.kind == Title.FU and q.upper() == o.root != 'FUAN':
                sort_key = (3, o.profile_id)
                value = (o.input_title(), o.profile)
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
        for p in get_profiles_title_status():
            try:
                o = existing[p.id]
            except KeyError:
                amount = amounts[p.id]
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
                amount = initial_amount
                selected = False
            else:
                amount = self.sign * o.amount
                selected = True
            yield (p, amount, selected)


def describe_purchases(purchases):
    # PaymentPurchaseList helper
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


class PaymentPurchaseList(TemplateView):
    template_name = 'regnskab/payment_purchase_list.html'

    @regnskab_permission_required_method
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
            p.sheets = []
            for s_id, purchases in profile_sheets.get(p.id, {}).items():
                purchases_str = describe_purchases(purchases)
                n_rows = len(set(p.row_id for p in purchases))
                p.sheets.append((sheets[s_id], purchases_str, n_rows, n_rows > 1))
            if not p.sheets:
                continue
            # TODO make 250 configurable
            p.warn = 250 < p.b0 and 0 < p.b1 and p.sheets
            rows.append(p)

        context_data['object_list'] = rows
        return context_data
