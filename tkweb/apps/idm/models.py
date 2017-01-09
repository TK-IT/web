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


@python_2_unicode_compatible
class Title(models.Model):
    BEST, FU, EFU = 'BEST', 'FU', 'EFU'
    KIND = [(BEST, 'BEST'), (FU, 'FU'), (EFU, 'EFU')]

    profile = models.ForeignKey('Profile')
    period = models.IntegerField(verbose_name='Årgang')
    root = models.CharField(max_length=10, verbose_name='Titel')
    kind = models.CharField(max_length=10, choices=KIND, verbose_name='Slags')

    def titletupel(self):
        return (self.root, self.period)

    def age(self, gfyear=None):
        if gfyear is None:
            gfyear = config.GFYEAR
        return gfyear - self.period

    def display_root(self):
        return self.root.replace('KASS', 'KA$$')

    def display_title(self, gfyear=None):
        return tk.prefix(self.titletupel(), _get_gfyear(gfyear),
                         type=tk.PREFIXTYPE_UNICODE)

    def input_title(self, gfyear=None):
        # The title as it would be typed
        return tk.prefix(self.titletupel(), _get_gfyear(gfyear))

    def display_title_and_year(self, gfyear=None):
        if self.root == 'EFUIT':
            return self.display_title(gfyear)
        prefixAndName = self.display_title(gfyear)
        postfix = tk.postfix(("", self.period),
                             tk.POSTFIXTYPE_LONGSLASH)
        return '%s (%s)' % (prefixAndName, postfix)

    def ascii_root(self):
        tr = {197: 'AA', 198: 'AE', 216: 'OE', 229: 'aa', 230: 'ae', 248: 'oe'}
        return self.root.translate(tr)

    def email_local_part(self, gfyear=None):
        return tk.email(self.titletupel(), _get_gfyear(gfyear))

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

    def __str__(self):
        return '%s %s' % (self.display_title(), getattr(self, 'profile', ''))
