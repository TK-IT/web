import collections
from django import forms
from django.core.exceptions import ValidationError
from regnskab.models import EmailTemplate, Session, config


class SheetCreateForm(forms.Form):
    name = forms.CharField(max_length=200, required=False)
    period = forms.IntegerField()
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
                name, unit_price = line.split()
            except ValueError:
                raise ValidationError("Not two words: %r" % line)
            try:
                kinds.append(dict(name=name, unit_price=float(unit_price)))
            except ValueError:
                raise ValidationError("Not a number: %r" % unit_price)
        names = collections.Counter(o['name'] for o in kinds)
        dups = {k: v for k, v in names.items() if v > 1}
        if dups:
            raise ValidationError("Duplicate names: %r" % (dups,))
        return kinds


class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ('name', 'subject', 'body', 'format')
        widgets = {'subject': forms.TextInput(attrs={'size': 60})}

    name = forms.CharField(required=True)


class SessionForm(forms.Form):
    subject = forms.CharField(max_length=200,
                              widget=forms.TextInput(attrs={'size': 60}))
    body = forms.CharField(widget=forms.Textarea(attrs={'cols': 70, 'rows': 20}))
    format = forms.ChoiceField(choices=EmailTemplate.FORMAT)
    name = forms.CharField(max_length=200, required=False,
                           label='Gem emailskabelon som')


class TransactionBatchForm(forms.Form):
    def __init__(self, **kwargs):
        profiles = kwargs.pop('profiles')
        super().__init__(**kwargs)
        self._profiles = []
        GFYEAR = config.GFYEAR
        for profile, amount, selected in profiles:
            p = 'profile%d_' % profile.id
            if profile.title:
                profile.display_name = ('%s %s' %
                                        (profile.title.display_title(GFYEAR),
                                         profile.name))
            else:
                profile.display_name = profile.name
            self.fields[p + 'selected'] = forms.BooleanField(
                initial=selected,
                required=False, label='%s markeret' % profile.display_name)
            amount_str = '%g' % amount
            try:
                int(amount_str)
            except ValueError:
                amount_str = '%.2f' % amount
            self.fields[p + 'amount'] = forms.FloatField(
                initial=amount_str, label='%s beløb' % profile.display_name,
                widget=forms.TextInput())
            self._profiles.append(profile)

    def profile_fields(self):
        for profile in self._profiles:
            p = 'profile%d_' % profile.id
            yield (profile, self[p + 'amount'], self[p + 'selected'])

    def profile_data(self):
        data = self.cleaned_data
        for profile in self._profiles:
            p = 'profile%d_' % profile.id
            yield (profile, data[p + 'amount'], data[p + 'selected'])


class OtherExpenseBatchForm(PaymentBatchForm):
    note = forms.CharField(max_length=255)
