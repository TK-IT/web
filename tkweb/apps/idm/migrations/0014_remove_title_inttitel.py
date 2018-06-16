from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0013_kind_not_null'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='title',
            name='inttitel',
        ),
    ]
