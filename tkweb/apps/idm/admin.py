# encoding: utf8
from django import forms
from django.urls import reverse
from django.db.models import Q
from django.contrib import admin
from django.utils.html import format_html
from constance import config
import tktitler as tk

from tkweb.apps.idm.models import (
    Profile, Group, Title,
)


class ProfileTitleAdmin(admin.TabularInline):
    model = Title


class MailingListFilter(admin.SimpleListFilter):
    title = 'Hængerlisten'
    parameter_name = 'on_mailing_list'

    def lookups(self, request, model_admin):
        return (
            ('1', 'Ja'),
            ('0', 'Nej'),
        )

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(groups__regexp=Group.REGEXP_MAILING_LIST)
        if self.value() == '0':
            return queryset.exclude(groups__regexp=Group.REGEXP_MAILING_LIST)


class EmailAddressFilter(admin.SimpleListFilter):
    title = 'Email-udbyder'
    parameter_name = 'email_address'

    def domains(self):
        return [
            ('AU', 'au', ['.au.dk', 'inano.dk', 'iha.dk', 'asb.dk']),
            ('Google', 'google', ['gmail.com']),
            ('Hotmail', 'hotmail',
             'live.dk live.com hotmail.dk hotmail.com msn.com'.split()),
            # ('Yahoo', 'yahoo', 'yahoo.com yahoo.dk'.split()),
            # ('Skolekom', 'skolekom', ['skolekom.dk']),
            # ('Apple', 'apple', 'me.com icloud.com'.split()),
            ('TDC', 'tdc', '.mail.dk .tdc.dk .tele.dk tdcadsl.dk'.split()),
        ]

    def lookups(self, request, model_admin):
        for label, key, domains in self.domains():
            yield (key, label)
        yield ('others', 'Andre')
        yield ('empty', '(Ingen)')

    def match_domains(self, domains):
        o = []
        for d in domains:
            if d.startswith('.'):
                o.append(Q(email__iendswith=d) | Q(email__iendswith='@'+d[1:]))
            else:
                o.append(Q(email__iendswith='@'+d))
        r = o[0]
        for q in o[1:]:
            r = r | q
        return r

    def queryset(self, request, queryset):
        v = self.value()
        if v == 'empty':
            return queryset.filter(email='')
        for label, key, domains in self.domains():
            if v == key:
                return queryset.filter(self.match_domains(domains))
            elif v == 'others':
                queryset = queryset.exclude(self.match_domains(domains))
        if v == 'others':
            queryset = queryset.exclude(email='')
        return queryset


class TitleRootFilter(admin.SimpleListFilter):
    title = 'Titel'
    parameter_name = 'title'

    def lookups(self, request, model_admin):
        values = self._values()
        tr = dict(KASS='KA$$')
        return [(v, tr.get(v, v)) for v in values]

    def _values(self):
        eight = 'CERM FORM INKA KASS NF PR SEKR VC'.split()
        fu = 'FUAN EFUIT'.split()
        old = 'TVC BEST'.split()
        return eight + fu + old

    def queryset(self, request, queryset):
        if self.value() in self._values():
            return queryset.filter(root=self.value())


class TitlePeriodFilter(admin.AllValuesFieldListFilter):
    def choices(self, cl):
        gfyear = config.GFYEAR
        for choice in super(TitlePeriodFilter, self).choices(cl):
            try:
                period = int(choice['display'])
            except ValueError:
                pass
            except TypeError:
                pass
            else:
                choice['display'] = tk.prepostfix(
                    ('BEST/FU', period), gfyear=gfyear,
                    prefixtype='unicode')
            yield choice


class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'get_titles', 'get_email',
        'on_mailing_list', 'allow_direct_email',
    )
    list_filter = [MailingListFilter, 'allow_direct_email', 'gone', 'groups',
                   EmailAddressFilter]
    inlines = [ProfileTitleAdmin]
    search_fields = ['name', 'email']
    filter_horizontal = ['groups']

    def get_queryset(self, request):
        qs = super(ProfileAdmin, self).get_queryset(request)
        qs = qs.prefetch_related('title_set', 'groups')
        return qs

    def get_titles(self, profile):
        titles = list(profile.title_set.all())
        if titles:
            with tk.set_gfyear(config.GFYEAR):
                return ', '.join(sorted(tk.prepostfix(t, prefixtype="unicode")
                                        for t in titles))

    get_titles.short_description = 'Titler'

    def get_email(self, profile):
        if profile.email:
            return format_html(
                '<a href="mailto:{}">{}</a>', profile.email, profile.email)

    get_email.short_description = 'Emailadresse'
    get_email.admin_order_field = 'email'

    def on_mailing_list(self, profile):
        return any(g.regexp == Group.REGEXP_MAILING_LIST
                   for g in profile.groups.all())

    on_mailing_list.short_description = 'Hængerlisten'
    on_mailing_list.boolean = True


class GroupAdminForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'regexp', 'matchtest']

    members = forms.ModelMultipleChoiceField(
        Profile.objects.all(),
        widget=admin.widgets.FilteredSelectMultiple('personer', False),
        required=False,
        label='Medlemmer',
    )

    def __init__(self, *args, **kwargs):
        super(GroupAdminForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            qs = self.instance.profile_set.all()
            self.initial['members'] = qs.values_list('pk', flat=True)


class GroupAdmin(admin.ModelAdmin):
    form = GroupAdminForm

    list_display = (
        'name', 'regexp', 'matchtest', 'members',
    )

    def members(self, group):
        return group.profile_set.count() or None

    members.short_description = 'Medlemmer'

    def save_model(self, request, obj, form, change):
        """
        Override save_model to also update Group.profile_set.
        """
        # Based on http://stackoverflow.com/a/21480139/1570972
        super(GroupAdmin, self).save_model(request, obj, form, change)
        obj.profile_set.clear()
        obj.profile_set.add(*form.cleaned_data['members'])


class TitleAdmin(admin.ModelAdmin):
    list_display = (
        'get_display_title', 'profile_link', 'get_period', 'get_email')
    list_filter = ['kind', TitleRootFilter, ('period', TitlePeriodFilter)]
    list_select_related = ['profile']
    search_fields = ['profile__name']

    def profile_link(self, title):
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:idm_profile_change',
                    args=(title.profile_id,)),
            title.profile)

    profile_link.short_description = 'Person'
    profile_link.admin_order_field = 'profile'

    def get_email(self, title):
        profile = title.profile
        if profile.email:
            return format_html(
                '<a href="mailto:{}">{}</a>', profile.email, profile.email)

    get_email.short_description = 'Emailadresse'
    get_email.admin_order_field = 'profile__email'

    def get_display_title(self, title):
        return tk.prepostfix(title, config.GFYEAR, prefixtype='unicode')

    get_display_title.short_description = 'Titel'

    def get_period(self, title):
        return tk.prepostfix(
            (title.get_kind_display(), title.period),
            config.GFYEAR,
            prefixtype='unicode')

    get_period.short_description = 'Årgang'
    get_period.admin_order_field = 'period'


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Title, TitleAdmin)
