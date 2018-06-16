from django.db import migrations, models


def strip_names(apps, schema_editor):
    Profile = apps.get_model('idm', 'Profile')
    for p in Profile.objects.all():
        if p.name != p.name.strip():
            p.name = p.name.strip()
            p.save()


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0039_gone_default'),
    ]

    operations = [
        migrations.RunPython(strip_names),
    ]
