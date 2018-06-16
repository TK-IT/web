from django.db import models, migrations


def fix_emails(apps, schema_editor):
    Profile = apps.get_model('idm', 'Profile')
    save = []
    for p in Profile.objects.all():
        e = p.email
        e = e.replace('&#064;', '@')
        e = e.replace(' ', '')
        if e != p.email:
            p.email = e
            save.append(p)
    for p in save:
        p.save()


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0033_add_verbose_names'),
    ]

    operations = [
        migrations.RunPython(fix_emails,
                             lambda apps, schema_editor: None)
    ]
