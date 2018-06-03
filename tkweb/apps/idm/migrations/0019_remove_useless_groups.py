# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def remove_useless_groups(apps, schema_editor):
    Group = apps.get_model("idm", "Group")
    Group.objects.exclude(type=0).delete()


class Migration(migrations.Migration):

    dependencies = [("idm", "0018_rename_orgtitel_root")]

    operations = [
        migrations.RunPython(remove_useless_groups, lambda apps, schema_editor: None)
    ]
