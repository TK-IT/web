# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("idm", "0007_manage_all")]

    operations = [
        migrations.DeleteModel(name="Adresser"),
        migrations.DeleteModel(name="Andenbruger"),
        migrations.DeleteModel(name="Arrangementer"),
        migrations.DeleteModel(name="Best"),
        migrations.DeleteModel(name="Bestyrelsen"),
        migrations.DeleteModel(name="Bestyrelsenold"),
        migrations.DeleteModel(name="Bruger"),
        migrations.DeleteModel(name="Grupperold"),
        migrations.DeleteModel(name="Grupperv2Old"),
        migrations.DeleteModel(name="J50Adr"),
        migrations.DeleteModel(name="J50AdrOld"),
        migrations.DeleteModel(name="J50Arr"),
        migrations.DeleteModel(name="Lokaldata"),
        migrations.DeleteModel(name="Mylog"),
        migrations.DeleteModel(name="Nyheder"),
        migrations.DeleteModel(name="Tkfolkbackup"),
        migrations.DeleteModel(name="Tkfolkfix"),
        migrations.DeleteModel(name="TkfolkOld"),
    ]
