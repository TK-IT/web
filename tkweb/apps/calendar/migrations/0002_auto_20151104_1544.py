from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('calendar', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='event',
            options={'ordering': ['date']},
        ),
    ]
