from django.utils import timezone
from django.contrib import admin
from regnskab.models import Alias, Transaction, Sheet, EmailTemplate, Session


class AliasAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'profile', 'period', 'start_time', 'end_time')

    def get_fields(self, request, obj=None):
        if obj and obj.pk:
            # Modifying an existing
            return ('profile', 'root', 'start_time', 'end_time',
                    'created_by', 'period')
        else:
            # Creating a new
            return ('profile', 'root')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
            obj.start_time = timezone.now()
        obj.save()


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('profile', 'kind', 'time', 'amount', 'note')


class SheetAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False


class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('subject', 'created_time')


class SessionAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False


admin.site.register(Alias, AliasAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Sheet, SheetAdmin)
admin.site.register(EmailTemplate, EmailTemplateAdmin)
admin.site.register(Session, SessionAdmin)
