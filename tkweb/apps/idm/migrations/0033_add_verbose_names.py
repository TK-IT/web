# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0032_remove_profile_gone_janej'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='group',
            options={'verbose_name': 'gruppe', 'ordering': ['name'], 'verbose_name_plural': 'grupper'},
        ),
        migrations.AlterModelOptions(
            name='profile',
            options={'verbose_name': 'person', 'ordering': ['name'], 'verbose_name_plural': 'personer'},
        ),
        migrations.AlterModelOptions(
            name='title',
            options={'verbose_name': 'titel', 'ordering': ['-period', 'kind', 'root'], 'verbose_name_plural': 'titler'},
        ),
        migrations.AlterField(
            model_name='group',
            name='matchtest',
            field=models.TextField(verbose_name='Eksempler'),
        ),
        migrations.AlterField(
            model_name='group',
            name='name',
            field=models.CharField(max_length=25, verbose_name='Navn', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='group',
            name='regexp',
            field=models.CharField(max_length=50, verbose_name='Regulært udtryk'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='allow_direct_email',
            field=models.BooleanField(verbose_name='Tillad emails til titel'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='country',
            field=models.CharField(max_length=50, verbose_name='Land', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='email',
            field=models.CharField(max_length=50, verbose_name='Emailadresse', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='gone',
            field=models.BooleanField(verbose_name='Afdød'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='groups',
            field=models.ManyToManyField(to='idm.Group', verbose_name='Grupper', blank=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='house_number',
            field=models.CharField(max_length=15, verbose_name='Husnr.', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='name',
            field=models.CharField(max_length=50, verbose_name='Navn', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='note',
            field=models.TextField(verbose_name='Note', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='phone_number',
            field=models.CharField(max_length=20, verbose_name='Telefonnr.', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='postal_code',
            field=models.CharField(max_length=10, verbose_name='Postnr.', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='street_name',
            field=models.CharField(max_length=50, verbose_name='Gade', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='town',
            field=models.CharField(max_length=25, verbose_name='By', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='title',
            name='kind',
            field=models.CharField(max_length=10, verbose_name='Slags', choices=[('BEST', 'BEST'), ('FU', 'FU'), ('EFU', 'EFU')]),
        ),
        migrations.AlterField(
            model_name='title',
            name='period',
            field=models.IntegerField(verbose_name='Årgang'),
        ),
        migrations.AlterField(
            model_name='title',
            name='root',
            field=models.CharField(max_length=10, verbose_name='Titel'),
        ),
    ]
