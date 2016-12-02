"""regnskab URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url

from regnskab.views import (
    Home, SessionCreate,
    SheetCreate, SheetDetail, SheetRowUpdate,
    EmailTemplateList, EmailTemplateUpdate, EmailTemplateCreate,
    SessionList, SessionUpdate, EmailList, EmailDetail, EmailSend,
    PaymentBatchCreate, PurchaseNoteList, PurchaseBatchCreate,
    ProfileList, ProfileDetail, PaymentPurchaseList,
    BalancePrint,
)

urlpatterns = [
    url(r'^$', Home.as_view(), name='home'),
    url(r'^session/(?P<session>\d+)/sheet/new/$', SheetCreate.as_view(),
        name='sheet_create'),
    url(r'^sheet/(?P<pk>\d+)/$', SheetDetail.as_view(), name='sheet_detail'),
    url(r'^sheet/(?P<pk>\d+)/edit/$', SheetRowUpdate.as_view(), name='sheet_update'),
    url(r'^template/$', EmailTemplateList.as_view(),
        name='email_template_list'),
    url(r'^template/(?P<pk>\d+)/$', EmailTemplateUpdate.as_view(),
        name='email_template_update'),
    url(r'^template/new/$', EmailTemplateCreate.as_view(),
        name='email_template_create'),
    url(r'^session/$', SessionList.as_view(),
        name='session_list'),
    url(r'^session/new/$', SessionCreate.as_view(),
        name='session_create'),
    url(r'^session/(?P<pk>\d+)/$', SessionUpdate.as_view(),
        name='session_update'),
    url(r'^session/(?P<pk>\d+)/email/$', EmailList.as_view(),
        name='email_list'),
    url(r'^session/(?P<pk>\d+)/email/send/$',
        EmailSend.as_view(), name='email_send'),
    url(r'^session/(?P<pk>\d+)/email/(?P<profile>\d+)/$', EmailDetail.as_view(),
        name='email_detail'),
    url(r'^session/(?P<pk>\d+)/email/(?P<profile>\d+)/send/$',
        EmailSend.as_view(), name='email_send'),
    url(r'^session/(?P<pk>\d+)/payment/$', PaymentBatchCreate.as_view(),
        name='payment_batch_create'),
    url(r'^session/(?P<pk>\d+)/other/$', PurchaseNoteList.as_view(),
        name='purchase_note_list'),
    url(r'^session/(?P<pk>\d+)/other/add/$', PurchaseBatchCreate.as_view(),
        name='purchase_batch_create'),
    url(r'^session/(?P<pk>\d+)/purchases/$', PaymentPurchaseList.as_view(),
        name='payment_purchase_list'),
    url(r'^session/(?P<pk>\d+)\.(?P<ext>tex)$', BalancePrint.as_view(),
        name='balance_print_tex'),
    url(r'^session/(?P<pk>\d+)\.(?P<ext>pdf)$', BalancePrint.as_view(),
        name='balance_print_pdf'),
    url(r'^profile/$', ProfileList.as_view(),
        name='profile_list'),
    url(r'^profile/(?P<pk>\d+)/$', ProfileDetail.as_view(),
        name='profile_detail'),
]
