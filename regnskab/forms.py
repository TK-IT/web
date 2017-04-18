import collections
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from regnskab.models import EmailTemplate, Session, config
from regnskab.widgets import RichTextarea
from regnskab.utils import plain_to_html, html_to_plain
import tktitler as tk


def placeholder_from_help(cls):
    for f in cls.base_fields.values():
        if f.help_text and 'placeholder' not in f.widget.attrs:
            f.widget.attrs['placeholder'] = f.help_text
            f.help_text = None
    return cls


@placeholder_from_help
class SheetCreateForm(forms.Form):
    start_date = forms.DateField(label='På-dato',
                                 help_text='Format DD.MM.YYYY')
    end_date = forms.DateField(label='Af-dato',
                               help_text='Format DD.MM.YYYY')
    image_file = forms.FileField(label='Scannet PDF',
                                 required=False)
    name = forms.CharField(max_length=200, required=False,
                           label='Særlig krydsliste',
                           help_text='(f.eks. revy)')
    period = forms.IntegerField(label='Bestyrelsesår')
    kinds = forms.CharField(widget=forms.Textarea,
                            label='Priser')

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
        fields = ('name', 'subject', 'body', 'format', 'markup')
        widgets = {'subject': forms.TextInput(attrs={'size': 60})}

    name = forms.CharField(required=True)
    initial_markup = forms.ChoiceField(
        choices=EmailTemplate.MARKUP, widget=forms.HiddenInput())

    @staticmethod
    def initial_body(instance):
        if instance is None:
            return ''
        if instance.markup == EmailTemplate.HTML:
            return instance.body_html_data_uris()
        elif instance.markup == EmailTemplate.PLAIN:
            return instance.body_plain()
        else:
            raise ValueError(instance.markup)

    @staticmethod
    def convert_body(body, in_, out):
        if in_ == EmailTemplate.PLAIN and out == EmailTemplate.HTML:
            return plain_to_html(body)
        elif in_ == EmailTemplate.HTML and out == EmailTemplate.PLAIN:
            return html_to_plain(body)
        else:
            assert in_ == out
            return body

    def __init__(self, **kwargs):
        instance = kwargs.get('instance')
        initial = kwargs.setdefault('initial', {})
        initial.setdefault('body', EmailTemplateForm.initial_body(instance))
        super().__init__(**kwargs)
        if instance and instance.markup == EmailTemplate.HTML:
            self.fields['body'].widget = RichTextarea()
            self.fields['initial_markup'].initial = EmailTemplate.HTML
        else:
            self.fields['initial_markup'].initial = EmailTemplate.PLAIN

    def clean(self):
        cleaned_data = super().clean()
        try:
            body = cleaned_data['body']
            in_ = cleaned_data['initial_markup']
            out = cleaned_data['markup']
        except KeyError:
            pass
        else:
            cleaned_data['body'] = EmailTemplateForm.convert_body(
                body, in_, out)
        return cleaned_data

    def save(self):
        instance = super().save(commit=False)
        instance.clean()
        instance.save()
        self.save_m2m()
        return instance


class AnonymousEmailTemplateForm(forms.Form):
    subject = forms.CharField(max_length=200, initial='[TK] ',
                              widget=forms.TextInput(attrs={'size': 60}))
    body = forms.CharField(widget=forms.Textarea(attrs={'cols': 70, 'rows': 20}))
    format = forms.ChoiceField(choices=EmailTemplate.FORMAT, initial=EmailTemplate.POUND)
    markup = forms.ChoiceField(choices=EmailTemplate.MARKUP, initial=EmailTemplate.PLAIN)
    initial_markup = forms.ChoiceField(
        choices=EmailTemplate.MARKUP, widget=forms.HiddenInput())

    def __init__(self, **kwargs):
        instance = kwargs.pop('instance', None)
        initial = kwargs.setdefault('initial', {})
        data = kwargs.get('data', {})
        initial.setdefault('body', EmailTemplateForm.initial_body(instance))
        if instance:
            initial.setdefault('subject', instance.subject)
            initial.setdefault('format', instance.format)
            initial.setdefault('markup', instance.markup)
        super().__init__(**kwargs)

        if instance:
            initial_markup = instance.markup
        elif data and data.get('body'):
            initial_markup = data.get('initial_markup', EmailTemplate.PLAIN)
        else:
            # Consider the following scenario.
            # The user wants to create a Newsletter in HTML markup.
            # The user goes to NewsletterCreate, changes Markup to HTML
            # from the default PLAIN, and presses submit.  In this case,
            # the form is invalid since body is required but empty.
            # We want to redisplay the erroneous form with the HTML widget
            # instead of the PLAIN widget. This is only safe to do when
            # body is empty; otherwise, we would need to convert between
            # PLAIN and HTML, which we shouldn't do at this point.
            initial_markup = data.get('markup', EmailTemplate.PLAIN)

        if initial_markup == EmailTemplate.HTML:
            self.fields['body'].widget = RichTextarea()
            self.fields['initial_markup'].initial = EmailTemplate.HTML
        else:
            self.fields['initial_markup'].initial = EmailTemplate.PLAIN

    def clean(self):
        cleaned_data = super().clean()
        try:
            body = cleaned_data['body']
            in_ = cleaned_data['initial_markup']
            out = cleaned_data['markup']
        except KeyError:
            pass
        else:
            cleaned_data['body'] = EmailTemplateForm.convert_body(
                body, in_, out)
        return cleaned_data


class TransactionBatchForm(forms.Form):
    @tk.set_gfyear(lambda: config.GFYEAR)
    def __init__(self, **kwargs):
        profiles = kwargs.pop('profiles')
        super().__init__(**kwargs)
        self._profiles = []
        for profile, amount, selected in profiles:
            p = 'profile%d_' % profile.id
            if profile.title:
                profile.display_name = (
                    '%s %s' %
                    (tk.prefix(profile.title, type='unicode')
                     if profile.title.period else profile.title.root,
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


class BalancePrintForm(forms.Form):
    PDF, SOURCE, PRINT = 'pdf', 'source', 'print'
    print_choices = [
        (PDF, 'Hent som PDF'),
        (SOURCE, 'Hent TeX-kildekode'),
        (PRINT, 'Print på A2'),
    ]

    highlight = forms.BooleanField(required=False, initial=True)
    mode = forms.ChoiceField(choices=print_choices, initial='pdf')


@placeholder_from_help
class SheetRowForm(forms.Form):
    start_date = forms.DateField(label='På-dato',
                                 help_text='Format DD.MM.YYYY')
    end_date = forms.DateField(label='Af-dato',
                               help_text='Format DD.MM.YYYY')
    data = forms.CharField(
        widget=forms.HiddenInput(
            attrs=dict(id='tk_rows')))


@placeholder_from_help
class ProfileListForm(forms.Form):
    purchases_after = forms.DateField(label='Forbrug siden', required=False,
                                      help_text='Format DD.MM.YYYY')
