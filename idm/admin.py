from django.contrib import admin

from idm.models import (
    Profile, Group, tk_prefix,
    Title,
)


class ProfileTitleAdmin(admin.TabularInline):
    model = Title


class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'navn', 'get_titles', 'email', 'accepteremail', 'accepterdirektemail',
    )
    inlines = [ProfileTitleAdmin]

    def get_titles(self, profile):
        return ' '.join(
            sorted(t.display_title() for t in profile.title_set.all()))

    get_titles.short_description = 'Titles'


class GroupAdmin(admin.ModelAdmin):
    list_display = (
        'navn', 'regexp', 'matchtest',
    )


class TitleAdmin(admin.ModelAdmin):
    list_display = (
        '__str__', 'profile', 'period', 'root', 'kind', 'display_title')


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Title, TitleAdmin)
