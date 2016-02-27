# encoding: utf8
from __future__ import unicode_literals

from django.db import models
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible


def tk_prefix(age):
    def sup(n):
        digits = '⁰¹²³⁴⁵⁶⁷⁸⁹'
        return ''.join(digits[int(i)] for i in str(n))

    prefix = ['K', '', 'G', 'B', 'O', 'TO']
    if age < -1:
        return 'K%s' % sup(-age)
    elif age + 1 < len(prefix):
        return prefix[age + 1]
    else:
        return 'T%sO' % sup(age - 3)


@python_2_unicode_compatible
class Group(models.Model):
    TYPES = (
        (0, 'Underforening'),
        (1, 'Årgangsgruppe'),
        (2, 'Titel'),
        (3, 'DirectUser'),
        (4, 'BESTFU hack'),
    )

    navn = models.CharField(max_length=25, blank=True, null=True)
    regexp = models.CharField(max_length=50)
    matchtest = models.TextField()
    relativ = models.IntegerField()
    type = models.IntegerField(choices=TYPES)

    class Meta:
        db_table = 'grupper'
        ordering = ['navn']

    def __str__(self):
        return self.navn


@python_2_unicode_compatible
class Profile(models.Model):
    JANEJ = (
        ('ja', 'ja'),
        ('nej', 'nej'),
    )

    navn = models.CharField(max_length=50, blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True)
    accepteremail = models.CharField(max_length=3, blank=True, null=True,
                                     choices=JANEJ)
    accepterdirektemail = models.CharField(max_length=3, choices=JANEJ)
    gade = models.CharField(max_length=50, blank=True, null=True)
    husnr = models.CharField(max_length=15, blank=True, null=True)
    postnr = models.CharField(max_length=10, blank=True, null=True)
    postby = models.CharField(max_length=25, blank=True, null=True)
    land = models.CharField(max_length=50, blank=True, null=True)
    gone = models.CharField(max_length=3, choices=JANEJ)
    tlf = models.CharField(max_length=20, blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    groups = models.ManyToManyField(Group, blank=True,
                                    limit_choices_to=Q(type=0))

    class Meta:
        db_table = 'tkfolk'
        ordering = ['navn']

    def __str__(self):
        return self.navn


@python_2_unicode_compatible
class GradGroupMembership(models.Model):
    profile = models.ForeignKey(Profile)
    group = models.ForeignKey(Group, limit_choices_to=Q(type=1))
    grad = models.IntegerField()

    def __str__(self):
        return '%s%s %s' % (tk_prefix(self.grad), self.group, self.profile)


@python_2_unicode_compatible
class Best(models.Model):
    sortid = models.IntegerField(primary_key=True)
    orgtitel = models.CharField(max_length=50)
    titel = models.CharField(max_length=10)

    class Meta:
        db_table = 'best'

    def __str__(self):
        return self.titel


@python_2_unicode_compatible
class Title(models.Model):
    profile = models.ForeignKey('Profile')
    grad = models.IntegerField()
    orgtitel = models.CharField(max_length=10)
    inttitel = models.CharField(max_length=10)

    def display_title(self):
        return '%s%s' % (tk_prefix(self.grad), self.orgtitel)

    def __str__(self):
        return '%s %s' % (self.display_title(), self.profile)


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
