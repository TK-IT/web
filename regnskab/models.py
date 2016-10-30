from django.db import models
from tkweb.apps.idm.models import (
    unicode_superscript, tk_prefix, get_period, parse_bestfu_alias,
)


class Profile(models.Model):
    name = models.CharField(max_length=50, verbose_name="Navn")
    email = models.EmailField(max_length=50, blank=True,
                              verbose_name="Emailadresse")

    class Meta:
        ordering = ['name']
        verbose_name = 'person'
        verbose_name_plural = verbose_name + 'er'

    def __str__(self):
        return self.name


class Title(models.Model):
    BEST, FU, EFU = 'BEST', 'FU', 'EFU'
    KIND = [(BEST, 'BEST'), (FU, 'FU'), (EFU, 'EFU')]

    profile = models.ForeignKey('Profile')
    period = models.IntegerField(verbose_name='Årgang')
    root = models.CharField(max_length=10, verbose_name='Titel')
    kind = models.CharField(max_length=10, choices=KIND, verbose_name='Slags')

    def age(self, gfyear):
        return gfyear - self.period

    def display_root(self):
        return self.root.replace('KASS', 'KA$$')

    def display_title(self, gfyear=None):
        return '%s%s' % (tk_prefix(self.age(gfyear)), self.display_root())

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


class Alias(models.Model):
    profile = models.ForeignKey(Profile)
    period = models.IntegerField(blank=True, null=True, verbose_name='Årgang')
    root = models.CharField(max_length=10, verbose_name='Titel')

    def display_title(self, gfyear):
        return '%s%s' % (tk_prefix(self.age(gfyear)), self.root)

    class Meta:
        ordering = ['period', 'root']

    def __str__(self):
        return self.display_title()


class Sheet(models.Model):
    name = models.CharField(max_length=200, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        s = '%s %s-%s' % (self.name, self.start_date, self.end_date)
        return s.strip()


class PurchaseKind(models.Model):
    sheet = models.ForeignKey(Sheet)
    position = models.PositiveIntegerField()
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ['sheet', 'position']

    def __str__(self):
        return self.name


class SheetRow(models.Model):
    sheet = models.ForeignKey(Sheet)
    position = models.PositiveIntegerField()
    name = models.CharField(max_length=200, blank=False, null=True)
    profile = models.ForeignKey(Profile, blank=False, null=True)

    class Meta:
        ordering = ['sheet', 'position']

    def __str__(self):
        return self.name


class Purchase(models.Model):
    row = models.ForeignKey(SheetRow)
    kind = models.ForeignKey(PurchaseKind)
    count = models.DecimalField(max_digits=9, decimal_places=4,
                                help_text='antal krydser eller brøkdel')

    class Meta:
        ordering = ['row', 'kind']
