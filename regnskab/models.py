import re
import heapq
import itertools
from collections import namedtuple, defaultdict
from decimal import Decimal

from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.db import models
from django.db.models import F
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import EmailMessage


def _import_profile_title():
    try:
        module_name = settings.TKWEB_IDM_MODULE
    except AttributeError:
        raise ImproperlyConfigured('settings must define TKWEB_IDM_MODULE')

    models_module = module_name + '.models'
    import importlib
    try:
        module = importlib.import_module(models_module)
    except ImportError:
        raise ImproperlyConfigured(
            models_module + ' is not a module that can be imported')

    try:
        return (module.Profile, module.Title, module.tk_prefix, module.config,
                module.parse_bestfu_alias)
    except AttributeError:
        raise ImproperlyConfigured(
            models_module + ' must define Profile, Title, tk_prefix, ' +
            'config, parse_bestfu_alias')


Profile, Title, tk_prefix, config, parse_bestfu_alias = _import_profile_title()


def get_inka():
    try:
        return Profile.objects.get(title__root='INKA',
                                   title__period=config.GFYEAR)
    except Profile.DoesNotExist:
        return Profile()


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


class Alias(models.Model):
    profile = models.ForeignKey(Profile)
    period = models.IntegerField(blank=True, null=True, verbose_name='Årgang')
    root = models.CharField(max_length=200, verbose_name='Titel')
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=False)
    created_time = models.DateTimeField(auto_now_add=True)

    def age(self, gfyear=None):
        if gfyear is None:
            gfyear = config.GFYEAR
        return gfyear - self.period

    def display_root(self):
        return self.root

    def display_title(self, gfyear=None):
        if self.period is None:
            return self.root
        return '%s%s' % (tk_prefix(self.age(gfyear)), self.display_root())

    def input_title(self, gfyear=None):
        # The title as it would be typed
        if self.period is None:
            return self.root
        return '%s%s' % (tk_prefix(self.age(gfyear), sup_fn=str), self.root)

    class Meta:
        ordering = ['period', 'root']
        verbose_name = 'alias'
        verbose_name_plural = verbose_name + 'er'

    def __str__(self):
        return self.display_title()


class Payment(models.Model):
    session = models.ForeignKey('Session', on_delete=models.SET_NULL,
                                null=True, blank=False)
    profile = models.ForeignKey(Profile)
    time = models.DateTimeField()
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    note = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=False)
    created_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%.2f kr.' % self.amount


def get_primary_titles(title_qs=None, period=None):
    if title_qs is None:
        title_qs = Title.objects.all()
    if period is not None:
        period = config.GFYEAR
    title_qs = title_qs.filter(period__lte=period)
    title_qs = title_qs.exclude(root='EFUIT', period__lt=period)
    title_qs = title_qs.order_by('period')
    titles = {}
    for t in title_qs:
        # Override older titles
        titles[t.profile_id] = t
    return titles


class Sheet(models.Model):
    session = models.ForeignKey('Session', on_delete=models.SET_NULL,
                                null=True, blank=False)
    name = models.CharField(max_length=200, blank=True,
                            help_text='f.eks. HSTR, revy, matlabotanisk have')
    start_date = models.DateField()
    end_date = models.DateField()
    period = models.IntegerField(verbose_name='Årgang')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=False)
    created_time = models.DateTimeField(auto_now_add=True)

    def rows(self):
        result = []
        kinds = list(self.purchasekind_set.all())
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
            result.append(dict(
                id=row.id,
                profile=row.profile,
                position=row.position,  # needed?
                name=row.name,
                kinds=purchase_list,
            ))
        profile_ids = set(row['profile'] for row in result)
        titles = get_primary_titles(
            Title.objects.filter(profile_id__in=profile_ids),
            self.period)

        for row in result:
            try:
                title = row['title'] = titles[row['profile'].id]
            except KeyError:
                title = row['title'] = None
                continue
            row['display_title'] = title.display_title(self.period)

        if self.legacy_style():
            # Sort rows by title, period
            def key(row):
                return (row['title'] is None,
                        row['title'] and (-row['title'].period,
                                          row['title'].kind,
                                          row['title'].root))

            result.sort(key=key)
        return result

    def legacy_style(self):
        try:
            return self._legacy_style
        except AttributeError:
            self._legacy_style = (len(self.purchasekind_set.all()) == 4)
            return self._legacy_style

    class Meta:
        ordering = ['start_date']
        verbose_name = 'krydsliste'
        verbose_name_plural = verbose_name + 'r'

    def __str__(self):
        s = '%s %s-%s' % (self.name, self.start_date, self.end_date)
        return s.strip()


class PurchaseKind(models.Model):
    sheet = models.ForeignKey(Sheet)
    position = models.PositiveIntegerField()
    name = models.CharField(max_length=200,
                            help_text='f.eks. guldøl, guldølskasser')
    price = models.DecimalField(max_digits=12, decimal_places=2,
                                help_text='f.eks. 8, 10, 13, 200, 250')

    @property
    def short_name(self):
        if self.name.endswith('kasse'):
            return 'ks'
        return self.name

    class Meta:
        ordering = ['sheet', 'position']
        verbose_name = 'prisklasse'
        verbose_name_plural = verbose_name + 'r'

    def __str__(self):
        return str(self.name)


class SheetRow(models.Model):
    sheet = models.ForeignKey(Sheet)
    position = models.PositiveIntegerField()
    name = models.CharField(max_length=200, blank=False, null=True)
    profile = models.ForeignKey(Profile, blank=False, null=True)

    class Meta:
        ordering = ['sheet', 'position']
        verbose_name = 'krydslisteindgang'
        verbose_name_plural = verbose_name + 'e'

    def __str__(self):
        return self.name or str(self.profile)


class Purchase(models.Model):
    row = models.ForeignKey(SheetRow)
    kind = models.ForeignKey(PurchaseKind)
    count = models.DecimalField(max_digits=9, decimal_places=4,
                                help_text='antal krydser eller brøkdel')

    def __str__(self):
        return '%g× %s' % (self.count, self.kind)

    class Meta:
        ordering = ['row', 'kind']
        verbose_name = 'krydser'
        verbose_name_plural = verbose_name


def compute_balance(profile_ids=None):
    balance = defaultdict(Decimal)
    purchase_qs = Purchase.objects.all()
    if profile_ids:
        purchase_qs = purchase_qs.filter(row__profile_id__in=profile_ids)
    purchase_qs = purchase_qs.annotate(profile_id=F('row__profile_id'))
    purchase_qs = purchase_qs.annotate(amount=F('count') * F('kind__price'))
    purchase_qs = purchase_qs.values_list('profile_id', 'amount')
    for profile, amount in purchase_qs:
        balance[profile] += amount
    payment_qs = Payment.objects.all()
    if profile_ids:
        payment_qs = payment_qs.filter(profile_id__in=profile_ids)
    payment_qs = payment_qs.values_list('profile_id', 'amount')
    for profile, amount in payment_qs:
        balance[profile] -= amount
    return balance


class EmailTemplate(models.Model):
    POUND = 'pound'
    FORMAT = [(POUND, 'pound')]

    name = models.CharField(max_length=255, blank=True)
    subject = models.TextField(blank=False)
    body = models.TextField(blank=False)
    format = models.CharField(max_length=10, choices=FORMAT)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=False)
    created_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or str(self.created_time)


def format(template, context):
    return re.sub(r'#([^#]*)#', lambda mo: context[mo.group(1)], template)


Balance = namedtuple('Balance', 'profile_id amount'.split())


class Session(models.Model):
    email_template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL,
                                       null=True, blank=False)
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
        if self.email_template is None:
            raise ValidationError("template required to generate emails")

        profiles = Profile.objects.all().annotate(profile_id=F('id'))
        profiles = profiles.order_by('profile_id')
        balances = compute_balance()
        balances = [Balance(profile_id=i, amount=a)
                    for i, a in balances.items()]
        balances.sort(key=lambda o: o.profile_id)
        titles = get_primary_titles(period=self.period)
        titles = sorted(titles.values(), key=lambda o: o.profile_id)

        payments = self.payment_set.all()
        payments = payments.order_by('profile_id')

        kind_qs = PurchaseKind.objects.filter(sheet__session=self)
        kind_qs = kind_qs.order_by('name', 'price')
        kind_groups = itertools.groupby(kind_qs, key=lambda k: k.name)
        kind_price = {n: set(k.price for k in g)
                      for n, g in kind_groups}

        purchases = Purchase.objects.filter(
            row__sheet__session=self)
        purchases = purchases.annotate(
            profile_id=F('row__profile_id'),
            amount=F('count')*F('kind__price'),
            name=F('kind__name'),
            price=F('kind__price'))
        purchases = purchases.order_by('profile_id', 'name')

        emails = Email.objects.filter(session=self)
        emails = emails.order_by('profile_id')

        data = heapq.merge(profiles, payments, purchases, emails, balances,
                           titles, key=lambda o: o.profile_id)
        data_by_profile = itertools.groupby(data, key=lambda o: o.profile_id)

        for profile_id, profile_data in data_by_profile:
            self.regenerate_email(
                kind_price, profile_data)

    def regenerate_email(self, kind_price, data_iterable):
        payment_sum = 0
        other_sum = 0
        purchase_count = defaultdict(Decimal)
        existing_email = None
        primary_title = None
        balance = 0
        profile = None

        for o in data_iterable:
            if isinstance(o, Payment):
                if o.amount > 0:
                    payment_sum += o.amount
                else:
                    other_sum -= o.amount
            elif isinstance(o, Email):
                assert existing_email is None
                existing_email = o
            elif isinstance(o, Purchase):
                purchase_count[o.name] += o.count
            elif isinstance(o, Title):
                assert primary_title is None
                primary_title = o
            elif isinstance(o, Balance):
                balance = o.amount
            elif isinstance(o, Profile):
                profile = o
            else:
                raise TypeError(type(o))

        activity = (balance > 0 or any(purchase_count.values()) or
                    payment_sum or other_sum)
        if not activity or not profile.email:
            if existing_email:
                existing_email.delete()
            return

        kasse_count = purchase_count['ølkasse']
        if 'guldølkasse' in purchase_count:
            guld_ratio = (next(iter(kind_price['guldølkasse'])) /
                          next(iter(kind_price['ølkasse'])))
            kasse_count += guld_ratio * purchase_count['guldølkasse']
        if 'sodavandkasse' in purchase_count:
            vand_ratio = (next(iter(kind_price['sodavandkasse'])) /
                          next(iter(kind_price['ølkasse'])))
            kasse_count += vand_ratio * purchase_count['sodavandkasse']

        if primary_title:
            title = primary_title.display_title(self.period)
        else:
            title = None

        def format_price(p):
            return ('%.2f' % p).replace('.', ',')

        def format_price_set(ps):
            return '/'.join(map(format_price, sorted(ps)))

        def format_count(c):
            return ('%.2f' % c).rstrip('0').rstrip('.').replace('.', ',')

        context = {
            'TITEL ': title + ' ' if title else '',
            'NAVN': profile.name,
            'BETALT': format_price(payment_sum),
            'POEL': format_price_set(kind_price.get('øl', ())),
            'PVAND': format_price_set(kind_price.get('sodavand', ())),
            'PGULD': format_price_set(kind_price.get('guldøl', ())),
            'PKASSER': format_price_set(kind_price.get('ølkasse', ())),
            'GAELD': format_price(balance),
            'MAXGAELD': format_price(250),  # TODO make this configurable
            'OEL': format_count(purchase_count.get('øl', 0)),
            'VAND': format_count(purchase_count.get('sodavand', 0)),
            'GULD': format_count(purchase_count.get('guldøl', 0)),
            'KASSER': format_count(kasse_count),
            'INKA': get_inka().name,
        }

        email_fields = ('subject', 'body', 'recipient_name', 'recipient_email')
        email = Email(
            session=self,
            profile=profile,
            subject=format(self.email_template.subject, context),
            body=format(self.email_template.body, context),
            recipient_name=profile.name,
            recipient_email=profile.email,
        )
        if existing_email:
            changed = any(getattr(email, k) != getattr(existing_email, k)
                          for k in email_fields)
            if changed:
                email.pk = existing_email.pk
            else:
                return
        email.save()


class Email(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.SET_NULL,
                                null=True, blank=False, related_name='+')
    subject = models.TextField(blank=False)
    body = models.TextField(blank=False)
    recipient_name = models.CharField(max_length=255)
    recipient_email = models.CharField(max_length=255)

    def __str__(self):
        return '%s <%s>' % (self.recipient_name, self.recipient_email)

    def to_message(self):
        headers = {
            'From': 'INKA@TAAGEKAMMERET.dk',
        }
        return EmailMessage(
            subject=self.subject,
            body=self.body,
            from_email='admin@TAAGEKAMMERET.dk',
            reply_to=['INKA@TAAGEKAMMERET.dk'],
            to=['%s <%s>' % (self.recipient_name, self.recipient_email)],
            headers=headers)
