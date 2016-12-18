from django import forms

from uniprint.models import Document, Printer
import uniprint.options


class PrintoutForm(forms.Form):
    document = forms.ModelChoiceField(Document.objects.all())
    printer = forms.ModelChoiceField(Printer.objects.all())
    copies = forms.IntegerField(initial=1)
    page_range = forms.CharField(required=False)

    def clean_option(self):
        choice_objects = uniprint.options.choices
        key = self.cleaned_data['option']
        return next(o for o in choice_objects if o.key == key)

    def __init__(self):
        choice_objects = uniprint.options.choices
        choices = [(c.key, c.name) for c in choice_objects]
        self.fields['option'] = forms.ChoiceField(
            choices=choices, initial=choice_objects[0].key)
