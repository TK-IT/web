import re
import textwrap
from django import forms


class EmailForm(forms.Form):
    LINES = 'lines'
    PARAGRAPHS = 'paragraphs'
    NONE = 'none'
    WRAPPING = [(LINES, 'linjer'), (PARAGRAPHS, 'afsnit'), (NONE, 'ingen')]

    sender_name = forms.CharField(initial='BEST')
    sender_email = forms.CharField(initial='BEST')

    subject = forms.CharField()

    text = forms.CharField(widget=forms.Textarea)

    wrapping = forms.ChoiceField(choices=WRAPPING, initial=LINES)

    @staticmethod
    def perform_wrapping(text, wrapping):
        text = text.replace(u'\r', u'')

        if wrapping == u'paragraphs':
            paragraphs = re.findall(r'(.*?)(\n\n+|\n*$)', text, re.S)
            text = u''.join(
                u'%s%s'
                % ('\n'.join(textwrap.wrap(par, 79)),
                   sep)
                for par, sep in paragraphs)
        elif wrapping == 'lines':
            text = u''.join(
                u'%s\n' % u'\n'.join(textwrap.wrap(line, 79))
                for line in text.splitlines())

        return text

    def clean(self):
        cleaned_data = super(EmailForm, self).clean()
        if 'text' in cleaned_data and 'wrapping' in cleaned_data:
            t0 = cleaned_data['text']
            wrapping = cleaned_data['wrapping']
            t1 = self.perform_wrapping(t0, wrapping)
            t2 = self.perform_wrapping(t1, wrapping)
            if t1 != t2:
                raise ValueError("Line wrapping failed (no fixpoint)")
            cleaned_data['wrapped_text'] = t1
        return cleaned_data
