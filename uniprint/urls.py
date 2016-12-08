from django.conf.urls import url

from uniprint.views import (
    Home, DocumentCreate, PrintoutCreate,
)

urlpatterns = [
    url(r'^$', Home.as_view()),
    url(r'^upload/$', DocumentCreate.as_view()),
    url(r'^print/$', PrintoutCreate.as_view()),
]
