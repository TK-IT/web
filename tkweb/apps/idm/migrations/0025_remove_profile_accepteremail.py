from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0024_add_mailing_list_group'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='accepteremail',
        ),
    ]
