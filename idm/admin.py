from django.contrib import admin

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


class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'get_titles', 'email', 'on_mailing_list', 'allow_direct_email',
    )
    list_filter = [MailingListFilter, 'allow_direct_email', 'gone']
    inlines = [ProfileTitleAdmin]

    def get_titles(self, profile):
        return ' '.join(
            sorted(t.display_title() for t in profile.title_set.all()))

    get_titles.short_description = 'Titler'

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
        '__str__', 'profile', 'period', 'root', 'kind', 'display_title')

    list_filter = ['kind', 'period']


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Title, TitleAdmin)
