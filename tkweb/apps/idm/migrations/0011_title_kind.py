from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0010_remove_funny_titles'),
    ]

    operations = [
        migrations.AddField(
            model_name='title',
            name='kind',
            field=models.CharField(blank=True, null=True, max_length=10, choices=[('BEST', 'BEST'), ('FU', 'FU'), ('EFU', 'EFU')]),
        ),
    ]
