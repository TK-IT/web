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
from django.contrib import admin

from regnskab.views import SheetCreate, SheetDetail, SheetRowUpdate

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^sheet/new/$', SheetCreate.as_view(), name='sheet_create'),
    url(r'^sheet/(?P<pk>\d+)/$', SheetDetail.as_view(), name='sheet'),
    url(r'^sheet/(?P<pk>\d+)/edit/$', SheetRowUpdate.as_view(), name='sheet_update'),
]
