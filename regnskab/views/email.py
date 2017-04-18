import logging
import itertools

import django.core.mail
from django.http import Http404
from django.utils import timezone
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import (
    View, TemplateView, ListView, CreateView, UpdateView, DetailView,
)

from regnskab.forms import EmailTemplateForm
from regnskab.models import (
    EmailTemplate, Email,
    Profile, Session,
    get_profiles_title_status,
)
from regnskab.images.utils import save_png, png_data_uri

from .auth import regnskab_permission_required_method

logger = logging.getLogger('regnskab')


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

    @regnskab_permission_required_method
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
                format=self.object.format,
                created_by=self.request.user)
            backup.save()
            qs.update(email_template=backup)
        form.save()
        logger.info("%s: Ret emailskabelon %s",
                    self.request.user, self.kwargs['pk'])
        return redirect('regnskab:email_template_list')

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class EmailTemplateCreate(CreateView):
    template_name = 'regnskab/email_template_form.html'
    form_class = EmailTemplateForm

    def get_initial(self):
        name = self.request.GET.get('name', '')
        try:
            email_template = EmailTemplate.objects.get(
                name='Standard')
        except EmailTemplate.DoesNotExist:
            return dict(subject='[TK] Status på ølregningen',
                        name=name)
        else:
            return dict(subject=email_template.subject,
                        name=name,
                        body=email_template.body)

    def form_valid(self, form):
        o = form.save()
        logger.info("%s: Opret emailskabelon %s",
                    self.request.user, o.pk)
        return redirect('regnskab:email_template_list')

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class EmailList(TemplateView):
    template_name = 'regnskab/email_list.html'

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        self.regnskab_session = get_object_or_404(
            Session.objects, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_emails(self):
        period = self.regnskab_session.period
        time = self.regnskab_session.send_time
        profile_list = get_profiles_title_status(period=period, time=time)
        order = {p.id: i for i, p in enumerate(profile_list)}
        profiles = {p.id: p for p in profile_list}
        emails = list(Email.objects.filter(session_id=self.kwargs['pk']))
        emails.sort(key=lambda o: order.get(o.profile_id, 0))
        for o in emails:
            o.profile = profiles.get(o.profile_id, o.profile)
            o.title_name = getattr(o.profile, 'title_name', o.profile.name)
        return emails

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['object_list'] = self.get_emails()
        context_data['session'] = self.regnskab_session
        context_data['editable'] = not self.regnskab_session.sent
        return context_data


def get_image_for_emails(emails):
    import numpy as np
    import scipy.misc

    assert all(isinstance(email, Email) for email in emails)
    if not emails:
        return []

    session = emails[0].session
    assert all(email.session == session for email in emails)
    assert all(email.profile_id for email in emails)
    sheets = session.sheet_set.exclude(row_image=None)
    sheets = sheets.prefetch_related('sheetrow_set')
    rows_by_profile = {email.profile_id: [] for email in emails}
    for sheet in sheets:
        if not sheet.row_image:
            continue
        row_image = scipy.misc.imread(sheet.row_image)
        for row in sheet.sheetrow_set.all():
            try:
                p = rows_by_profile[row.profile_id]
            except KeyError:
                continue
            p.append(row_image[row.image_start:row.image_stop])
    for email in emails:
        images = rows_by_profile.pop(email.profile_id)
        if not images:
            yield None
            continue
        image_width = max(image.shape[1] for image in images)
        for i, image in enumerate(images):
            if image.shape[1] < image_width:
                images[i] = np.pad(
                    image,
                    [(0, 0), (0, image_width - image.shape[1])],
                    'maximum')
        images_concat = np.concatenate(images)
        yield images_concat


def get_image_for_email(email):
    result, = get_image_for_emails([email])
    return result


class EmailDetail(DetailView):
    template_name = 'regnskab/email_detail.html'

    @regnskab_permission_required_method
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
        context_data['images'] = self.get_images()
        return context_data

    def get_images(self):
        together = get_image_for_email(self.get_object())
        if together is not None:
            png_data = save_png(together)
            return png_data_uri(png_data)

    def get_object(self):
        return get_object_or_404(
            Email.objects,
            session_id=self.kwargs['pk'],
            profile_id=self.kwargs['profile'])


class EmailSend(View):
    @regnskab_permission_required_method
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
        for message, image in zip(messages, get_image_for_emails(emails)):
            if image is not None:
                png_data = save_png(image)
                message.attach('krydser.png', png_data, 'image/png')
        override_recipient = (len(messages) == 1 and
                              self.request.POST.get('override_recipient'))
        if override_recipient:
            for m in messages:
                m.to = [override_recipient]
        email_backend = django.core.mail.get_connection()
        if profile:
            logger.info("%s: Send email for %s i opgørelse %s til %s",
                        self.request.user, p, regnskab_session.pk,
                        override_recipient)
        else:
            logger.info("%s: Send emails i opgørelse %s",
                        self.request.user, regnskab_session.pk)
        email_backend.send_messages(messages)
        if override_recipient:
            return redirect('regnskab:email_list', pk=emails[0].session_id)
        else:
            regnskab_session.send_time = timezone.now()
            regnskab_session.save()
            return redirect('regnskab:home')
