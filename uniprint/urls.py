from django.conf.urls import url

from uniprint.views import (
    Home, DocumentCreate, PrintoutCreate,
    DocumentList,
)

urlpatterns = [
    url(r'^$', Home.as_view(), name='home'),
    url(r'^upload/$', DocumentCreate.as_view(), name='document_create'),
    url(r'^print/$', PrintoutCreate.as_view(), name='printout_create'),
    url(r'^document/$', DocumentList.as_view(), name='document_list'),
    url(r'^document/(?P<username>\w+)/$',
        DocumentList.as_view(), name='document_list'),
]
