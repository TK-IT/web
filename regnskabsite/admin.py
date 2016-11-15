from django.contrib import admin
from regnskab.models import Profile, Title


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'email')


class TitleAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'profile', 'period', 'kind')


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Title, TitleAdmin)
