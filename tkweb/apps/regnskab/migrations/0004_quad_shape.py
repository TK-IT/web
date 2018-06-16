from django.db import migrations, models


def get_shape(q):
    n = len(q)
    m = len(q[0])
    if all(len(r) == m for r in q):
        return (n, m)


def transpose(xs):
    return list(zip(*xs))


def set_shapes(qs, from_shape, to_shape):
    for o in qs:
        shape = get_shape(o.quad)
        if shape is None:
            print("Object %s: %s has unrecognizable shape" %
                  (o.pk, o.quad))
        elif shape == from_shape:
            o.quad = transpose(o.quad)
            assert get_shape(o.quad) == to_shape
            o.save()


def quad_shape(apps, schema_editor):
    SheetImage = apps.get_model('regnskab', 'SheetImage')
    set_shapes(SheetImage.objects.all(), (4, 2), (2, 4))


def quad_shape_reverse(apps, schema_editor):
    SheetImage = apps.get_model('regnskab', 'SheetImage')
    set_shapes(SheetImage.objects.all(), (2, 4), (4, 2))


class Migration(migrations.Migration):

    dependencies = [
        ('regnskab', '0003_sheetimage_parameters'),
    ]

    operations = [
        migrations.RunPython(quad_shape, quad_shape_reverse),
    ]
