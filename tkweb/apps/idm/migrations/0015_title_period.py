from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0014_remove_title_inttitel'),
    ]

    operations = [
        migrations.AddField(
            model_name='title',
            name='period',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
