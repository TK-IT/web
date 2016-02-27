from __future__ import unicode_literals

from django.db import models


class Profile(models.Model):
    navn = models.CharField(max_length=50, blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True)
    accepteremail = models.CharField(max_length=3, blank=True, null=True)
    accepterdirektemail = models.CharField(max_length=3)
    gade = models.CharField(max_length=50, blank=True, null=True)
    husnr = models.CharField(max_length=15, blank=True, null=True)
    postnr = models.CharField(max_length=10, blank=True, null=True)
    postby = models.CharField(max_length=25, blank=True, null=True)
    land = models.CharField(max_length=50, blank=True, null=True)
    gone = models.CharField(max_length=3)
    tlf = models.CharField(max_length=20, blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tkfolk'


class Best(models.Model):
    sortid = models.IntegerField(primary_key=True)
    orgtitel = models.CharField(max_length=50)
    titel = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'best'


class Group(models.Model):
    navn = models.CharField(max_length=25, blank=True, null=True)
    regexp = models.CharField(max_length=50)
    matchtest = models.TextField()
    relativ = models.IntegerField()
    type = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'grupper'


class Adresser(models.Model):
    id = models.IntegerField(primary_key=True)
    gade = models.CharField(max_length=50)
    husnr = models.CharField(max_length=15)
    postnr = models.CharField(max_length=10)
    postby = models.CharField(max_length=25)
    land = models.CharField(max_length=25)
    tlf = models.CharField(max_length=15)
    gone = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'adresser'


class Andenbruger(models.Model):
    login = models.CharField(max_length=32, blank=True, null=True)
    password = models.CharField(max_length=32, blank=True, null=True)
    type = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'andenbruger'


class Arrangementer(models.Model):
    titel = models.CharField(max_length=50, blank=True, null=True)
    dag = models.IntegerField(blank=True, null=True)
    maned = models.IntegerField(blank=True, null=True)
    ar = models.IntegerField(blank=True, null=True)
    beskrivelse = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'arrangementer'


class Bestyrelsen(models.Model):
    titel = models.CharField(max_length=5, blank=True, null=True)
    navn = models.CharField(max_length=50, blank=True, null=True)
    adresse1 = models.CharField(max_length=50, blank=True, null=True)
    adresse2 = models.CharField(max_length=50, blank=True, null=True)
    postnr = models.IntegerField(blank=True, null=True)
    postby = models.CharField(max_length=25, blank=True, null=True)
    dag = models.IntegerField(blank=True, null=True)
    maned = models.IntegerField(blank=True, null=True)
    ar = models.IntegerField(blank=True, null=True)
    stdtlf = models.IntegerField(blank=True, null=True)
    mbltlf = models.IntegerField(blank=True, null=True)
    arskort = models.IntegerField(blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True)
    hjemmeside = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bestyrelsen'


class Bestyrelsenold(models.Model):
    titel = models.CharField(max_length=5, blank=True, null=True)
    navn = models.CharField(max_length=50, blank=True, null=True)
    adresse1 = models.CharField(max_length=50, blank=True, null=True)
    adresse2 = models.CharField(max_length=50, blank=True, null=True)
    postnr = models.IntegerField(blank=True, null=True)
    postby = models.CharField(max_length=25, blank=True, null=True)
    dag = models.IntegerField(blank=True, null=True)
    maned = models.IntegerField(blank=True, null=True)
    ar = models.IntegerField(blank=True, null=True)
    stdtlf = models.IntegerField(blank=True, null=True)
    mbltlf = models.IntegerField(blank=True, null=True)
    arskort = models.IntegerField(blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True)
    hjemmeside = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bestyrelsenOLD'


class Bruger(models.Model):
    login = models.CharField(max_length=32, blank=True, null=True)
    password = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bruger'


class Gradgruppemedlemmer(models.Model):
    personid = models.IntegerField(blank=True, null=True)
    grad = models.IntegerField(blank=True, null=True)
    gruppeid = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'gradgruppemedlemmer'


class Gruppemedlemmer(models.Model):
    gruppeid = models.IntegerField(blank=True, null=True)
    personid = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'gruppemedlemmer'


class Grupperold(models.Model):
    navn = models.CharField(max_length=25, blank=True, null=True)
    regexp = models.CharField(max_length=50)
    matchtest = models.TextField()
    relativ = models.IntegerField()
    type = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'grupperOLD'


class Grupperv2Old(models.Model):
    navn = models.CharField(max_length=25, blank=True, null=True)
    regexp = models.CharField(max_length=50)
    matchtest = models.TextField()
    relativ = models.IntegerField()
    type = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'grupperV2OLD'


class J50Adr(models.Model):
    periode = models.CharField(max_length=5, blank=True, null=True)
    orgtitel = models.CharField(max_length=5, blank=True, null=True)
    vistnok = models.IntegerField(blank=True, null=True)
    navn = models.CharField(max_length=50, blank=True, null=True)
    gade = models.CharField(max_length=50, blank=True, null=True)
    husnr = models.CharField(max_length=15, blank=True, null=True)
    postnr = models.CharField(max_length=10, blank=True, null=True)
    postby = models.CharField(max_length=25, blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True)
    bekraft = models.IntegerField(blank=True, null=True)
    periode2 = models.CharField(max_length=5, blank=True, null=True)
    orgtitel2 = models.CharField(max_length=5, blank=True, null=True)
    gone = models.IntegerField(blank=True, null=True)
    vistnok2 = models.CharField(max_length=5, blank=True, null=True)
    tlf = models.CharField(max_length=15, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    tilmeld = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'j50adr'


class J50AdrOld(models.Model):
    periode = models.CharField(max_length=5, blank=True, null=True)
    orgtitel = models.CharField(max_length=5, blank=True, null=True)
    vistnok = models.IntegerField(blank=True, null=True)
    navn = models.CharField(max_length=50, blank=True, null=True)
    gade = models.CharField(max_length=50, blank=True, null=True)
    husnr = models.CharField(max_length=15, blank=True, null=True)
    postnr = models.CharField(max_length=10, blank=True, null=True)
    postby = models.CharField(max_length=25, blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True)
    bekraft = models.IntegerField(blank=True, null=True)
    periode2 = models.CharField(max_length=5, blank=True, null=True)
    orgtitel2 = models.CharField(max_length=5, blank=True, null=True)
    gone = models.IntegerField(blank=True, null=True)
    vistnok2 = models.CharField(max_length=5, blank=True, null=True)
    tlf = models.CharField(max_length=15, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    tilmeld = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'j50adr-OLD'


class J50Arr(models.Model):
    titel = models.CharField(max_length=25, blank=True, null=True)
    dag = models.IntegerField(blank=True, null=True)
    fra = models.IntegerField(blank=True, null=True)
    til = models.IntegerField(blank=True, null=True)
    skema = models.IntegerField(blank=True, null=True)
    arrangement = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'j50arr'


class Lokaldata(models.Model):
    navn = models.CharField(unique=True, max_length=10)
    data = models.TextField()

    class Meta:
        managed = False
        db_table = 'lokalData'


class Mylog(models.Model):
    sec = models.IntegerField(blank=True, null=True)
    min = models.IntegerField(blank=True, null=True)
    hour = models.IntegerField(blank=True, null=True)
    day = models.IntegerField(blank=True, null=True)
    month = models.IntegerField(blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    action = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'mylog'


class Nyheder(models.Model):
    dag = models.IntegerField(blank=True, null=True)
    maned = models.IntegerField(blank=True, null=True)
    ar = models.IntegerField(blank=True, null=True)
    beskrivelse = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'nyheder'


class Titler(models.Model):
    personid = models.IntegerField(blank=True, null=True)
    grad = models.IntegerField(blank=True, null=True)
    orgtitel = models.CharField(max_length=10, blank=True, null=True)
    inttitel = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'titler'


class TkfolkOld(models.Model):
    navn = models.CharField(max_length=50, blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True)
    accepteremail = models.CharField(max_length=3, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tkfolk-OLD'


class Tkfolkbackup(models.Model):
    navn = models.CharField(max_length=50, blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True)
    accepteremail = models.CharField(max_length=3, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tkfolkBACKUP'


class Tkfolkfix(models.Model):
    navn = models.CharField(max_length=50, blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True)
    accepteremail = models.CharField(max_length=3, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tkfolkFix'
