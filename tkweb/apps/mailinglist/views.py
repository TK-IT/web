from collections import OrderedDict
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect
from django.views.generic import FormView, ListView
import django.core.mail
from django.core.mail import EmailMessage
from tkweb.apps.mailinglist.forms import EmailForm, FileForm
from tkweb.apps.mailinglist.models import SharedFile
from tkweb.apps.idm.models import Group


send_permission_required = permission_required(
    'mailinglist.send', raise_exception=True)


class EmailFormView(FormView):
    template_name = 'mailinglist/email_form.html'
    form_class = EmailForm

    @method_decorator(send_permission_required)
    def dispatch(self, request, *args, **kwargs):
        return super(EmailFormView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('email_form')

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if request.POST.get('wrap'):
            # Don't check if form is valid; just wrap text and redisplay.
            kwargs = self.get_form_kwargs()
            data = kwargs['data'].copy()
            data['text'] = form.perform_wrapping(data['text'],
                                                 data['wrapping'])
            kwargs['data'] = data
            form = self.get_form_class()(**kwargs)
            return self.render_to_response(self.get_context_data(form=form))
        elif request.POST.get('send') or request.POST.get('only_me'):
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        else:
            form.add_error(None, 'Tryk på en knap')
            return self.form_invalid(form)

    def get_recipients(self, form):
        group = Group.objects.get(regexp=Group.REGEXP_MAILING_LIST)
        recipients = group.profile_set.all()
        recipients = recipients.exclude(email='')
        email_addresses = recipients.values_list('email', flat=True)
        return sorted(email_addresses)

    def translate_subject(self, subject):
        if '[TK' in subject:
            # No change
            return subject
        else:
            return '[TK] %s' % (subject,)

    def form_valid(self, form):
        data = form.cleaned_data
        subject = data['subject']
        subject = self.translate_subject(subject)
        text = data['wrapped_text']
        from_email = '%s@TAAGEKAMMERET.dk' % (data['sender_email'],)
        from_field = '"%s" <%s>' % (data['sender_name'], from_email)

        recipients = self.get_recipients(form)

        if self.request.POST.get('only_me'):
            recipients = [self.request.user.email]

        sender = 'admin@TAAGEKAMMERET.dk'
        list_name = 'mailinglist'
        list_id = '%s.TAAGEKAMMERET.dk' % list_name
        unsub = '<mailto:%s?subject=unsubscribe%%20%s>' % (sender, list_name)
        help = '<mailto:%s?subject=list-help>' % (sender,)
        sub = '<mailto:%s?subject=subscribe%%20%s>' % (sender, list_name)

        messages = []
        for recipient in recipients:
            headers = OrderedDict([
                ('From', from_field),
                ('X-TK-Recipient', recipient),
                ('X-TK-Sender', self.request.user.get_full_name()),
                ('Sender', sender),
                ('List-Name', list_name),
                ('List-Id', list_id),
                ('List-Unsubscribe', unsub),
                ('List-Help', help),
                ('List-Subscribe', sub),
                ('Precedence', 'bulk'),
                ('X-Auto-Response-Suppress', 'OOF'),
                ('Organization', 'TÅGEKAMMERET'),
            ])

            msg = EmailMessage(
                subject=subject,
                body=text,
                from_email='admin@TAAGEKAMMERET.dk',
                bcc=[recipient],
                headers=headers,
            )
            messages.append(msg)

        email_backend = django.core.mail.get_connection()
        email_backend.send_messages(messages)
        return HttpResponseRedirect(self.get_success_url())


class FileList(ListView):
    queryset = SharedFile.objects.all()
    template_name = 'mailinglist/file_list.html'

    @method_decorator(send_permission_required)
    def dispatch(self, request, *args, **kwargs):
        return super(FileList, self).dispatch(request, *args, **kwargs)


class FileCreate(FormView):
    form_class = FileForm
    template_name = 'mailinglist/file_create.html'

    @method_decorator(send_permission_required)
    def dispatch(self, request, *args, **kwargs):
        return super(FileCreate, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        for i in form.cleaned_data['files']:
            i.creator = self.request.user
            i.save()
        return HttpResponseRedirect(reverse('file_list'))
