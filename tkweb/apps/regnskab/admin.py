from django.utils import timezone
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from tkweb.apps.regnskab.models import (
    Alias,
    Transaction,
    Sheet,
    EmailTemplate,
    Session,
    SheetImage,
    Newsletter,
)


class AliasAdmin(admin.ModelAdmin):
    list_display = ("__str__", "profile", "period", "start_time", "end_time")

    def get_fields(self, request, obj=None):
        if obj and obj.pk:
            # Modifying an existing
            return ("profile", "root", "start_time", "end_time", "created_by", "period")
        else:
            # Creating a new
            return ("profile", "root")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
            obj.start_time = timezone.now()
        obj.save()


class TransactionAdmin(admin.ModelAdmin):
    list_display = ("profile", "kind", "time", "amount", "note")

    def has_change_permission(self, request, obj=None):
        if obj and (not obj.session_id or obj.session.sent):
            return False
        return True

    has_delete_permission = has_change_permission


class SheetAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        if obj and (not obj.session_id or obj.session.sent):
            return False
        return True

    has_delete_permission = has_change_permission


class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ("subject", "created_time")


class SessionAdmin(admin.ModelAdmin):
    list_display = ("item_link", "send_time", "period", "created_by", "email_template")
    list_display_links = []

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        if obj and obj.sent:
            return False
        return True

    has_delete_permission = has_change_permission

    def item_link(self, obj):
        if obj.sent:
            return "Udsendt %s" % (obj.send_time,)
        text = "Oprettet %s" % (obj.created_time,)
        url = reverse("admin:regnskab_session_change", args=(obj.pk,))
        return format_html('<a href="{}">{}</a>', url, text)

    item_link.verbose_name = "Opgørelse"


class SheetImageAdmin(admin.ModelAdmin):
    pass


class NewsletterAdmin(admin.ModelAdmin):
    list_display = ("subject", "send_time", "period", "created_by")

    def subject(self, obj):
        return obj.email_template.subject

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        if obj and obj.sent:
            return False
        return True


admin.site.register(Alias, AliasAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Sheet, SheetAdmin)
admin.site.register(EmailTemplate, EmailTemplateAdmin)
admin.site.register(Session, SessionAdmin)
admin.site.register(SheetImage, SheetImageAdmin)
admin.site.register(Newsletter, NewsletterAdmin)
