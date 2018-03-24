# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('idm', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Alias',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period', models.IntegerField(help_text='Bruges kun hvis aliaset skal opdateres automatisk efter hver GF', blank=True, null=True, verbose_name='Årgang')),
                ('root', models.CharField(max_length=200, verbose_name='Alias')),
                ('start_time', models.DateTimeField(blank=True, null=True)),
                ('end_time', models.DateTimeField(blank=True, null=True)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, on_delete=django.db.models.deletion.SET_NULL)),
                ('profile', models.ForeignKey(to='idm.Profile')),
            ],
            options={
                'ordering': ['period', 'root'],
                'verbose_name_plural': 'aliaser',
                'verbose_name': 'alias',
            },
        ),
        migrations.CreateModel(
            name='Email',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.TextField()),
                ('body', models.TextField()),
                ('recipient_name', models.CharField(max_length=255)),
                ('recipient_email', models.CharField(max_length=255)),
                ('profile', models.ForeignKey(to='idm.Profile', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+')),
            ],
        ),
        migrations.CreateModel(
            name='EmailTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, blank=True)),
                ('subject', models.TextField()),
                ('body', models.TextField()),
                ('format', models.CharField(max_length=10, choices=[('pound', 'pound')])),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, on_delete=django.db.models.deletion.SET_NULL)),
            ],
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period', models.IntegerField(verbose_name='Årgang')),
                ('send_time', models.DateTimeField(null=True, blank=True)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, on_delete=django.db.models.deletion.SET_NULL)),
                ('email_template', models.ForeignKey(verbose_name='Emailskabelon', to='regnskab.EmailTemplate', null=True, on_delete=django.db.models.deletion.SET_NULL)),
            ],
            options={
                'get_latest_by': 'created_time',
            },
        ),
        migrations.CreateModel(
            name='Purchase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count', models.DecimalField(help_text='antal krydser eller brøkdel', max_digits=9, decimal_places=4)),
            ],
            options={
                'ordering': ['row', 'kind__position'],
                'verbose_name_plural': 'krydser',
                'verbose_name': 'krydser',
            },
        ),
        migrations.CreateModel(
            name='PurchaseKind',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.PositiveIntegerField()),
                ('name', models.CharField(help_text='f.eks. guldøl, guldølskasser', max_length=200)),
                ('unit_price', models.DecimalField(help_text='f.eks. 8, 10, 13, 200, 250', max_digits=12, decimal_places=2)),
            ],
            options={
                'ordering': ['sheet', 'position'],
                'verbose_name_plural': 'prisklasser',
                'verbose_name': 'prisklasse',
            },
        ),
        migrations.CreateModel(
            name='Sheet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='f.eks. HSTR, revy, matlabotanisk have', blank=True, max_length=200)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('period', models.IntegerField(verbose_name='Årgang')),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, on_delete=django.db.models.deletion.SET_NULL)),
                ('session', models.ForeignKey(null=True, to='regnskab.Session')),
            ],
            options={
                'ordering': ['start_date'],
                'verbose_name_plural': 'krydslister',
                'verbose_name': 'krydsliste',
            },
        ),
        migrations.CreateModel(
            name='SheetRow',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.PositiveIntegerField()),
                ('name', models.CharField(max_length=200, null=True)),
                ('profile', models.ForeignKey(null=True, to='idm.Profile')),
                ('sheet', models.ForeignKey(to='regnskab.Sheet')),
            ],
            options={
                'ordering': ['sheet', 'position'],
                'verbose_name_plural': 'krydslisteindgange',
                'verbose_name': 'krydslisteindgang',
            },
        ),
        migrations.CreateModel(
            name='SheetStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField(blank=True, null=True)),
                ('end_time', models.DateTimeField(blank=True, null=True)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, on_delete=django.db.models.deletion.SET_NULL)),
                ('profile', models.ForeignKey(to='idm.Profile')),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('kind', models.CharField(choices=[('payment', 'Betaling'), ('purchase', 'Diverse køb'), ('correction', 'Korrigering')], max_length=10)),
                ('time', models.DateTimeField()),
                ('amount', models.DecimalField(max_digits=9, decimal_places=2)),
                ('note', models.CharField(blank=True, max_length=255)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, on_delete=django.db.models.deletion.SET_NULL)),
                ('profile', models.ForeignKey(to='idm.Profile')),
                ('session', models.ForeignKey(null=True, to='regnskab.Session')),
            ],
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
            model_name='email',
            name='session',
            field=models.ForeignKey(to='regnskab.Session'),
        ),
    ]
