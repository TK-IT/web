import logging
import itertools

import django.core.mail
from django.core.exceptions import ValidationError
from django.http import Http404
from django.utils import timezone
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import (
    View, TemplateView, ListView, CreateView, UpdateView, DetailView, FormView,
)

from tkweb.apps.regnskab.forms import EmailTemplateForm, AnonymousEmailTemplateForm
from tkweb.apps.regnskab.models import (
    EmailTemplate, Email,
    Profile, Session,
    get_profiles_title_status, config,
    Newsletter, NewsletterEmail,
)
from tkweb.apps.regnskab.images.utils import save_png, png_data_uri

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
        self.object.make_template_editable()
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


class NewsletterList(ListView):
    model = Newsletter
    template_name = 'regnskab/newsletter_list.html'

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class NewsletterCreate(FormView):
    form_class = AnonymousEmailTemplateForm
    template_name = 'regnskab/newsletter_create.html'

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        template = EmailTemplate(
            name='',
            subject=form.cleaned_data['subject'],
            body=form.cleaned_data['body'],
            format=form.cleaned_data['format'],
            markup=form.cleaned_data['markup'],
            created_by=self.request.user)
        template.save()
        newsletter = Newsletter(
            email_template=template,
            period=config.GFYEAR,
            created_by=self.request.user)
        newsletter.save()
        try:
            template.clean()
            newsletter.regenerate_emails()
        except ValidationError as exn:
            newsletter.delete()
            template.delete()
            form.add_error(None, exn)
            return self.form_invalid(form)
        return redirect('regnskab:newsletter_update', pk=newsletter.pk)


class NewsletterUpdate(FormView):
    form_class = AnonymousEmailTemplateForm
    template_name = 'regnskab/newsletter_update.html'

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(Newsletter, pk=kwargs['pk'])
        self.email_template = self.object.email_template
        refs = self.email_template.refcount()
        if refs != 1:
            raise ValueError(
                "Newsletter %s's EmailTemplate %s has incorrect refcount %s" %
                (self.object.id, self.email_template.id, refs))
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.email_template
        return kwargs

    def form_valid(self, form):
        self.email_template.subject = form.cleaned_data['subject']
        self.email_template.body = form.cleaned_data['body']
        self.email_template.format = form.cleaned_data['format']
        self.email_template.markup = form.cleaned_data['markup']
        self.email_template.created_by = self.request.user
        try:
            self.email_template.clean()
            self.object.regenerate_emails()
        except ValidationError as exn:
            form.add_error(None, exn)
            return self.form_invalid(form)
        self.email_template.save()
        return redirect('regnskab:newsletter_update',
                        pk=self.object.pk)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['object'] = self.object
        return context_data


class EmailListBase(TemplateView):
    def get_emails(self):
        period = self.object.period
        time = self.object.send_time
        profile_list = get_profiles_title_status(period=period, time=time)
        order = {p.id: i for i, p in enumerate(profile_list)}
        profiles = {p.id: p for p in profile_list}
        emails = list(self.object.email_set.all())
        emails.sort(key=lambda o: order.get(o.profile_id, 0))
        for o in emails:
            try:
                o.profile = profiles[o.profile_id]
            except KeyError:
                pass
            o.title_name = getattr(o.profile, 'title_name', o.profile.name)
        return emails

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['object_list'] = self.get_emails()
        return context_data


class EmailList(EmailListBase):
    template_name = 'regnskab/email_list.html'

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        self.regnskab_session = self.object = get_object_or_404(
            Session.objects, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['session'] = self.regnskab_session
        return context_data


class NewsletterEmailList(EmailListBase):
    template_name = 'regnskab/newsletter_email_list.html'

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(
            Newsletter.objects, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['object'] = self.object
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


class NewsletterEmailDetail(DetailView):
    template_name = 'regnskab/newsletter_email_detail.html'

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        self.newsletter = get_object_or_404(Newsletter, pk=self.kwargs['pk'])
        self.profile = get_object_or_404(
            Profile.objects, pk=self.kwargs['profile'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['newsletter'] = self.newsletter
        context_data['profile'] = self.profile
        return context_data

    def get_object(self):
        return get_object_or_404(
            NewsletterEmail,
            newsletter_id=self.kwargs['pk'],
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


class NewsletterEmailSend(View):
    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk, profile=None):
        newsletter = get_object_or_404(Newsletter, pk=pk)
        if profile is None:
            qs = NewsletterEmail.objects.filter(newsletter=newsletter)
        else:
            p = get_object_or_404(Profile.objects, pk=profile)
            qs = NewsletterEmail.objects.filter(newsletter=newsletter,
                                                profile=p)

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
        if profile:
            logger.info("%s: Send email for %s i nyhedsbrev %s til %s",
                        self.request.user, p, newsletter.pk,
                        override_recipient)
        else:
            logger.info("%s: Send emails i nyhedsbrev %s",
                        self.request.user, newsletter.pk)
        email_backend.send_messages(messages)
        if not override_recipient:
            newsletter.send_time = timezone.now()
            newsletter.save()
        return redirect('regnskab:newsletter_email_list', pk=pk)
