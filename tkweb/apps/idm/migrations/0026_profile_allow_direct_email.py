from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0025_remove_profile_accepteremail'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='allow_direct_email',
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
    ]
