import re
import textwrap
from django import forms
from multiupload.fields import MultiFileField
from tkweb.apps.mailinglist.models import SharedFile


class EmailForm(forms.Form):
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


class FileForm(forms.Form):
    files = MultiFileField()

    def clean_files(self):
        files = self.cleaned_data.get('files', [])
        return [SharedFile(file=file) for file in files]
