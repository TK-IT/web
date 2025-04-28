import re

from django.core.exceptions import ValidationError
from django.db import models
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


def validate_tktitler_root(value):
    try:
        tk.validate_title((value, 1956))
    except ValueError as exn:
        raise ValidationError("Invalid title root: %s" % exn)


def validate_tktitler_period(value):
    try:
        tk.validate_title(("", value))
    except ValueError as exn:
        raise ValidationError("Invalid title period: %s" % exn)


class Group(models.Model):
    REGEXP_MAILING_LIST = 'no$public$address'

    name = models.CharField(max_length=25, verbose_name="Navn")
    regexp = models.CharField(max_length=50, verbose_name="Regulært udtryk",
                              validators=[validate_regex_pattern])
    matchtest = models.TextField(verbose_name="Eksempler", blank=True)

    def clean(self):
        try:
            validate_regex_pattern(self.regexp)
        except ValidationError:
            # Already reported in clean_fields().
            return
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
class Title(models.Model):
    BEST, FU, EFU = 'BEST', 'FU', 'EFU'
    KIND = [(BEST, 'BEST'), (FU, 'FU'), (EFU, 'EFU')]

    profile = models.ForeignKey('Profile', on_delete=models.CASCADE)
    period = models.IntegerField(
        verbose_name="Årgang", validators=[validate_tktitler_period]
    )
    root = models.CharField(
        max_length=10, verbose_name="Titel", validators=[validate_tktitler_root]
    )
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


@python_2_unicode_compatible
class Position(models.Model):
    '''
    A position held by different groups of people through the time. Examples:

    - BEST/FU
    - ABEN
    - EFUIT
    - Quizudvalg
    '''
    name = models.CharField(max_length=100, verbose_name='Titel', unique=True)
    current_period = models.IntegerField()

    def __str__(self):
        return self.name

    @staticmethod
    def get_current_period(name):
        qs = Position.objects.filter(name=name)
        result = list(qs.values_list('current_period', flat=True))
        if not result:
            raise Position.DoesNotExist()
        if len(result) > 1:
            raise Position.MultipleObjectsReturned()  # TODO: Verify this name
        return result[0]


@python_2_unicode_compatible
class PositionPeriod(models.Model):
    '''
    A group of people holding a position at a particular time. Examples:

    - BEST/FU from 2014-09-21 until 2015-09-20
    - ABEN from 2015-12-16 until 2016-12-21
    - EFUIT from 2011-10-03 until 2013-09-23
    - Quizudvalg from 2016-04-01 until 2016-04-15

    The "age" of a PositionPeriod is the number of PositionPeriods that follow,
    which is used when forming relative titles with tktitler.
    '''
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    period = models.IntegerField()

    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [('position', 'period')]

    @property
    def current(self):
        return self.end_time is None

    @staticmethod
    def filter_by_age(position, age):
        period = position.current_period - age
        qs = PositionPeriod.objects.filter(position=position,
                                           period=period)
        return qs

    @staticmethod
    def get_by_age(position, age):
        result = PositionPeriod.filter_by_age(position, age).get()
        assert result.position_id == position.id
        result.position = position
        return result

    def get_age(self):
        return self.position.current_period - self.period

    def __str__(self):
        return tk.prefix((str(self.position), self.period),
                         self.position.current_period)


@python_2_unicode_compatible
class Holder(models.Model):
    '''
    A person having a particular title in a particular position. Examples:

    - 18 people in BEST/FU from 2014-09-21, all with different titles
    - 2 people in ABEN from 2015-12-16, both with title "ABEN"
    - 1 person in EFUIT from 2011-10-03 with title "EFUIT"
    '''
    title = models.ForeignKey(PositionPeriod, on_delete=models.CASCADE)
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE)
    root = models.CharField(max_length=10, verbose_name='Titel')

    @staticmethod
    def get_by_age(position, age):
        try:
            position_period = PositionPeriod.get_by_age(position, age)
        except PositionPeriod.DoesNotExist:
            raise Holder.DoesNotExist()
        result = list(position_period.holder_set.all())
        if not result:
            raise Holder.DoesNotExist()
        for o in result:
            # TODO Is this assignment already done by Django?
            o.title = position_period
        return result

    def __str__(self):
        return tk.prefix((self.root, self.title.period),
                         self.title.position.current_period)
