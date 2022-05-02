import os
import re
import base64
import hashlib
import logging
import datetime
import tempfile
import functools
import itertools
import contextlib
from collections import OrderedDict
from decimal import Decimal

from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.db import models
from django.db.models import F
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
from django.utils.text import slugify as dslugify
from django.utils.html import format_html
from django.template.defaultfilters import floatformat

from unidecode import unidecode
from jsonfield import JSONField
import tktitler as tk

from tkweb.apps.regnskab.rules import get_default_prices
from tkweb.apps.regnskab.utils import (
    sum_vector, sum_matrix, plain_to_html, html_to_plain, EmailMultiRelated,
)

from constance import config
from tkweb.apps.idm.models import Profile, Title

logger = logging.getLogger('regnskab')


BEST_ORDER = dict(zip('FORM INKA KASS NF CERM SEKR PR VC'.split(), range(8)))


def get_inka():
    try:
        return Profile.objects.get(title__root='INKA',
                                   title__period=config.GFYEAR)
    except Profile.DoesNotExist:
        return Profile()


def _get_gfyear(gfyear):
    if gfyear is None:
        return config.GFYEAR
    return gfyear


class SheetStatus(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=False)
    created_time = models.DateTimeField(auto_now_add=True)

    def since(self):
        if self.end_time:
            return 'ikke siden %s' % (self.end_time.date(),)
        else:
            return 'siden %s' % (self.start_time.date(),)


@tk.title_class
class Alias(models.Model):
    profile = models.ForeignKey(Profile)
    period = models.IntegerField(
        blank=True, null=True, verbose_name='Årgang',
        help_text='Bruges kun hvis aliaset skal opdateres automatisk ' +
                  'efter hver GF')
    root = models.CharField(max_length=200, verbose_name='Alias')
    is_title = models.BooleanField(
        blank=True, default=False, verbose_name='Primær titel',
        help_text='Markeres hvis aliaset skal vises foran personens navn ' +
                  'som om det var en titel.')
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=False)
    created_time = models.DateTimeField(auto_now_add=True)

    def title_tuple(self):
        if self.period is None:
            raise ValueError('Cannot take tk.prefix of Alias with no period')
        return (self.root, self.period)

    def clean(self):
        if self.is_title and self.period is not None:
            raise ValidationError('Primær titel må ikke have en årgang')

    class Meta:
        ordering = ['period', 'root']
        verbose_name = 'alias'
        verbose_name_plural = verbose_name + 'er'

    def __str__(self):
        return tk.postfix(self) if self.period else self.root


class Transaction(models.Model):
    PAYMENT, PURCHASE, CORRECTION = 'payment', 'purchase', 'correction'
    KIND = [
        (PAYMENT, 'Betaling'),
        (PURCHASE, 'Diverse køb'),
        (CORRECTION, 'Korrigering'),
    ]

    session = models.ForeignKey('Session', on_delete=models.CASCADE,
                                null=True, blank=False)
    kind = models.CharField(max_length=10, choices=KIND)
    profile = models.ForeignKey(Profile)
    time = models.DateTimeField()
    period = models.IntegerField(verbose_name='Årgang')
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    note = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=False)
    created_time = models.DateTimeField(auto_now_add=True)

    def get_kind_display(self):
        if self.note:
            return self.note
        return next((l for k, l in Transaction.KIND if k == self.kind),
                    '')

    def __str__(self):
        return '%.2f kr.' % self.amount


def title_key(t):
    # EFU after others. Latest period first.
    kind = 'Alias' if isinstance(t, Alias) else t.kind
    if kind == Title.BEST:
        return (0, -t.period, BEST_ORDER.get(t.root, 9))
    elif kind == Title.FU:
        return (0, -t.period, 10, t.root)
    elif kind == Title.EFU:
        return (1, -t.period, t.root)
    elif kind == 'Alias':
        return (2, t.root)
    else:
        raise ValueError(kind)


def get_titles(profile_ids=None, period=None, time=None):
    '''dict mapping profile id to list of titles in priority order'''
    title_qs = Title.objects.all()
    alias_qs = Alias.objects.filter(is_title=True)
    if profile_ids:
        title_qs = title_qs.filter(profile_id__in=profile_ids)
        alias_qs = alias_qs.filter(profile_id__in=profile_ids)

    if period is not None:
        title_qs = title_qs.filter(period__lte=period)
    title_qs = title_qs.order_by('profile_id')
    alias_qs = alias_qs.order_by('-start_time')
    if time is not None:
        alias_qs = alias_qs.exclude(start_time__gt=time)

    groups = itertools.groupby(title_qs, key=lambda t: t.profile_id)
    titles = {pk: sorted(g, key=title_key) for pk, g in groups}

    # Add primary aliases
    for t in alias_qs:
        titles.setdefault(t.profile_id, []).append(t)
    return titles


@functools.wraps(get_titles)
def get_primary_titles(*args, **kwargs):
    all_titles = get_titles(*args, **kwargs)
    return {p: ts[0] for p, ts in all_titles.items()}


def slugify(string):
    return dslugify(unidecode(string))


def sheet_upload_to(instance, original_filename):
    base, ext = os.path.splitext(os.path.basename(original_filename))
    return 'sheet/%s%s' % (slugify(base), ext)


class Sheet(models.Model):
    session = models.ForeignKey('Session', on_delete=models.CASCADE,
                                null=True, blank=False)
    name = models.CharField(max_length=200, blank=True,
                            help_text='f.eks. HSTR, revy, matlabotanisk have')
    start_date = models.DateField()
    end_date = models.DateField()
    period = models.IntegerField(verbose_name='Årgang')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=False)
    created_time = models.DateTimeField(auto_now_add=True)

    image_file = models.FileField(upload_to=sheet_upload_to,
                                  blank=True, null=True)
    row_image_width = models.PositiveIntegerField(blank=True, null=True)
    row_image = models.FileField(upload_to=sheet_upload_to,
                                 blank=True, null=True)

    def columns(self):
        qs = self.purchasekind_set.all()
        return qs.order_by('position')

    def rows(self):
        result = []
        transactions = self.legacy_transactions()
        kinds = list(self.columns())
        kind_dict = {kind.id: kind for kind in kinds}
        sheetrow_qs = self.sheetrow_set.all()
        sheetrow_qs = sheetrow_qs.select_related('profile')
        sheetrow_qs = sheetrow_qs.prefetch_related('purchase_set')
        for row in sheetrow_qs:
            purchases = {
                p.kind_id: p
                for p in row.purchase_set.all()
            }
            for purchase in purchases.values():
                # Use cached kind
                purchase.kind = kind_dict[purchase.kind_id]
            purchase_list = [
                purchases.get(kind.id, Purchase(row=row, kind=kind, count=0))
                for kind in kinds
            ]
            for p in purchase_list:
                if p.count % 1 == 0:
                    p.counter = range(int(p.count))
                else:
                    p.counter = None
            im_url, im_width, im_start, im_stop = row.image_data()
            if im_url:
                image = dict(url=im_url, width=im_width,
                             start=im_start, stop=im_stop,
                             height=im_stop - im_start)
            else:
                image = None
            row_empty = not any(p.count for p in purchase_list)
            result.append(dict(
                id=row.id,
                profile=row.profile,
                position=row.position,  # needed?
                name=row.name,
                kinds=purchase_list,
                image=image,
                empty=row_empty,
                legacy_transactions=transactions.pop(row.profile_id, {}),
            ))
        profile_ids = set(row['profile'] for row in result)
        titles = get_primary_titles(profile_ids=profile_ids,
                                    period=self.period)

        for row in result:
            try:
                title = row['title'] = titles[row['profile'].id]
            except (KeyError, AttributeError):
                title = row['title'] = row['display_title'] = None
                row['title_name'] = (
                    row['profile'].name if row['profile'] else '')
            else:
                row['display_title'] = (
                    tk.prefix(title, self.period, type='unicode')
                    if title.period else title.root)
                row['title_name'] = ' '.join(
                    (row['display_title'], row['profile'].name))

        if self.legacy_style():
            # Sort rows by title, period
            def key(row):
                if isinstance(row['title'], Title):
                    return (0, -row['title'].period,
                            row['title'].kind,
                            row['title'].root)
                return (1,)

            result.sort(key=key)
        return result

    def legacy_style(self):
        return self.session_id is None

    def legacy_transactions(self):
        if not self.legacy_style():
            return {}
        d = self.end_date
        d1 = d - datetime.timedelta(1)
        d2 = d + datetime.timedelta(1)
        qs = Transaction.objects.filter(time__gt=d1, time__lt=d2)
        qs = (t for t in qs if t.time.date() == d)
        transactions = {}
        for t in qs:
            for_profile = transactions.setdefault(t.profile_id, {})
            amount = -t.amount if t.kind == Transaction.PAYMENT else t.amount
            try:
                for_profile[t.kind] += amount
            except KeyError:
                for_profile[t.kind] = amount
        return transactions

    @contextlib.contextmanager
    def image_file_name(self):
        '''
        Open the image file, regardless of whether the model has been saved
        to the database or not.

        When the Sheet is being uploaded and saved, self.image_file.path
        is blank even though the image file exists somewhere on the host.

        This context manager yields the filename of a file containing the
        image associated with the Sheet.

        The context manager is partially re-entrant: The first opening of
        image_file_name() instantiates a filename, and when the first
        context is closed, the filename is invalidated. Any additional
        openings in between return the same filename.

        That is, this is valid::

            with sheet.image_file_name() as f1:
                with sheet.image_file_name() as f2:
                    assert f1 == f2
                    # f2 is valid
                # f2 is still valid
            # f2 is now invalid

        But the following is not valid::

            c1 = sheet.image_file_name()
            f1 = c1.__enter__()
            with sheet.image_file_name() as f2:
                # f2 is valid
                assert f1 == f2
                c1.__exit__(None, None, None)
                # c2 is not closed, but f2 is now invalid
        '''
        try:
            f = self._image_file_name
        except AttributeError:
            pass
        else:
            yield f
            return
        if self.image_file and os.path.exists(self.image_file.path):
            yield self.image_file.path
        else:
            with tempfile.NamedTemporaryFile(mode='w+b') as fp:
                self.image_file.file.open('rb')
                fp.write(self.image_file.file.read())
                fp.flush()
                self._image_file_name = fp.name
                yield fp.name
                del self._image_file_name

    class Meta:
        ordering = ['start_date']
        verbose_name = 'krydsliste'
        verbose_name_plural = verbose_name + 'r'

    def __str__(self):
        s = '%s %s-%s' % (self.name, self.start_date, self.end_date)
        return s.strip()


class PurchaseKind(models.Model):
    sheets = models.ManyToManyField(Sheet)
    position = models.PositiveIntegerField()
    name = models.CharField(max_length=200,
                            help_text='f.eks. guldøl, guldølskasser')
    unit_price = models.DecimalField(max_digits=12, decimal_places=2,
                                     help_text='f.eks. 8, 10, 13, 200, 250')

    @property
    def short_name(self):
        if self.name.endswith('kasse'):
            return 'ks'
        return self.name

    @classmethod
    def get_or_create(cls, name, position, unit_price):
        qs = cls.objects.filter(name=name, position=position,
                                unit_price=unit_price)
        try:
            kind = qs[0]
        except IndexError:
            kind = PurchaseKind(name=name, position=position,
                                unit_price=unit_price)
            kind.save()
        return kind

    class Meta:
        ordering = ['position']
        verbose_name = 'prisklasse'
        verbose_name_plural = verbose_name + 'r'

    def __str__(self):
        return str(self.name)


class SheetRow(models.Model):
    sheet = models.ForeignKey(Sheet)
    position = models.PositiveIntegerField()
    name = models.CharField(max_length=200, blank=False, null=True)
    profile = models.ForeignKey(Profile, blank=False, null=True)
    image_start = models.PositiveIntegerField(blank=True, null=True)
    image_stop = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        ordering = ['sheet', 'position']
        verbose_name = 'krydslisteindgang'
        verbose_name_plural = verbose_name + 'e'

    def image_data(self):
        if self.image_start is None or self.image_stop is None:
            return None, None, None, None
        row_image = self.sheet.row_image
        row_image_width = self.sheet.row_image_width
        if not row_image or not row_image_width:
            return None, None, None, None
        return (row_image.url, row_image_width,
                self.image_start, self.image_stop)

    def image_html(self):
        url, width, start, stop = self.image_data()
        if not url:
            return ''
        return format_html(
            '<div style="display:inline-block;overflow:hidden;' +
            'position:relative;width:{}px;height:{}px">' +
            '<img src="{}" style="position:absolute;top:-{}px" /></div>',
            width, stop - start, url, start)

    def __str__(self):
        return self.name or str(self.profile)


class Purchase(models.Model):
    row = models.ForeignKey(SheetRow)
    kind = models.ForeignKey(PurchaseKind)
    count = models.DecimalField(max_digits=9, decimal_places=4,
                                help_text='antal krydser eller brøkdel')

    def __str__(self):
        return '%g× %s' % (self.count, self.kind)

    def get_count_display(self):
        if self.count % 1 == 0:
            return str(int(self.count))
        else:
            return floatformat(self.count, '4').rstrip('0')

    class Meta:
        ordering = ['row', 'kind__position']
        verbose_name = 'krydser'
        verbose_name_plural = verbose_name


def compute_balance(profile_ids=None, created_before=None, *,
                    output_matrix=False, purchases_after=None):
    purchase_qs = Purchase.objects.all()
    if created_before:
        purchase_qs = purchase_qs.filter(
            row__sheet__created_time__lt=created_before)
    if profile_ids:
        purchase_qs = purchase_qs.filter(row__profile_id__in=profile_ids)
    purchase_qs = purchase_qs.exclude(row__profile_id=None)
    balance = sum_vector(purchase_qs, 'row__profile_id',
                         F('count') * F('kind__unit_price'))

    transaction_qs = Transaction.objects.all()
    if profile_ids:
        transaction_qs = transaction_qs.filter(profile_id__in=profile_ids)
    if created_before:
        transaction_qs = transaction_qs.filter(created_time__lt=created_before)
    transaction_balance = sum_vector(transaction_qs, 'profile_id', 'amount')
    for profile_id, amount in transaction_balance.items():
        try:
            balance[profile_id] += amount
        except KeyError:
            balance[profile_id] = amount
    if output_matrix:
        if purchases_after:
            purchase_qs = purchase_qs.filter(
                row__sheet__start_date__gte=purchases_after)
            transaction_qs = transaction_qs.filter(time__gt=purchases_after)
        purchases = sum_matrix(purchase_qs, 'kind__name',
                               'row__profile_id', 'count')
        purchases.update(sum_matrix(transaction_qs, 'kind',
                                    'profile_id', 'amount'))
        return balance, purchases
    else:
        return balance


class EmailTemplateInline(models.Model):
    mime_type = models.CharField(max_length=255)
    blob = models.BinaryField()
    hash = models.CharField(max_length=255)

    def compute_hash(self):
        algo = 'sha256'
        hexdigest = getattr(hashlib, algo)(self.blob).hexdigest()
        self.hash = '%s-%s' % (algo, hexdigest)
        return self.hash

    @classmethod
    def get_or_create(cls, mime_type, blob):
        o = cls(mime_type=mime_type, blob=blob)
        o.compute_hash()
        try:
            return cls.objects.get(hash=o.hash)
        except cls.DoesNotExist:
            o.save()
            return o


def _process_inlines(body_html, cb):
    '''
    Internal helper used by body_html_data_uris and body_html_inlines.
    '''
    def repl(mo):
        q1, inline_pk, hash, q2 = mo.groups()
        try:
            inline = EmailTemplateInline.objects.get(
                pk=inline_pk, hash=hash)
        except EmailTemplateInline.DoesNotExist:
            res = cb(None)
            return mo.group() if res is None else q1 + res + q2
        else:
            return q1 + cb(inline) + q2

    pattern = r'([\'"])cid:regnskab-(\d+)-([a-zA-Z0-9-]+)([\'"])'
    return re.sub(pattern, repl, body_html)


def body_html_inlines(body_html):
    '''
    Returns (html, inlines), where `html` is the HTML body including
    images with cid:-URIs and `inlines` is a list mapping each
    "cid:foobar"-URI to ('foobar', <EmailTemplateInline object>).
    '''
    # Invisible GIF, https://stackoverflow.com/a/15960901/1570972
    invis = ('data:image/gif;base64,' +
             'R0lGODlhAQABAAAAACH5BAEAAAAALAAAAAABAAEAAAI=')
    inlines = []

    def cb(inline):
        if inline is not None:
            cid = inline.hash
            inlines.append((cid, inline))
            return 'cid:%s' % cid
        return invis

    return _process_inlines(body_html, cb), inlines


class EmailTemplate(models.Model):
    POUND = 'pound'
    FORMAT = [(POUND, 'pound')]
    PLAIN = 'plain'
    HTML = 'html'
    MARKUP = [(PLAIN, 'Ren tekst'), (HTML, 'HTML')]

    name = models.CharField(max_length=255, blank=True)
    subject = models.TextField(blank=False)
    body = models.TextField(blank=False)
    format = models.CharField(max_length=10, choices=FORMAT)
    markup = models.CharField(max_length=10, choices=MARKUP)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=False)
    created_time = models.DateTimeField(auto_now_add=True)

    def refcount(self):
        '''
        Return the number of COW-references to this EmailTemplate.
        If refcount() == 0, the object is not visible on the site.
        If refcount() > 1, then the object should be forked before
        being updated.
        '''
        count = Session.objects.filter(email_template_id=self.id).count()
        count += Newsletter.objects.filter(email_template_id=self.id).count()
        if self.name:
            # EmailTemplateList refers to this
            count += 1
        return count

    def make_template_editable(self, user):
        if self.name == '':
            raise AssertionError('make_template_editable: anonymous template')
        sessions = Session.objects.filter(email_template_id=self.id)
        if sessions.exists():
            # Move Session objects pointing to self to a new anonymous
            # EmailTemplate.
            backup = EmailTemplate(
                name='',
                subject=self.subject,
                body=self.body,
                format=self.format,
                markup=self.markup,
                created_by=user)
            backup.save()
            sessions.update(email_template=backup)

    def clean(self):
        '''
        Replace data:-URIs with cid:-URIs of the form "regnskab-<pk>-<hash>",
        where <pk> is the ID of an EmailTemplateInline object with the
        appropriate <hash>.
        '''
        if self.markup == EmailTemplate.HTML:
            def repl(mo):
                q1, mime_type, base64_data, q2 = mo.groups()
                # We don't care to assert that q1 == q2 (GIGO).
                blob = base64.b64decode(base64_data)
                o = EmailTemplateInline.get_or_create(mime_type, blob)
                return '%scid:regnskab-%s-%s%s' % (q1, o.pk, o.hash, q2)

            # Require the data:-URI to be quoted to allow whitespace.
            # Note that we don't permit non-base64-URIs or MIME parameters.
            pattern = (
                r'([\'"])data:([a-z]+/[a-z0-9-]+);base64,' +
                r'([a-zA-Z0-9+/= \t\n\r]*)([\'"])')
            self.body = re.sub(pattern, repl, self.body)
            if 'data:' in self.body and settings.DEBUG:
                raise ValueError(self.body)

    def body_html_data_uris(self):
        '''
        Returns HTML with valid cid:-URIs replaced by data:-URIs.
        '''
        def cb(inline):
            if inline is not None:
                return 'data:%s;base64,%s' % (
                    inline.mime_type, base64.b64encode(inline.blob).decode())

        return _process_inlines(self.body_html(), cb)

    def body_html(self):
        '''
        Return body text as HTML, converting from plain text if necessary.
        '''
        if self.markup == EmailTemplate.HTML:
            return self.body
        elif self.markup == EmailTemplate.PLAIN:
            return plain_to_html(self.body)
        else:
            raise ValueError(self.markup)

    def body_plain(self):
        '''
        Return body text as plain text, converting from HTML if necessary.
        '''
        if self.markup == EmailTemplate.HTML:
            return html_to_plain(self.body)
        elif self.markup == EmailTemplate.PLAIN:
            return self.body
        else:
            raise ValueError(self.markup)

    def __str__(self):
        return self.name or str(self.created_time)


def regenerate_emails(email_set):
    assert isinstance(email_set, (Session, Newsletter))

    if email_set.email_template is None:
        raise ValidationError("template required to generate emails")

    if email_set.sent:
        raise ValidationError(
            "Tried to regenerate emails for session already sent")

    if email_set.email_template.markup == EmailTemplate.HTML:
        html_template = email_set.email_template.body_html()
        if '#SKJULNUL:' in html_template:
            # TODO Handle #SKJULNUL:# in HTML emails.
            raise ValidationError(
                '#SKJULNUL:# kan ikke bruges i HTML-emails')

    recipients = email_set.get_recipient_data()

    for profile_id, profile_data in recipients.items():
        regenerate_email(email_set, profile_data)


def get_base_recipient_data(email_set):
    assert isinstance(email_set, (Session, Newsletter))
    recipients = {}
    profiles = get_profiles_title_status(period=email_set.period)
    for profile in profiles:
        recipients[profile.id] = dict(profile=profile, title=profile.title)
    initial_balances = compute_balance(created_before=email_set.created_time)
    for p_id, initial_balance in initial_balances.items():
        recipients[p_id]['initial_balance'] = initial_balance
    for p_id, balance in compute_balance().items():
        recipients[p_id]['balance'] = balance

    emails = email_set.email_set.all()
    emails = emails.order_by('profile_id')
    for email in emails:
        recipients[email.profile_id]['email'] = email

    # Cache call to get_inka
    email_set._inka = get_inka()
    # Cache call to get_max_debt
    from tkweb.apps.regnskab.rules import get_max_debt
    email_set._max_debt = get_max_debt()

    return recipients


def get_base_email_context(email_set, profile_data):
    assert isinstance(email_set, (Session, Newsletter))

    from tkweb.apps.regnskab.emailtemplate import format_price

    primary_title = profile_data.get('title')
    balance = profile_data.get('balance', Decimal())
    profile = profile_data['profile']
    initial_balance = profile_data.get('initial_balance', Decimal())

    if primary_title:
        title = (tk.prefix(primary_title, email_set.period, type='unicode')
                 if primary_title.period else primary_title.root)
    else:
        title = None

    context = {
        'TITEL ': title + ' ' if title else '',
        'NAVN': profile.name,
        'GAELDFOER': format_price(initial_balance),
        'GAELD': format_price(balance),
        'MAXGAELD': format_price(email_set._max_debt),
        'INKA': email_set._inka.name,
    }
    return context


def regenerate_email(email_set, profile_data):
    assert isinstance(email_set, (Session, Newsletter))

    if isinstance(email_set, Session):
        email_class = Email
    elif isinstance(email_set, Newsletter):
        email_class = NewsletterEmail
    else:
        raise TypeError(type(email_set))

    from tkweb.apps.regnskab.emailtemplate import format
    context = email_set.get_email_context(profile_data)
    existing_email = profile_data.get('email')
    if context is None:
        if existing_email:
            existing_email.delete()
        return
    profile = profile_data['profile']

    email_fields = ('subject', 'body_plain', 'body_html',
                    'recipient_name', 'recipient_email')
    try:
        email = email_class(
            profile=profile,
            subject=format(email_set.email_template.subject, context),
            body_plain=format(email_set.email_template.body_plain(), context),
            recipient_name=profile.name,
            recipient_email=profile.email,
        )
        email.email_set = email_set
        if email_set.email_template.markup == EmailTemplate.HTML:
            email.body_html = format(
                email_set.email_template.body_html(), context)
    except KeyError as exn:
        raise ValidationError("Emailskabelon har en ukendt variabel %r" %
                              exn.args[0])
    if existing_email:
        changed_keys = [k for k in email_fields
                        if getattr(email, k) != getattr(existing_email, k)]
        if changed_keys:
            email.pk = existing_email.pk
        else:
            return
    email.save()


class Session(models.Model):
    email_template = models.ForeignKey(EmailTemplate,
                                       on_delete=models.SET_NULL,
                                       null=True, blank=False,
                                       verbose_name='Emailskabelon')
    period = models.IntegerField(verbose_name='Årgang')
    send_time = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=False)
    created_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        get_latest_by = 'created_time'

    @property
    def sent(self):
        return bool(self.send_time)

    def regenerate_emails(self):
        regenerate_emails(self)

    def get_recipient_data(self):
        recipients = get_base_recipient_data(self)

        transactions = self.transaction_set.all().order_by('profile_id')
        transaction_sums = sum_vector(transactions, 'profile_id', 'amount')
        payment_sums = sum_vector(
            transactions.filter(kind=Transaction.PAYMENT),
            'profile_id', 'amount')
        for p_id, transaction_sum in transaction_sums.items():
            recipients[p_id]['transaction_sum'] = transaction_sum
        for p_id, payment_sum in payment_sums.items():
            recipients[p_id]['payment_sum'] = payment_sum

        kind_qs = PurchaseKind.objects.filter(sheets__session=self)
        kind_qs = kind_qs.order_by('name', 'unit_price')
        kind_groups = itertools.groupby(kind_qs, key=lambda k: k.name)
        self._kind_price = {n: set(k.unit_price for k in g)
                            for n, g in kind_groups}
        if not self._kind_price:
            self._kind_price = {n: {p} for n, p in get_default_prices()}

        purchases = Purchase.objects.filter(
            row__sheet__session=self)
        purchases = purchases.exclude(row__profile=None)
        pmatrix = sum_matrix(purchases, 'row__profile_id', 'kind__name',
                             F('count'))
        for p_id, purchase_count in pmatrix.items():
            recipients[p_id]['purchase_count'] = purchase_count

        return recipients

    def get_email_context(self, profile_data):
        from tkweb.apps.regnskab.emailtemplate import (
            format_price, format_price_set, format_count,
        )
        context = get_base_email_context(self, profile_data)

        kind_price = self._kind_price

        payment_sum = profile_data.get('payment_sum', 0)
        transaction_sum = profile_data.get('transaction_sum', 0)
        other_sum = transaction_sum - payment_sum
        purchase_count = profile_data.get('purchase_count') or {}
        balance = profile_data.get('balance', Decimal())
        profile = profile_data['profile']
        any_debt = balance > 0
        any_crosses = any(purchase_count.values())
        any_payments = payment_sum != 0
        any_others = other_sum != 0
        send_email = any_debt or any_crosses or any_payments or any_others
        if not send_email or not profile.email:
            return

        # kasse_count is legacy
        kasse_count = purchase_count.get('ølkasse', Decimal())
        if 'guldølkasse' in purchase_count:
            guld_ratio = (next(iter(kind_price['guldølkasse'])) /
                          next(iter(kind_price['ølkasse'])))
            kasse_count += guld_ratio * purchase_count['guldølkasse']
        if 'sodavandkasse' in purchase_count:
            vand_ratio = (next(iter(kind_price['sodavandkasse'])) /
                          next(iter(kind_price['ølkasse'])))
            kasse_count += vand_ratio * purchase_count['sodavandkasse']

        context.update({
            'BETALT': format_price(-payment_sum),
            'ANDET': format_price(other_sum),
            'POEL': format_price_set(kind_price.get('øl', ())),
            'PVAND': format_price_set(kind_price.get('sodavand', ())),
            'PGULD': format_price_set(kind_price.get('guldøl', ())),
            'PKASSER': format_price_set(kind_price.get('ølkasse', ())),
            'POELKS': format_price_set(kind_price.get('ølkasse', ())),
            'PGULDKS': format_price_set(kind_price.get('guldølkasse', ())),
            'PVANDKS': format_price_set(kind_price.get('sodavandkasse', ())),
            'OEL': format_count(purchase_count.get('øl', 0)),
            'VAND': format_count(purchase_count.get('sodavand', 0)),
            'GULD': format_count(purchase_count.get('guldøl', 0)),
            'OELKS': format_count(purchase_count.get('ølkasse', 0)),
            'VANDKS': format_count(purchase_count.get('sodavandkasse', 0)),
            'GULDKS': format_count(purchase_count.get('guldølkasse', 0)),
            'KASSER': format_count(kasse_count),  # Legacy
        })
        return context


class Newsletter(models.Model):
    email_template = models.ForeignKey(EmailTemplate,
                                       on_delete=models.SET_NULL,
                                       null=True, blank=False,
                                       verbose_name='Emailskabelon')
    period = models.IntegerField(verbose_name='Årgang')
    send_time = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=False)
    created_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        get_latest_by = 'created_time'

    @property
    def sent(self):
        return bool(self.send_time)

    def regenerate_emails(self):
        regenerate_emails(self)

    def get_email_context(self, profile_data):
        if not profile_data['profile'].in_current:
            return
        return get_base_email_context(self, profile_data)

    def get_recipient_data(self):
        return get_base_recipient_data(self)


def to_message(email):
    assert isinstance(email, (Email, NewsletterEmail))

    sender = 'INKA@TAAGEKAMMERET.dk'
    list_requests = 'admin@TAAGEKAMMERET.dk'
    list_name = 'krydsliste'
    list_id = '%s.TAAGEKAMMERET.dk' % list_name
    unsub = '<mailto:%s?subject=unsubscribe%%20%s>' % (list_requests, list_name)
    help = '<mailto:%s?subject=list-help>' % (list_requests,)
    sub = '<mailto:%s?subject=subscribe%%20%s>' % (list_requests, list_name)

    headers = OrderedDict([
        ('From', 'INKA@TAAGEKAMMERET.dk'),
        ('X-TK-Sender', 'INKAs regnskab'),
        ('X-TK-Recipient', email.recipient_email),
        ('Sender', sender),
        ('List-Name', list_name),
        ('List-Id', list_id),
        ('List-Unsubscribe', unsub),
        ('List-Help', help),
        ('List-Subscribe', sub),
        ('Precedence', 'bulk'),
        ('X-Auto-Response-Suppress', 'OOF'),
        ('Organization', 'TÅGEKAMMERET'),
    ])

    reply_to = ['INKA@TAAGEKAMMERET.dk']
    to = ['%s <%s>' % (email.recipient_name, email.recipient_email)]
    if email.body_html is not None:
        msg = EmailMultiRelated(
            subject=email.subject,
            body=email.body_plain,
            from_email=sender,
            reply_to=reply_to,
            to=to,
            headers=headers)
        html, relateds = body_html_inlines(email.body_html)
        msg.attach_alternative(html, 'text/html')
        for cid, r in relateds:
            msg.attach_related(r.blob, r.mime_type, cid)
        return msg

    return EmailMessage(
        subject=email.subject,
        body=email.body_plain,
        from_email=sender,
        reply_to=reply_to,
        to=to,
        headers=headers)


def email_body_html_data_uris(email):
    '''
    Returns HTML with valid cid:-URIs replaced by data:-URIs.
    '''
    assert isinstance(email, (Email, NewsletterEmail))
    if email.body_html is None:
        return format_html('<pre style="white-space: pre-wrap">{}</pre>',
                           email.body_plain)
    def cb(inline):
        if inline is not None:
            return 'data:%s;base64,%s' % (
                inline.mime_type, base64.b64encode(inline.blob).decode())

    return _process_inlines(email.body_html, cb)


class Email(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE,
                                related_name='email_set')
    profile = models.ForeignKey(Profile, on_delete=models.SET_NULL,
                                null=True, blank=False, related_name='+')
    subject = models.TextField(blank=False)
    body_plain = models.TextField(blank=False)
    body_html = models.TextField(blank=True, null=True)
    recipient_name = models.CharField(max_length=255)
    recipient_email = models.CharField(max_length=255)

    @property
    def email_set(self):
        return self.session

    @email_set.setter
    def email_set(self, v):
        self.session = v

    def to_message(self):
        return to_message(self)

    def body_html_data_uris(self):
        return email_body_html_data_uris(self)

    def __str__(self):
        return '%s <%s>' % (self.recipient_name, self.recipient_email)


class NewsletterEmail(models.Model):
    newsletter = models.ForeignKey(Newsletter, on_delete=models.CASCADE,
                                   related_name='email_set')
    profile = models.ForeignKey(Profile, on_delete=models.SET_NULL,
                                null=True, blank=False, related_name='+')
    subject = models.TextField(blank=False)
    body_plain = models.TextField(blank=False)
    body_html = models.TextField(blank=True, null=True)
    recipient_name = models.CharField(max_length=255)
    recipient_email = models.CharField(max_length=255)

    @property
    def email_set(self):
        return self.newsletter

    @email_set.setter
    def email_set(self, v):
        self.newsletter = v

    def to_message(self):
        return to_message(self)

    def body_html_data_uris(self):
        return email_body_html_data_uris(self)

    def __str__(self):
        return '%s <%s>' % (self.recipient_name, self.recipient_email)


def get_profiles_title_status(period=None, time=None):
    def profile_key(p):
        if p.status is None:
            return (3, p.name)
        elif not p.in_current:
            return (2, p.name)
        elif p.title is None:
            return (1, p.name)
        elif isinstance(p.title, Alias):
            return (1, '%s %s' % (p.title, p.name))
        else:
            return (0, title_key(p.title))

    titles = get_titles(period=period, time=time)
    status_qs = SheetStatus.objects.all().order_by('profile_id')
    if time is not None:
        status_qs = status_qs.exclude(start_time__gt=time)
    groups = itertools.groupby(status_qs, key=lambda s: s.profile_id)
    statuses = {pk: max(s, key=lambda s: (s.end_time is None, s.end_time))
                for pk, s in groups}

    profiles = list(Profile.objects.all())
    for p in profiles:
        p.status = statuses.get(p.id)
        p.titles = titles.get(p.id, [])
        p.title = p.titles[0] if p.titles else None
        if p.title:
            p.title_name = (
                '%s %s' %
                (tk.prefix(p.title, period or config.GFYEAR, type='unicode')
                 if p.title.period else p.title.root,
                 p.name))
        else:
            p.title_name = p.name
        p.in_current = (p.status and
                        (p.status.end_time is None or
                         (time is not None and p.status.end_time > time)))
    profiles.sort(key=profile_key)
    return profiles


class SheetImage(models.Model):
    sheet = models.ForeignKey(Sheet, on_delete=models.CASCADE)
    page = models.PositiveIntegerField()

    parameters = JSONField(default={})
    quad = JSONField(default=[])
    cols = JSONField(default=[])
    rows = JSONField(default=[])
    person_rows = JSONField(default=[])
    crosses = JSONField(default=[])
    boxes = JSONField(default=[])
    person_counts = JSONField(default=[])

    verified_time = models.DateTimeField(blank=True, null=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                    blank=True, null=True)

    @property
    def verified(self):
        return self.verified_time is not None

    def set_verified(self, verified_by):
        if verified_by is False:
            self.verified_time = None
            self.verified_by = None
        else:
            self.verified_time = timezone.now()
            self.verified_by = verified_by

    def get_image(self):
        try:
            return self._image
        except AttributeError:
            pass

        from tkweb.apps.regnskab.images.utils import load_pdf_page

        with self.sheet.image_file_name() as filename:
            self._image = load_pdf_page(filename, self.page - 1)

        return self._image

    def compute_person_counts(self):
        col_bounds = [0, 15, 21, 36]

        i = 0
        res = []
        for person_row_count in self.person_rows:
            j = i + person_row_count
            person_rows = self.crosses[i:j]
            groups = []
            for i, j in zip(col_bounds[:-1], col_bounds[1:]):
                group_rows = [r[i:j] for r in person_rows]
                crosses = box_crosses = 0
                for r in group_rows:
                    try:
                        x = next(i for i in range(len(r))
                                 if not r[len(r)-1-i])
                    except StopIteration:
                        x = 0
                    r_crosses = sum(r) - x
                    crosses += r_crosses
                    box_crosses += x
                groups.append([crosses, box_crosses/2])
            res.append(groups)
            i = j
        self.person_counts = res
