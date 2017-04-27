class KrydslisteSite(object):
    name = 'krydsliste'

    def get_urls(self):
        from django.conf import settings
        from django.conf.urls import url
        from krydsliste.views import (
            SheetList, SheetCreate, SheetUpdate, Print,
        )

        urls = [
            url(r'^$', SheetList.as_view(), name='sheet_list'),
            url(r'^new/$', SheetCreate.as_view(), name='sheet_create'),
            url(r'^(?P<pk>\d+)/$', SheetUpdate.as_view(), name='sheet_update'),
            url(r'^(?P<pk>\d+)/print/$', Print.as_view(), name='print'),
        ]
        return urls

    @property
    def urls(self):
        return self.get_urls(), 'regnskab', self.name


site = KrydslisteSite()
