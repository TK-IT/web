from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('regnskab', '0012_remove_purchasekind_sheet'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='period',
            field=models.IntegerField(verbose_name='Årgang', default=0),
            preserve_default=False,
        ),
    ]
