from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0019_remove_useless_groups'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='type',
            field=models.IntegerField(default=0),
        ),
        migrations.RemoveField(
            model_name='group',
            name='type',
        ),
    ]
