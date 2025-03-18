from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0005_add_verbose_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='basemedia',
            name='isCoverFile',
            field=models.BooleanField(null=True, verbose_name='Vis på forsiden'),
        ),
    ]
