from django.conf.urls import url
from tkweb.apps.mailinglist.views import (
    EmailFormView, FileList, FileCreate,
)


urlpatterns = [
    url('^$', EmailFormView.as_view(), name='email_form'),
    url('^file/$', FileList.as_view(), name='file_list'),
    url('^file/upload/$', FileCreate.as_view(), name='file_create'),
]
