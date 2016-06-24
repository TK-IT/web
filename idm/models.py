# encoding: utf8
from __future__ import unicode_literals

from django.db import models
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible
from constance import config


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
    REGEXP_MAILING_LIST = 'no$public$address'

    name = models.CharField(max_length=25, blank=True, null=True)
    regexp = models.CharField(max_length=50)
    matchtest = models.TextField()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Profile(models.Model):
    JANEJ = (
        ('ja', 'ja'),
        ('nej', 'nej'),
    )

    name = models.CharField(max_length=50, blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True)
    allow_direct_email = models.BooleanField(blank=True)
    street_name = models.CharField(max_length=50, blank=True, null=True)
    house_number = models.CharField(max_length=15, blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, null=True)
    town = models.CharField(max_length=25, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    gone = models.CharField(max_length=3, choices=JANEJ)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    groups = models.ManyToManyField(Group, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Title(models.Model):
    BEST, FU, EFU = 'BEST', 'FU', 'EFU'
    KIND = [(BEST, 'BEST'), (FU, 'FU'), (EFU, 'EFU')]

    profile = models.ForeignKey('Profile')
    period = models.IntegerField()
    root = models.CharField(max_length=10)
    kind = models.CharField(max_length=10, choices=KIND)

    @property
    def age(self):
        return config.GFYEAR - self.period

    def display_title(self):
        return '%s%s' % (tk_prefix(self.age), self.root)

    class Meta:
        ordering = ['-period', 'kind', 'root']

    def __str__(self):
        return '%s %s' % (self.display_title(), self.profile)
