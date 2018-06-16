from django.db import migrations, models


def cutoff_values(apps, schema_editor):
    SheetImage = apps.get_model('regnskab', 'SheetImage')
    for o in SheetImage.objects.all():
        if o.parameters.get('extract_person_rows.cutoff') == 1:
            o.parameters['extract_person_rows.cutoff'] = 0.5
        if o.parameters.get('extract_rows.cutoff') == 1:
            o.parameters['extract_rows.cutoff'] = 0.5
        o.save()


class Migration(migrations.Migration):

    dependencies = [
        ('regnskab', '0005_sheetimage_fields'),
    ]

    operations = [
        migrations.RunPython(cutoff_values, lambda *args: None),
    ]
