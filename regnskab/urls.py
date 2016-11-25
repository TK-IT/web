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
    Home,
    SheetCreate, SheetDetail, SheetRowUpdate,
    EmailTemplateList, EmailTemplateUpdate, EmailTemplateCreate,
    SessionList, SessionUpdate, EmailList, EmailDetail,
    PaymentBatchCreate,
    ProfileList, ProfileDetail,
)

urlpatterns = [
    url(r'^$', Home.as_view(), name='home'),
    url(r'^session/(?P<session>\d+)/sheet/new/$', SheetCreate.as_view(),
        name='sheet_create'),
    url(r'^sheet/(?P<pk>\d+)/$', SheetDetail.as_view(), name='sheet'),
    url(r'^sheet/(?P<pk>\d+)/edit/$', SheetRowUpdate.as_view(), name='sheet_update'),
    url(r'^template/$', EmailTemplateList.as_view(),
        name='email_template_list'),
    url(r'^template/(?P<pk>\d+)/$', EmailTemplateUpdate.as_view(),
        name='email_template_update'),
    url(r'^template/new/$', EmailTemplateCreate.as_view(),
        name='email_template_create'),
    url(r'^session/$', SessionList.as_view(),
        name='session_list'),
    url(r'^session/(?P<pk>\d+)/$', SessionUpdate.as_view(),
        name='session_update'),
    url(r'^session/(?P<pk>\d+)/email/$', EmailList.as_view(),
        name='email_list'),
    url(r'^session/(?P<pk>\d+)/email/(?P<profile>\d+)/$', EmailDetail.as_view(),
        name='email_detail'),
    url(r'^session/(?P<pk>\d+)/payment/$', PaymentBatchCreate.as_view(),
        name='payment_batch_create'),
    url(r'^profile/$', ProfileList.as_view(),
        name='profile_list'),
    url(r'^profile/(?P<pk>\d+)/$', ProfileDetail.as_view(),
        name='profile_detail'),
]
