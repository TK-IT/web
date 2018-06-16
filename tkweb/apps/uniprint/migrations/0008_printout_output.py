from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uniprint', '0007_remove_printout_duplex'),
    ]

    operations = [
        migrations.AddField(
            model_name='printout',
            name='output',
            field=models.TextField(blank=True, null=True),
        ),
    ]
