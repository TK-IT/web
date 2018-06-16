from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0020_remove_group_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='relativ',
            field=models.IntegerField(default=0),
        ),
        migrations.RemoveField(
            model_name='group',
            name='relativ',
        ),
    ]
