from django.db.models import F, Sum


def sum_matrix(qs, column_spec, row_spec, value_spec):
    qs = qs.order_by()
    qs = qs.annotate(row_spec=F(row_spec), column_spec=F(column_spec))
    qs = qs.values('row_spec', 'column_spec')
    qs = qs.annotate(value_spec=Sum(value_spec))
    res = {}
    for record in qs:
        row = record.pop('row_spec')
        column = record.pop('column_spec')
        value = record.pop('value_spec')
        cells = res.setdefault(column, {})
        assert row not in cells
        cells[row] = value
    return res
