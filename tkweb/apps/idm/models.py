# encoding: utf8
from __future__ import unicode_literals

import re

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from constance import config
import tktitler as tk


def _get_gfyear(gfyear):
    if gfyear is None:
        gfyear = config.GFYEAR
    return gfyear


# Remember to update the migrations that refer to this function
# if it is moved to a different file.
def validate_regex_pattern(value):
    try:
        re.compile(value)
    except re.error as exn:
        raise ValidationError('Invalid regex pattern: %s' % (exn,))


@python_2_unicode_compatible
class Group(models.Model):
    REGEXP_MAILING_LIST = 'no$public$address'

    name = models.CharField(max_length=25, verbose_name="Navn")
    regexp = models.CharField(max_length=50, verbose_name="Regulært udtryk",
                              validators=[validate_regex_pattern])
    matchtest = models.TextField(verbose_name="Eksempler", blank=True)

    def clean(self):
        if self.matchtest and self.regexp:
            not_accepted = []
            for example in self.matchtest.split(','):
                mo = re.fullmatch(self.regexp, example)
                if mo is None:
                    not_accepted.append(example)
            if not_accepted:
                # Tie the error to the regexp field
                raise ValidationError(
                    {'regexp': "Failed examples: %s" % ','.join(not_accepted)})

    class Meta:
        ordering = ['name']
        verbose_name = 'gruppe'
        verbose_name_plural = verbose_name + 'r'

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Profile(models.Model):
    name = models.CharField(max_length=50, verbose_name="Navn")
    email = models.EmailField(max_length=50, blank=True,
                              verbose_name="Emailadresse")
    allow_direct_email = models.BooleanField(
        blank=True, default=True, verbose_name="Tillad emails til titel")
    street_name = models.CharField(max_length=50, blank=True,
                                   verbose_name="Gade")
    house_number = models.CharField(max_length=15, blank=True,
                                    verbose_name="Husnr.")
    postal_code = models.CharField(max_length=10, blank=True,
                                   verbose_name="Postnr.")
    town = models.CharField(max_length=25, blank=True, verbose_name="By")
    country = models.CharField(max_length=50, blank=True, verbose_name="Land")
    gone = models.BooleanField(blank=True, verbose_name="Afdød", default=False)
    phone_number = models.CharField(max_length=20, blank=True,
                                    verbose_name="Telefonnr.")
    note = models.TextField(blank=True, verbose_name="Note")

    groups = models.ManyToManyField(Group, blank=True, verbose_name="Grupper")

    class Meta:
        ordering = ['name']
        verbose_name = 'person'
        verbose_name_plural = verbose_name + 'er'

    def __str__(self):
        return self.name


@tk.title_class
@python_2_unicode_compatible
class Title(models.Model):
    BEST, FU, EFU = 'BEST', 'FU', 'EFU'
    KIND = [(BEST, 'BEST'), (FU, 'FU'), (EFU, 'EFU')]

    profile = models.ForeignKey('Profile', on_delete=models.CASCADE)
    period = models.IntegerField(verbose_name='Årgang')
    root = models.CharField(max_length=10, verbose_name='Titel')
    kind = models.CharField(max_length=10, choices=KIND, verbose_name='Slags')

    def title_tuple(self):
        return (self.root, self.period)

    @classmethod
    def parse(cls, title, gfyear=None, **kwargs):
        root, period = tk.parse(title, _get_gfyear(gfyear))

        letter = '(?:[A-Z]|Æ|Ø|Å|AE|OE|AA)'
        title_patterns = [
            ('BEST', '^(?:CERM|FORM|INKA|KASS|NF|PR|SEKR|VC)$'),
            ('FU', '^FU%s%s$' % (letter, letter)),
            ('EFU', '^EFU%s%s$' % (letter, letter)),
        ]
        for kind, p in title_patterns:
            if re.match(p, root):
                return cls(period=period, root=root, kind=kind, **kwargs)
        raise ValueError(title)

    class Meta:
        ordering = ['-period', 'kind', 'root']
        verbose_name = 'titel'
        verbose_name_plural = 'titler'

    @tk.set_gfyear(lambda: config.GFYEAR)
    def __str__(self):
        return '%s %s' % (tk.prefix(self, type='unicode'), getattr(self, 'profile', ''))
