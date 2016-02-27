from django.contrib import admin

from idm.models import (
    Profile, Best, Group, tk_prefix,
    Title, GradGroupMembership,
)


class ProfileTitleAdmin(admin.TabularInline):
    model = Title


class ProfileGradGroupAdmin(admin.TabularInline):
    model = GradGroupMembership


class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'navn', 'title', 'email', 'accepteremail', 'accepterdirektemail',
    )
    inlines = [ProfileTitleAdmin, ProfileGradGroupAdmin]

    def title(self, profile):
        return ' '.join(
            sorted(t.display_title() for t in profile.title_set.all()))


class BestAdmin(admin.ModelAdmin):
    list_display = ('sortid', 'orgtitel', 'titel')


class GroupAdmin(admin.ModelAdmin):
    list_display = (
        'navn', 'type', 'regexp', 'matchtest', 'relativ'
    )


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Best, BestAdmin)
admin.site.register(Group, GroupAdmin)
