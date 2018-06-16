from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('regnskab', '0015_emailtemplate_markup'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailTemplateInline',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('mime_type', models.CharField(max_length=255)),
                ('blob', models.BinaryField()),
                ('hash', models.CharField(max_length=255)),
            ],
        ),
        migrations.RenameField(
            model_name='email',
            old_name='body',
            new_name='body_plain',
        ),
        migrations.AddField(
            model_name='email',
            name='body_html',
            field=models.TextField(blank=True, null=True),
        ),
    ]
