from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('regnskab', '0009_populate_purchasekind_sheets'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='purchasekind',
            options={'verbose_name_plural': 'prisklasser', 'verbose_name': 'prisklasse', 'ordering': ['position']},
        ),
        migrations.AlterField(
            model_name='purchasekind',
            name='sheet',
            field=models.ForeignKey(related_name='+', to='regnskab.Sheet'),
        ),
        migrations.AlterField(
            model_name='purchasekind',
            name='sheets',
            field=models.ManyToManyField(to='regnskab.Sheet'),
        ),
    ]
