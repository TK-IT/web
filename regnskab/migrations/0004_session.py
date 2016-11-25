# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('regnskab', '0003_root_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('send_time', models.DateTimeField(blank=True, null=True)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
                ('email_template', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='regnskab.EmailTemplate', null=True)),
                ('payment_set', models.ManyToManyField(verbose_name='betalinger', to='regnskab.Payment', blank=True)),
                ('sheet_set', models.ManyToManyField(verbose_name='krydslister', to='regnskab.Sheet', blank=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='emailbatch',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='emailbatch',
            name='payment_set',
        ),
        migrations.RemoveField(
            model_name='emailbatch',
            name='sheet_set',
        ),
        migrations.RemoveField(
            model_name='emailbatch',
            name='template',
        ),
        migrations.AlterField(
            model_name='email',
            name='batch',
            field=models.ForeignKey(to='regnskab.Session'),
        ),
        migrations.DeleteModel(
            name='EmailBatch',
        ),
    ]
