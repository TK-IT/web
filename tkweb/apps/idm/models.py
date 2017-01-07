# encoding: utf8
from __future__ import unicode_literals

import re

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from constance import config
from tkweb.apps.tkbrand.util import gfyearPPslash
import tktitler


def unicode_superscript(n):
    digits = '⁰¹²³⁴⁵⁶⁷⁸⁹'
    return ''.join(digits[int(i)] for i in str(n))


def tk_prefix(age, sup_fn=None):
    if not isinstance(age, int):
        raise TypeError(type(age).__name__)
    if sup_fn is None:
        sup_fn = unicode_superscript
    prefix = ['K', '', 'G', 'B', 'O', 'TO']
    if age < -1:
        return 'K%s' % sup_fn(-age)
    elif age + 1 < len(prefix):
        return prefix[age + 1]
    else:
        return 'T%sO' % sup_fn(age - 3)


def get_period(prefix, postfix, gfyear):
    """
    Parse a given prefix and postfix into a period.

    prefix and postfix are possibly empty strings,
    and gfyear is an int.

    If both strings are empty, the gfyear is returned:

    >>> get_period("", "", 2016)
    2016

    If only a prefix is given, it is subtracted from the gfyear:

    >>> get_period("B", "", 2016)
    2014
    >>> get_period("T30", "", 2016)
    2010
    >>> get_period("G2B2", "", 2016)
    2010

    These are the three different ways of writing 2010 as postfix.
    Note that the gfyear is ignored when postfix is given.

    >>> get_period("", "2010", 2016)
    2010
    >>> get_period("", "10", 2017)
    2010
    >>> get_period("", "1011", 2018)
    2010

    If both prefix and postfix are given, the prefix is subtracted from
    the postfix, and the gfyear is ignored:

    >>> get_period("O", "2016", 2030)
    2013
    """

    prefix = prefix.upper()
    if not re.match(r'^([KGBOT][0-9]*)*$', prefix):
        raise ValueError("Invalid prefix: %r" % prefix)
    if not re.match(r'^([0-9]{2}){0,2}$', postfix):
        raise ValueError("Invalid postfix: %r" % postfix)

    if not postfix:
        period = gfyear
    else:
        if len(postfix) == 4:
            first, second = int(postfix[0:2]), int(postfix[2:4])
            # Note that postfix 1920, 2021 and 2122 are technically ambiguous,
            # but luckily there was no BEST in 1920 and this script hopefully
            # won't live until the year 2122, so they are not actually
            # ambiguous.
            if postfix == '2021':
                # TODO: Should '2021' be parsed as 2020/21 or 2021/22?
                raise NotImplementedError(postfix)
            if (first + 1) % 100 == second:
                # There should be exactly one year between the two numbers
                if first > 56:
                    period = 1900 + first
                else:
                    period = 2000 + first
            elif first in (19, 20):
                # 19xx or 20xx
                period = int(postfix)
            else:
                raise ValueError(postfix)
        elif len(postfix) == 2:
            year = int(postfix[0:2])
            if year > 56:  # 19??
                period = 1900 + year
            else:  # 20??
                period = 2000 + year
        else:
            raise ValueError(postfix)

    # Now evaluate the prefix:
    prefix_value = dict(K=-1, G=1, B=2, O=3, T=1)
    grad = 0
    for base, exponent in re.findall(r"([KGBOT])([0-9]*)", prefix):
        exponent = int(exponent or 1)
        grad += prefix_value[base] * exponent

    return period - grad


def parse_bestfu_alias(alias, gfyear):
    """
    Resolve a BEST/FU alias into a (kind, root, period)-tuple
    where kind is 'BEST', 'FU' or 'EFU',
    root is the actual title, and period is which period the title
    refers to.

    >>> parse_bestfu_alias('OFORM', 2016)
    ('BEST', 'FORM', 2013)
    """

    alias = alias.upper()
    prefix_pattern = r"(?P<pre>(?:[KGBOT][KGBOT0-9]*)?)"
    postfix_pattern = r"(?P<post>(?:[0-9]{2}|[0-9]{4})?)"
    letter = '[A-Z]|Æ|Ø|Å|AE|OE|AA'
    letter_map = dict(AE='Æ', OE='Ø', AA='Å')
    title_patterns = [
        ('BEST', 'CERM|FORM|INKA|KASS|NF|PR|SEKR|VC'),
        ('FU', '(?P<a>E?FU)(?P<b>%s)(?P<c>%s)' % (letter, letter)),
    ]
    for kind, p in title_patterns:
        pattern = '^%s(?P<root>%s)%s$' % (prefix_pattern, p, postfix_pattern)
        mo = re.match(pattern, alias)
        if mo is not None:
            period = get_period(mo.group("pre"), mo.group("post"), gfyear)
            root = mo.group('root')
            if kind == 'FU':
                fu_kind = mo.group('a')
                letter1 = mo.group('b')
                letter2 = mo.group('c')
                assert root == fu_kind + letter1 + letter2
                # Translate AE OE AA
                letter1_int = letter_map.get(letter1, letter1)
                letter2_int = letter_map.get(letter2, letter2)
                root_int = fu_kind + letter1_int + letter2_int
                return fu_kind, root_int, period
            else:
                return kind, root, period
    raise ValueError(alias)


def get_gfyear(gfyear):
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
        return tktitler.tk_prefix(self.titletupel(), get_gfyear(gfyear),
                                  type=tktitler.PREFIXTYPE_UNICODE)

    def input_title(self, gfyear=None):
        # The title as it would be typed
        return tktitler.tk_prefix(self.titletupel(), get_gfyear(gfyear))

    def display_title_and_year(self, gfyear=None):
        if self.root == 'EFUIT':
            return self.display_title(gfyear)
        return '%s (%s)' % (self.display_title(gfyear),
                            gfyearPPslash(self.period))

    def ascii_root(self):
        tr = {197: 'AA', 198: 'AE', 216: 'OE', 229: 'aa', 230: 'ae', 248: 'oe'}
        return self.root.translate(tr)

    def email_local_part(self, gfyear=None):
        return tktitler.email(self.titletupel(), get_gfyear(gfyear))

    @classmethod
    def parse(cls, title, gfyear=None, **kwargs):
        root, period = tktitler.parse(title, get_gfyear(gfyear))

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
