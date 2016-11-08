# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Alias',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('period', models.IntegerField(blank=True, null=True, verbose_name='Årgang')),
                ('root', models.CharField(max_length=10, verbose_name='Titel')),
                ('start_time', models.DateTimeField(blank=True, null=True)),
                ('end_time', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'aliaser',
                'verbose_name': 'alias',
                'ordering': ['period', 'root'],
            },
        ),
        migrations.CreateModel(
            name='Email',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('subject', models.TextField()),
                ('body', models.TextField()),
                ('recipient_name', models.CharField(max_length=255)),
                ('recipient_email', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='EmailBatch',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('send_time', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='EmailTemplate',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('name', models.CharField(blank=True, max_length=255)),
                ('subject', models.TextField()),
                ('body', models.TextField()),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('format', models.CharField(choices=[('pound', 'pound')], max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('time', models.DateTimeField()),
                ('amount', models.DecimalField(decimal_places=2, max_digits=9)),
                ('note', models.CharField(blank=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('name', models.CharField(max_length=50, verbose_name='Navn')),
                ('email', models.EmailField(blank=True, max_length=50, verbose_name='Emailadresse')),
            ],
            options={
                'verbose_name_plural': 'personer',
                'verbose_name': 'person',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Purchase',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('count', models.DecimalField(help_text='antal krydser eller brøkdel', decimal_places=4, max_digits=9)),
            ],
            options={
                'verbose_name_plural': 'krydser',
                'verbose_name': 'krydser',
                'ordering': ['row', 'kind'],
            },
        ),
        migrations.CreateModel(
            name='PurchaseKind',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('position', models.PositiveIntegerField()),
                ('name', models.CharField(help_text='f.eks. guldøl, guldølskasser', max_length=200)),
                ('price', models.DecimalField(help_text='f.eks. 8, 10, 13, 200, 250', decimal_places=2, max_digits=12)),
            ],
            options={
                'verbose_name_plural': 'prisklasser',
                'verbose_name': 'prisklasse',
                'ordering': ['sheet', 'position'],
            },
        ),
        migrations.CreateModel(
            name='Sheet',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('name', models.CharField(help_text='f.eks. HSTR, revy, matlabotanisk have', max_length=200, blank=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
            ],
            options={
                'verbose_name_plural': 'krydslister',
                'verbose_name': 'krydsliste',
                'ordering': ['start_date'],
            },
        ),
        migrations.CreateModel(
            name='SheetRow',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('position', models.PositiveIntegerField()),
                ('name', models.CharField(null=True, max_length=200)),
                ('profile', models.ForeignKey(null=True, to='regnskab.Profile')),
                ('sheet', models.ForeignKey(to='regnskab.Sheet')),
            ],
            options={
                'verbose_name_plural': 'krydslisteindgange',
                'verbose_name': 'krydslisteindgang',
                'ordering': ['sheet', 'position'],
            },
        ),
        migrations.CreateModel(
            name='SheetStatus',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('start_time', models.DateTimeField(blank=True, null=True)),
                ('end_time', models.DateTimeField(blank=True, null=True)),
                ('profile', models.ForeignKey(to='regnskab.Profile')),
            ],
        ),
        migrations.CreateModel(
            name='Title',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('period', models.IntegerField(verbose_name='Årgang')),
                ('root', models.CharField(max_length=10, verbose_name='Titel')),
                ('kind', models.CharField(choices=[('BEST', 'BEST'), ('FU', 'FU'), ('EFU', 'EFU')], max_length=10, verbose_name='Slags')),
                ('profile', models.ForeignKey(to='regnskab.Profile')),
            ],
            options={
                'verbose_name_plural': 'titler',
                'verbose_name': 'titel',
                'ordering': ['-period', 'kind', 'root'],
            },
        ),
        migrations.AddField(
            model_name='purchasekind',
            name='sheet',
            field=models.ForeignKey(to='regnskab.Sheet'),
        ),
        migrations.AddField(
            model_name='purchase',
            name='kind',
            field=models.ForeignKey(to='regnskab.PurchaseKind'),
        ),
        migrations.AddField(
            model_name='purchase',
            name='row',
            field=models.ForeignKey(to='regnskab.SheetRow'),
        ),
        migrations.AddField(
            model_name='payment',
            name='profile',
            field=models.ForeignKey(to='regnskab.Profile'),
        ),
        migrations.AddField(
            model_name='emailbatch',
            name='template',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, null=True, to='regnskab.EmailTemplate'),
        ),
        migrations.AddField(
            model_name='email',
            name='batch',
            field=models.ForeignKey(to='regnskab.EmailBatch'),
        ),
        migrations.AddField(
            model_name='email',
            name='profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, null=True, to='regnskab.Profile', related_name='+'),
        ),
        migrations.AddField(
            model_name='alias',
            name='profile',
            field=models.ForeignKey(to='regnskab.Profile'),
        ),
    ]
