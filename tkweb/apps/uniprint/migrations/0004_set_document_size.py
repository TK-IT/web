# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def set_document_size(apps, schema_editor):
    Document = apps.get_model('uniprint', 'Document')
    qs = Document.objects.filter(size=0)
    for d in qs:
        d.size = len(d.file)
        assert d.size != 0
        d.save()


class Migration(migrations.Migration):

    dependencies = [
        ('uniprint', '0003_document_size'),
    ]

    operations = [
        migrations.RunPython(set_document_size),
    ]
