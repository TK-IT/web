from django.contrib import admin
from regnskab.models import (
    Profile, Title, Alias, Sheet, PurchaseKind, SheetRow, Purchase,
)


class ProfileAdmin(admin.ModelAdmin):
    pass


class TitleAdmin(admin.ModelAdmin):
    pass


class AliasAdmin(admin.ModelAdmin):
    pass


class SheetAdmin(admin.ModelAdmin):
    pass


class PurchaseKindAdmin(admin.ModelAdmin):
    pass


class SheetRowAdmin(admin.ModelAdmin):
    pass


class PurchaseAdmin(admin.ModelAdmin):
    pass


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Title, TitleAdmin)
admin.site.register(Alias, AliasAdmin)
admin.site.register(Sheet, SheetAdmin)
admin.site.register(PurchaseKind, PurchaseKindAdmin)
admin.site.register(SheetRow, SheetRowAdmin)
admin.site.register(Purchase, PurchaseAdmin)
