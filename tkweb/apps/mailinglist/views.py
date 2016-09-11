from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import permission_required
from django.views.generic import FormView
from tkweb.apps.mailinglist.forms import EmailForm


class EmailFormView(FormView):
    template_name = 'email_form.html'
    form_class = EmailForm

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
            form = form_class(**kwargs)
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

    def form_valid(self, form):
        data = form.cleaned_data
        subject = data['subject']
        text = data['wrapped_text']
        from_email = '%s@TAAGEKAMMERET.dk' % (data['sender_email'],)
        from_field = '"%s" <%s>' % (data['sender_name'], from_email)

        recipients = self.get_recipients(form)

        if data['only_me']:
            recipients = [self.request.user.email]

        messages = []
        for recipient in recipients:
            headers = {
                'From': from_field,
                'X-TK-Recipient': recipient,
                'X-TK-Sender': self.request.user.get_full_name(),
            }
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
