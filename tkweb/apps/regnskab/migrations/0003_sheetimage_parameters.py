# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [("regnskab", "0002_sheetimage")]

    operations = [
        migrations.AddField(
            model_name="sheetimage",
            name="parameters",
            field=jsonfield.fields.JSONField(default={}),
        )
    ]
