from django.contrib import admin
from regnskab.models import (
    Profile, Title, Alias, Payment, Sheet, PurchaseKind, SheetRow, Purchase,
    EmailTemplate, EmailBatch, Email,
)


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'email')


class TitleAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'profile', 'period', 'kind')


class AliasAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'profile', 'period', 'start_time', 'end_time')


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('profile', 'time', 'amount', 'note')


class SheetAdmin(admin.ModelAdmin):
    pass


class PurchaseKindAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'sheet', 'position')


class SheetRowAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'sheet', 'name', 'profile', 'position')


class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'row')


class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('subject', 'created_time')


class EmailBatchAdmin(admin.ModelAdmin):
    pass


class EmailAdmin(admin.ModelAdmin):
    pass


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Title, TitleAdmin)
admin.site.register(Alias, AliasAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Sheet, SheetAdmin)
admin.site.register(PurchaseKind, PurchaseKindAdmin)
admin.site.register(SheetRow, SheetRowAdmin)
admin.site.register(Purchase, PurchaseAdmin)
admin.site.register(EmailTemplate, EmailTemplateAdmin)
admin.site.register(EmailBatch, EmailBatchAdmin)
admin.site.register(Email, EmailAdmin)
