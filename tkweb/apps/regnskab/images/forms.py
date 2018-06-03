import json

from django import forms


class SheetImageParametersForm(forms.Form):
    reset = forms.BooleanField(required=False)

    def __init__(self, **kwargs):
        parameters = kwargs.pop("parameters")
        super().__init__(**kwargs)
        field_types = {int: forms.IntegerField, float: forms.FloatField}
        for k in sorted(parameters):
            field_type = field_types[type(parameters[k])]
            self.fields[k] = field_type(initial=parameters[k])


class SheetImageCrossesForm(forms.Form):
    verified = forms.BooleanField(required=False, label="Markér som færdig")
    data = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, **kwargs):
        sheet_image = self.instance = kwargs.pop("instance")
        super().__init__(**kwargs)
        cross_matrix = sheet_image.crosses
        crosses = [
            (i, j) for i, row in enumerate(cross_matrix) for j, v in enumerate(row) if v
        ]
        self.fields["data"].initial = json.dumps(
            dict(crosses=crosses, boxes=sheet_image.boxes), indent=2
        )

    def clean_data(self):
        return json.loads(self.cleaned_data["data"])

    def get_crosses(self):
        sheet_image = self.instance
        data = self.cleaned_data["data"]
        s = set(map(tuple, data["crosses"]))
        n_rows = len(sheet_image.rows) - 1
        n_cols = len(sheet_image.cols) - 1
        return [[bool((i, j) in s) for j in range(n_cols)] for i in range(n_rows)]

    def get_boxes(self):
        return self.cleaned_data["data"]["boxes"]
