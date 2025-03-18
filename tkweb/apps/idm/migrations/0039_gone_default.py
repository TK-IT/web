from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0038_allow_direct_email_default'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='gone',
            field=models.BooleanField(verbose_name='Afdød', blank=True, default=False),
        ),
    ]
