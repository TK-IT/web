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
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(verbose_name='Navn', max_length=50)),
                ('email', models.EmailField(blank=True, verbose_name='Emailadresse', max_length=50)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name_plural': 'personer',
                'verbose_name': 'person',
            },
        ),
        migrations.CreateModel(
            name='Title',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('period', models.IntegerField(verbose_name='Årgang')),
                ('root', models.CharField(verbose_name='Titel', max_length=10)),
                ('kind', models.CharField(choices=[('BEST', 'BEST'), ('FU', 'FU'), ('EFU', 'EFU')], verbose_name='Slags', max_length=10)),
                ('profile', models.ForeignKey(to='uniprintsite.Profile')),
            ],
            options={
                'ordering': ['-period', 'kind', 'root'],
                'verbose_name_plural': 'titler',
                'verbose_name': 'titel',
            },
        ),
    ]
