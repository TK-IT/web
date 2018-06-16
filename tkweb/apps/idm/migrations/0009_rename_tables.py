from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0008_delete_unused_tables'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='group',
            table='idm_group',
        ),
        migrations.AlterModelTable(
            name='profile',
            table='idm_profile',
        ),
        migrations.AlterModelTable(
            name='group',
            table=None,
        ),
        migrations.AlterModelTable(
            name='profile',
            table=None,
        ),
    ]
