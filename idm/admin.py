from django.contrib import admin

from idm.models import (
    Profile, Best,
    Title, GradGroupMembership,
)


class ProfileTitleAdmin(admin.TabularInline):
    model = Title


class ProfileGradGroupAdmin(admin.TabularInline):
    model = GradGroupMembership


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('navn', 'email', 'accepteremail', 'accepterdirektemail')
    inlines = [ProfileTitleAdmin, ProfileGradGroupAdmin]


class BestAdmin(admin.ModelAdmin):
    list_display = ('sortid', 'orgtitel', 'titel')


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Best, BestAdmin)
