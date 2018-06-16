from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('regnskab', '0014_populate_transaction_period'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailtemplate',
            name='markup',
            field=models.CharField(max_length=10, default='plain', choices=[('plain', 'Ren tekst'), ('html', 'HTML')]),
            preserve_default=False,
        ),
    ]
