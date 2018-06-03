# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [("idm", "0022_delete_gradgroupmembership")]

    operations = [
        migrations.AlterModelOptions(name="group", options={"ordering": ["name"]}),
        migrations.AlterModelOptions(name="profile", options={"ordering": ["name"]}),
        migrations.AlterModelOptions(
            name="title", options={"ordering": ["-period", "kind", "root"]}
        ),
        migrations.RenameField(model_name="group", old_name="navn", new_name="name"),
        migrations.RenameField(model_name="profile", old_name="navn", new_name="name"),
        migrations.RenameField(
            model_name="profile", old_name="gade", new_name="street_name"
        ),
        migrations.RenameField(
            model_name="profile", old_name="husnr", new_name="house_number"
        ),
        migrations.RenameField(
            model_name="profile", old_name="postnr", new_name="postal_code"
        ),
        migrations.RenameField(
            model_name="profile", old_name="postby", new_name="town"
        ),
        migrations.RenameField(
            model_name="profile", old_name="land", new_name="country"
        ),
        migrations.RenameField(
            model_name="profile", old_name="tlf", new_name="phone_number"
        ),
    ]
