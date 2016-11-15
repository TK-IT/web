# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from regnskab.models import Profile


profile_app = Profile._meta.app_label
profile_path = profile_app + '.' + Profile.__name__


class Migration(migrations.Migration):

    dependencies = [
        (profile_app, '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Alias',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period', models.IntegerField(blank=True, null=True, verbose_name='Årgang')),
                ('root', models.CharField(max_length=10, verbose_name='Titel')),
                ('start_time', models.DateTimeField(blank=True, null=True)),
                ('end_time', models.DateTimeField(blank=True, null=True)),
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
            ],
        ),
        migrations.CreateModel(
            name='EmailBatch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('send_time', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='EmailTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, blank=True)),
                ('subject', models.TextField()),
                ('body', models.TextField()),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('format', models.CharField(max_length=10, choices=[('pound', 'pound')])),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.DateTimeField()),
                ('amount', models.DecimalField(max_digits=9, decimal_places=2)),
                ('note', models.CharField(max_length=255, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Purchase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count', models.DecimalField(help_text='antal krydser eller brøkdel', max_digits=9, decimal_places=4)),
            ],
            options={
                'ordering': ['row', 'kind'],
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
                ('price', models.DecimalField(help_text='f.eks. 8, 10, 13, 200, 250', max_digits=12, decimal_places=2)),
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
                ('profile', models.ForeignKey(null=True, to=profile_path)),
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
                ('profile', models.ForeignKey(to=profile_path)),
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
            model_name='payment',
            name='profile',
            field=models.ForeignKey(to=profile_path),
        ),
        migrations.AddField(
            model_name='emailbatch',
            name='payment_set',
            field=models.ManyToManyField(blank=True, to='regnskab.Payment', verbose_name='betalinger'),
        ),
        migrations.AddField(
            model_name='emailbatch',
            name='sheet_set',
            field=models.ManyToManyField(blank=True, to='regnskab.Sheet', verbose_name='krydslister'),
        ),
        migrations.AddField(
            model_name='emailbatch',
            name='template',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='regnskab.EmailTemplate'),
        ),
        migrations.AddField(
            model_name='email',
            name='batch',
            field=models.ForeignKey(to='regnskab.EmailBatch'),
        ),
        migrations.AddField(
            model_name='email',
            name='profile',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=profile_path, related_name='+'),
        ),
        migrations.AddField(
            model_name='alias',
            name='profile',
            field=models.ForeignKey(to=profile_path),
        ),
    ]
