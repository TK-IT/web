import re
from django.db import models
from regnskabsite import config


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


class Profile(models.Model):
    name = models.CharField(max_length=50, verbose_name="Navn")
    email = models.EmailField(max_length=50, blank=True,
                              verbose_name="Emailadresse")

    class Meta:
        ordering = ['name']
        verbose_name = 'person'
        verbose_name_plural = verbose_name + 'er'

    def __str__(self):
        return str(self.name)


class Title(models.Model):
    BEST, FU, EFU = 'BEST', 'FU', 'EFU'
    KIND = [(BEST, 'BEST'), (FU, 'FU'), (EFU, 'EFU')]

    profile = models.ForeignKey('Profile')
    period = models.IntegerField(verbose_name='Årgang')
    root = models.CharField(max_length=10, verbose_name='Titel')
    kind = models.CharField(max_length=10, choices=KIND, verbose_name='Slags')

    def age(self, gfyear=None):
        if gfyear is None:
            gfyear = config.GFYEAR
        return gfyear - self.period

    def display_root(self):
        return self.root.replace('KASS', 'KA$$')

    def display_title(self, gfyear=None):
        return '%s%s' % (tk_prefix(self.age(gfyear)), self.display_root())

    def input_title(self, gfyear=None):
        # The title as it would be typed
        return '%s%s' % (tk_prefix(self.age(gfyear), sup_fn=str), self.root)

    def display_title_and_year(self, gfyear=None):
        return '%s (%02d/%02d)' % (self.display_title(gfyear),
                                   self.period % 100, (self.period+1) % 100)

    def ascii_root(self):
        tr = {197: 'AA', 198: 'AE', 216: 'OE', 229: 'aa', 230: 'ae', 248: 'oe'}
        return self.root.translate(tr)

    def email_local_part(self, gfyear=None):
        return '%s%s' % (tk_prefix(self.age(gfyear), sup_fn=str),
                         self.ascii_root())

    @classmethod
    def parse(cls, title, gfyear, **kwargs):
        kind, root, period = parse_bestfu_alias(title, gfyear)
        return cls(period=period, root=root, kind=kind, **kwargs)

    class Meta:
        ordering = ['-period', 'kind', 'root']
        verbose_name = 'titel'
        verbose_name_plural = 'titler'

    def __str__(self):
        return '%s %s' % (self.display_title(), getattr(self, 'profile', ''))
