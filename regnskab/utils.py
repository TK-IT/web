from django.db.models import F, Sum


def sum_vector(qs, index_spec, value_spec):
    '''
    Sum queryset values, grouping over given dimension.

    sum_matrix(Foo.objects.all(), 'c', 'z') turns into the SQL query:

    SELECT Foo.c, SUM(Foo.z) FROM Foo GROUP BY Foo.c

    The result is a mapping `d` such that d[x]
    is the sum of z values where c = x.
    '''
    qs = qs.order_by()
    qs = qs.annotate(index_spec=F(index_spec))
    qs = qs.values('index_spec')
    qs = qs.annotate(value_spec=Sum(value_spec))
    res = {}
    for record in qs:
        index = record.pop('index_spec')
        assert index not in res
        res[index] = record.pop('value_spec')
    return res


def sum_matrix(qs, column_spec, row_spec, value_spec):
    '''
    Sum queryset values, grouping over two dimensions.

    sum_matrix(Foo.objects.all(), 'c1', 'c2', 'z') turns into the SQL query:

    SELECT Foo.c1, Foo.c2, SUM(Foo.z) FROM Foo GROUP BY Foo.c1, Foo.c2

    The result is a nested mapping `d` such that d[x1][x2]
    is the sum of z values where c1 = x1 and c2 = x2.
    '''
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
