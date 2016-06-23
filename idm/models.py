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
class Title(models.Model):
    BEST, FU, EFU = 'BEST', 'FU', 'EFU'
    KIND = [(BEST, 'BEST'), (FU, 'FU'), (EFU, 'EFU')]

    profile = models.ForeignKey('Profile')
    grad = models.IntegerField()
    orgtitel = models.CharField(max_length=10)
    inttitel = models.CharField(max_length=10)
    kind = models.CharField(max_length=10, choices=KIND, blank=True, null=True)

    def display_title(self):
        return '%s%s' % (tk_prefix(self.grad), self.orgtitel)

    def __str__(self):
        return '%s %s' % (self.display_title(), self.profile)
