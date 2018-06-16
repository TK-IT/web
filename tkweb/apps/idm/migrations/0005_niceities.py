from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0004_copy_data'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='group',
            options={'ordering': ['navn']},
        ),
        migrations.AlterField(
            model_name='group',
            name='type',
            field=models.IntegerField(choices=[(0, 'Underforening'), (1, '\xc5rgangsgruppe'), (2, 'Titel'), (3, 'DirectUser'), (4, 'BESTFU hack')]),
        ),
        migrations.AlterField(
            model_name='profile',
            name='groups',
            field=models.ManyToManyField(to='idm.Group', blank=True),
        ),
        migrations.AlterModelOptions(
            name='profile',
            options={'ordering': ['navn']},
        ),
    ]
