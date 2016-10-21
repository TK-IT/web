# encoding: utf8
from django.contrib import admin
from django.db import models
from django.conf.urls import url
from django.views.generic import RedirectView


class MailinglistAdmin(admin.ModelAdmin):
    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.module_name
        return [
            url(r'^add/$',
                RedirectView.as_view(url='/email/', permanent=False),
                name='%s_%s_add' % info),
        ]

    def has_add_permission(self, request, obj=None):
        return request.user.has_perm('mailinglist.send')

    def has_delete_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, *args, **kwargs):
        return False


class Email(object):
    class Meta:
        app_label = 'mailinglist'
        object_name = 'Email'
        model_name = module_name = 'email'
        verbose_name = verbose_name_plural = 'Email til hængerlisten'
        abstract = False
        swapped = False

        def get_ordered_objects(self):
            return False

        def get_change_permission(self):
            return 'change_%s' % self.model_name

    _meta = Meta()


admin.site.register([Email], MailinglistAdmin)
