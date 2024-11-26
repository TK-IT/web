from collections import OrderedDict
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect
from django.views.generic import FormView, ListView
import django.core.mail
from django.core.mail import EmailMessage
from tkweb.apps.mailinglist.forms import EmailForm, FileForm, EmailToRecipientsForm
from tkweb.apps.mailinglist.models import SharedFile
from tkweb.apps.idm.models import Group


@method_decorator(permission_required("mailinglist.send"), name="dispatch")
class EmailFormView(FormView):
    template_name = 'mailinglist/email_form.html'
    form_class = EmailForm

    def get_success_url(self):
        return reverse('email_form')

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if request.POST.get('send') or request.POST.get('only_me'):
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        else:
            form.add_error(None, 'Tryk på en knap')
            return self.form_invalid(form)

    def get_recipients(self, form):
        "Overridden in EmailToRecipientsFormView."
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
        text = data['text'].replace("\r", "")
        from_email = '%s@TAAGEKAMMERET.dk' % (data['sender_email'],)
        from_field = '"%s" <%s>' % (data['sender_name'], from_email)

        recipients = self.get_recipients(form)

        if self.request.POST.get('only_me'):
            recipients = [self.request.user.email]

        sender = from_email
        list_requests = 'admin@TAAGEKAMMERET.dk'
        list_id = 'mailinglist.TAAGEKAMMERET.dk'
        unsub = '<mailto:%s?subject=unsubscribe%%20haengerlisten>' % (list_requests,)
        help = '<mailto:%s?subject=list-help>' % (list_requests,)
        sub = '<mailto:%s?subject=subscribe%%20haengerlisten>' % (list_requests,)

        messages = []
        for recipient in recipients:
            headers = OrderedDict([
                ('From', from_field),
                ('X-TK-Recipient', recipient),
                ('X-TK-Sender', self.request.user.get_full_name()),
                ('Sender', sender),
                ('List-Name', "mailinglist"),
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
                from_email=sender,
                bcc=[recipient],
                headers=headers,
            )
            messages.append(msg)

        email_backend = django.core.mail.get_connection()
        email_backend.send_messages(messages)
        return HttpResponseRedirect(self.get_success_url())


class EmailToRecipientsFormView(EmailFormView):
    form_class = EmailToRecipientsForm

    def get_success_url(self):
        return reverse('email_to_recipients_form')

    def get_recipients(self, form):
        return form.cleaned_data["recipients"].split()


@method_decorator(permission_required("mailinglist.send"), name="dispatch")
class FileList(ListView):
    queryset = SharedFile.objects.all()
    template_name = 'mailinglist/file_list.html'


@method_decorator(permission_required("mailinglist.send"), name="dispatch")
class FileCreate(FormView):
    form_class = FileForm
    template_name = 'mailinglist/file_create.html'

    def form_valid(self, form):
        for i in form.cleaned_data['files']:
            i.creator = self.request.user
            i.save()
        return HttpResponseRedirect(reverse('file_list'))
