from django.contrib import admin

from idm.models import (
    Profile, Best,
)


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('navn', 'email', 'accepteremail', 'accepterdirektemail')


class BestAdmin(admin.ModelAdmin):
    list_display = ('sortid', 'orgtitel', 'titel')


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Best, BestAdmin)
