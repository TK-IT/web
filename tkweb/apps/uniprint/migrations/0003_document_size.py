from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uniprint', '0002_printout_page_range'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='size',
            field=models.BigIntegerField(default=0),
            preserve_default=False,
        ),
    ]
