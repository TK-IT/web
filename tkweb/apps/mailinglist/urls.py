from django.conf.urls import url
from tkweb.apps.mailinglist.views import (
    EmailFormView, EmailToRecipientsFormView, FileList, FileCreate,
)


urlpatterns = [
    url('^$', EmailFormView.as_view(), name='email_form'),
    url('^recipients/$', EmailToRecipientsFormView.as_view(), name='email_to_recipients_form'),
    url('^file/$', FileList.as_view(), name='file_list'),
    url('^file/upload/$', FileCreate.as_view(), name='file_create'),
]
