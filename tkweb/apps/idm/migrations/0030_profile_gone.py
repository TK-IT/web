from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0029_rename_profile_gone_janej'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='gone',
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
    ]
