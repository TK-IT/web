import re
import textwrap
from django import forms
from multiupload.fields import MultiFileField
from tkweb.apps.mailinglist.models import SharedFile


class EmailForm(forms.Form):
    LINES = 'lines'
    PARAGRAPHS = 'paragraphs'
    NONE = 'none'
    WRAPPING = [(LINES, 'linjer'), (PARAGRAPHS, 'afsnit'), (NONE, 'ingen')]

    sender_name = forms.CharField(
        initial='BEST',
        widget=forms.TextInput(attrs={'size': 10, 'class': 'form-control'}),
    )
    sender_email = forms.CharField(
        initial='BEST',
        widget=forms.TextInput(attrs={'size': 10, 'class': 'form-control'}),
    )

    subject = forms.CharField(
        widget=forms.TextInput(attrs={'size': 50, 'class': 'form-control'}),
    )

    text = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 20, 'cols': 90, 'class': 'form-control'}),
    )

    wrapping = forms.ChoiceField(
        choices=WRAPPING,
        initial=LINES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

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


class FileForm(forms.Form):
    files = MultiFileField()

    def clean_files(self):
        files = self.cleaned_data.get('files', [])
        return [SharedFile(file=file) for file in files]
