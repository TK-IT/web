from django.conf.urls import url

from tkweb.apps.drinks.views import BarcardSelect, barcardGen

urlpatterns = [
    url(r'^$', BarcardSelect.as_view(), name='home'),
    url(r'^download/$', barcardGen, name='download'),
]
