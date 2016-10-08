from django import forms


class SheetCreateForm(forms.Form):
    name = forms.CharField(max_length=200, required=False)
    start_date = forms.DateField()
    end_date = forms.DateField()
