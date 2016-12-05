import itertools

import django.core.mail
from django.http import Http404
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import (
    View, ListView, CreateView, UpdateView, DetailView,
)

from regnskab.forms import EmailTemplateForm
from regnskab.models import (
    EmailTemplate, Email,
    Profile, Session,
)

from .base import regnskab_permission_required


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
