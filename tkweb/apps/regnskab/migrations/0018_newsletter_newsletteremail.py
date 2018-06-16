from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('regnskab', '0017_explicit_email_set'),
    ]

    operations = [
        migrations.CreateModel(
            name='Newsletter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('period', models.IntegerField(verbose_name='Årgang')),
                ('send_time', models.DateTimeField(blank=True, null=True)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('email_template', models.ForeignKey(verbose_name='Emailskabelon', null=True, on_delete=django.db.models.deletion.SET_NULL, to='regnskab.EmailTemplate')),
            ],
            options={
                'get_latest_by': 'created_time',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='NewsletterEmail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('subject', models.TextField()),
                ('body_plain', models.TextField()),
                ('body_html', models.TextField(blank=True, null=True)),
                ('recipient_name', models.CharField(max_length=255)),
                ('recipient_email', models.CharField(max_length=255)),
                ('newsletter', models.ForeignKey(related_name='email_set', to='regnskab.Newsletter')),
                ('profile', models.ForeignKey(null=True, related_name='+', on_delete=django.db.models.deletion.SET_NULL, to='idm.Profile')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
