# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("idm", "0017_remove_title_grad")]

    operations = [
        migrations.RenameField(model_name="title", old_name="orgtitel", new_name="root")
    ]
