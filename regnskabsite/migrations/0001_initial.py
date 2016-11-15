# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(verbose_name='Navn', max_length=50)),
                ('email', models.EmailField(verbose_name='Emailadresse', max_length=50, blank=True)),
            ],
            options={
                'verbose_name': 'person',
                'verbose_name_plural': 'personer',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Title',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('period', models.IntegerField(verbose_name='Årgang')),
                ('root', models.CharField(verbose_name='Titel', max_length=10)),
                ('kind', models.CharField(verbose_name='Slags', max_length=10, choices=[('BEST', 'BEST'), ('FU', 'FU'), ('EFU', 'EFU')])),
                ('profile', models.ForeignKey(to='regnskabsite.Profile')),
            ],
            options={
                'verbose_name': 'titel',
                'verbose_name_plural': 'titler',
                'ordering': ['-period', 'kind', 'root'],
            },
        ),
    ]
