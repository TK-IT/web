from django import forms
from regnskab.images.quadrilateral import Quadrilateral


class SheetImageForm(forms.Form):
    def __init__(self, **kwargs):
        sheet_image = self.instance = kwargs.pop('instance')
        super().__init__(**kwargs)
        cross_matrix = sheet_image.crosses
        crosses = {(i, j)
                   for i, row in enumerate(cross_matrix)
                   for j, v in enumerate(row) if v}
        row_y = [0] + sheet_image.rows + [1]
        col_x = sheet_image.cols + [1]
        quad = Quadrilateral(sheet_image.quad)
        for i, (y1, y2) in enumerate(zip(row_y[:-1], row_y[1:])):
            for j, (x1, x2) in enumerate(zip(col_x[:-1], col_x[1:])):
                v = (i, j) in crosses
                (x,), (y,) = quad.to_world(
                    [[(x1 + x2) / 2], [(y1 + y2) / 2]])
                attrs = {'data-x': x, 'data-y': y}
                self.fields['c-%s-%s' % (i, j)] = forms.BooleanField(
                    initial=v, required=False,
                    widget=forms.CheckboxInput(attrs=attrs))

    def get_crosses(self):
        sheet_image = self.instance
        data = self.cleaned_data
        n_rows = len(sheet_image.rows) + 1
        n_cols = len(sheet_image.cols)
        return [[bool(data.get('c-%s-%s' % (i, j)))
                 for j in range(n_cols)]
                for i in range(n_rows)]
