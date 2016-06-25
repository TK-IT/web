# encoding: utf8
from __future__ import unicode_literals

from django.db import models
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible
from constance import config


def unicode_superscript(n):
    digits = '⁰¹²³⁴⁵⁶⁷⁸⁹'
    return ''.join(digits[int(i)] for i in str(n))


def tk_prefix(age, sup_fn=None):
    if sup_fn is None:
        sup_fn = unicode_superscript
    prefix = ['K', '', 'G', 'B', 'O', 'TO']
    if age < -1:
        return 'K%s' % sup_fn(-age)
    elif age + 1 < len(prefix):
        return prefix[age + 1]
    else:
        return 'T%sO' % sup_fn(age - 3)


@python_2_unicode_compatible
class Group(models.Model):
    REGEXP_MAILING_LIST = 'no$public$address'

    name = models.CharField(max_length=25, blank=True, null=True,
                            verbose_name="Navn")
    regexp = models.CharField(max_length=50, verbose_name="Regulært udtryk")
    matchtest = models.TextField(verbose_name="Eksempler")

    class Meta:
        ordering = ['name']
        verbose_name = 'gruppe'
        verbose_name_plural = verbose_name + 'r'

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Profile(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True,
                            verbose_name="Navn")
    email = models.CharField(max_length=50, blank=True, null=True,
                             verbose_name="Emailadresse")
    allow_direct_email = models.BooleanField(
        blank=True, verbose_name="Tillad emails til titel")
    street_name = models.CharField(max_length=50, blank=True, null=True,
                                   verbose_name="Gade")
    house_number = models.CharField(max_length=15, blank=True, null=True,
                                    verbose_name="Husnr.")
    postal_code = models.CharField(max_length=10, blank=True, null=True,
                                   verbose_name="Postnr.")
    town = models.CharField(max_length=25, blank=True, null=True,
                            verbose_name="By")
    country = models.CharField(max_length=50, blank=True, null=True,
                               verbose_name="Land")
    gone = models.BooleanField(blank=True, verbose_name="Afdød")
    phone_number = models.CharField(max_length=20, blank=True, null=True,
                                    verbose_name="Telefonnr.")
    note = models.TextField(blank=True, null=True, verbose_name="Note")

    groups = models.ManyToManyField(Group, blank=True, verbose_name="Grupper")

    class Meta:
        ordering = ['name']
        verbose_name = 'person'
        verbose_name_plural = verbose_name + 'er'

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Title(models.Model):
    BEST, FU, EFU = 'BEST', 'FU', 'EFU'
    KIND = [(BEST, 'BEST'), (FU, 'FU'), (EFU, 'EFU')]

    profile = models.ForeignKey('Profile')
    period = models.IntegerField(verbose_name='Årgang')
    root = models.CharField(max_length=10, verbose_name='Titel')
    kind = models.CharField(max_length=10, choices=KIND, verbose_name='Slags')

    @property
    def age(self):
        return config.GFYEAR - self.period

    def display_title(self):
        return '%s%s' % (tk_prefix(self.age), self.root)

    class Meta:
        ordering = ['-period', 'kind', 'root']
        verbose_name = 'titel'
        verbose_name_plural = 'titler'

    def __str__(self):
        return '%s %s' % (self.display_title(), self.profile)
