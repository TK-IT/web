# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.db.models.deletion


profile_model = settings.TKWEB_IDM_MODULE.split('.')[-1] + '.Profile'


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(profile_model),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('regnskab', '0008_unit_price'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('kind', models.CharField(max_length=10, choices=[('payment', 'Betaling'), ('purchase', 'Diverse køb'), ('correction', 'Korrigering')])),
                ('time', models.DateTimeField()),
                ('amount', models.DecimalField(max_digits=9, decimal_places=2)),
                ('note', models.CharField(blank=True, max_length=255)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('profile', models.ForeignKey(to=profile_model)),
                ('session', models.ForeignKey(null=True, to='regnskab.Session')),
            ],
        ),
    ]
