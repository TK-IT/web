from django import forms
from krydsliste.models import Sheet


FRONT_INITIAL = '\n'.join(
    r'\person{%s}' % p
    for p in (
        r'\CERM FORM INKA \KASS NF PR SEKR \VC FUAN'.split() +
        9*['FU'] + ['EFUIT'] + 12*['']))
BACK_INITIAL = '\n'.join(24*[r'\person{}'] + 15*[r'\lille{}'])


class SheetForm(forms.ModelForm):
    PDF, SOURCE, PRINT = 'pdf', 'source', 'print'
    print_choices = [
        (PDF, 'Hent som PDF'),
        (SOURCE, 'Hent TeX-kildekode'),
        (PRINT, 'Print på A2'),
    ]

    class Meta:
        model = Sheet
        fields = ('name', 'title', 'left_label', 'right_label', 'column1',
                  'column2', 'column3', 'front_persons', 'back_persons')

    name = forms.CharField(label='Navn')
    title = forms.CharField(label='Overskrift', initial=r'\TKETs krydsliste')
    column1 = forms.CharField(label='Søjle 1', initial=r'Alm. øl og cocio')
    column2 = forms.CharField(label='Søjle 2', initial=r'Guldøl')
    column3 = forms.CharField(label='Søjle 3', initial=r'Vand')
    left_label = forms.CharField(label='På', initial=r'På: \dato')
    right_label = forms.CharField(label='Af', initial=r'Af: \dato')
    front_persons = forms.CharField(label='Indgange på forside',
                                    initial=FRONT_INITIAL,
                                    widget=forms.Textarea(attrs={'rows': 39}))
    back_persons = forms.CharField(label='Indgange på bagside',
                                   initial=BACK_INITIAL,
                                   widget=forms.Textarea(attrs={'rows': 39}))
    print_mode = forms.ChoiceField(choices=print_choices, initial='pdf')
