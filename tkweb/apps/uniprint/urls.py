from django.conf.urls import url

from uniprint.views import (
    Home, DocumentCreate, PrintoutCreate,
    DocumentList, PrintoutList,
)

urlpatterns = [
    url(r'^$', Home.as_view(), name='home'),
    url(r'^upload/$', DocumentCreate.as_view(), name='document_create'),
    url(r'^print/$', PrintoutCreate.as_view(), name='printout_create'),
    url(r'^document/$', DocumentList.as_view(), name='document_list'),
    url(r'^document/(?P<username>\w+)/$',
        DocumentList.as_view(), name='document_list'),
    url(r'^printout/$', PrintoutList.as_view(), name='printout_list'),
    url(r'^printout/(?P<username>\w+)/$',
        PrintoutList.as_view(), name='printout_list'),
]
