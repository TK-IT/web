from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0027_populate_profile_allow_direct_email'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='accepterdirektemail',
        ),
    ]
