from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0016_populate_title_period'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='title',
            name='grad',
        ),
    ]
