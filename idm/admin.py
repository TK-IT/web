from django.core import urlresolvers
from django.contrib import admin
from django.utils.html import format_html
from constance import config

from idm.models import (
    Profile, Group, tk_prefix,
    Title,
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


def period_display_prefix(period, name):
    second_half = (period + 1) % 100
    age = config.GFYEAR - period
    prefix = tk_prefix(age)
    return '%s%s %s/%02d' % (prefix, name, period, second_half)


class TitlePeriodFilter(admin.AllValuesFieldListFilter):
    def choices(self, cl):
        for choice in super().choices(cl):
            try:
                period = int(choice['display'])
            except ValueError:
                pass
            except TypeError:
                pass
            else:
                choice['display'] = period_display_prefix(period, 'BEST/FU')
            yield choice


class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'get_titles', 'get_email',
        'on_mailing_list', 'allow_direct_email',
    )
    list_filter = [MailingListFilter, 'allow_direct_email', 'gone']
    inlines = [ProfileTitleAdmin]

    def get_titles(self, profile):
        titles = list(profile.title_set.all())
        if titles:
            return ' '.join(sorted(t.display_title() for t in titles))

    get_titles.short_description = 'Titler'

    def get_email(self, profile):
        if profile.email:
            return format_html(
                '<a href="mailto:{}">{}</a>', profile.email, profile.email)

    get_email.short_description = 'Emailadresse'
    get_email.admin_order_field = 'email'

    def on_mailing_list(self, profile):
        return profile.groups.filter(regexp=Group.REGEXP_MAILING_LIST).exists()

    on_mailing_list.short_description = 'Hængerlisten'
    on_mailing_list.boolean = True


class GroupAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'regexp', 'matchtest',
    )


class TitleAdmin(admin.ModelAdmin):
    list_display = (
        'get_display_title', 'profile_link', 'period')
    list_filter = ['kind', TitleRootFilter, ('period', TitlePeriodFilter)]

    def profile_link(self, title):
        return format_html(
            '<a href="{}">{}</a>',
            urlresolvers.reverse('admin:idm_profile_change',
                                 args=(title.profile_id,)),
            title.profile)

    profile_link.short_description = 'Person'
    profile_link.admin_order_field = 'profile'

    def get_display_title(self, title):
        return title.display_title()

    get_display_title.short_description = 'Titel'


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Title, TitleAdmin)
