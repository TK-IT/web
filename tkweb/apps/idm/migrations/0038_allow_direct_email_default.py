from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0037_fields_non_null_and_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='allow_direct_email',
            field=models.BooleanField(default=True, verbose_name='Tillad emails til titel'),
        ),
    ]
