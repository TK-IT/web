from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0005_niceities'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Gradgruppemedlemmer',
        ),
        migrations.DeleteModel(
            name='Gruppemedlemmer',
        ),
        migrations.DeleteModel(
            name='Titler',
        ),
    ]
