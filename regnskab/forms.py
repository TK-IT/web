import collections
from django import forms
from django.core.exceptions import ValidationError
from regnskab.models import EmailTemplate, EmailBatch


class SheetCreateForm(forms.Form):
    name = forms.CharField(max_length=200, required=False)
    start_date = forms.DateField()
    end_date = forms.DateField()
    kinds = forms.CharField(widget=forms.Textarea)

    def clean_kinds(self):
        s = self.cleaned_data['kinds']
        kinds = []
        for line in s.splitlines():
            if not line:
                continue
            try:
                name, price = line.split()
            except ValueError:
                raise ValidationError("Not two words: %r" % line)
            try:
                kinds.append(dict(name=name, price=float(price)))
            except ValueError:
                raise ValidationError("Not a number: %r" % price)
        names = collections.Counter(o['name'] for o in kinds)
        dups = {k: v for k, v in names.items() if v > 1}
        if dups:
            raise ValidationError("Duplicate names: %r" % (dups,))
        return kinds


class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ('name', 'subject', 'body', 'format')


class EmailBatchForm(forms.ModelForm):
    class Meta:
        model = EmailBatch
        fields = ('template',)
