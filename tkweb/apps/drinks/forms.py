from django import forms

from tkweb.apps.drinks.models import Barcard

class BarcardGenForm(forms.Form):
    barcard = forms.ModelChoiceField(Barcard.objects.all())
