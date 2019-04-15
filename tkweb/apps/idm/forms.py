from django import forms


class GfyearBestForm(forms.Form):
    period = forms.IntegerField()

    def __init__(self, **kwargs):
        profiles = kwargs.pop('profiles')
        self.roots = kwargs.pop('roots')
        super().__init__(**kwargs)
        choices = [(None, '---')] + [(profile.id, profile.name) for profile in profiles]
        self.profiles = {profile.id: profile for profile in profiles}
        for root in self.roots:
            self.fields[root] = forms.ChoiceField(required=False, choices=choices)
