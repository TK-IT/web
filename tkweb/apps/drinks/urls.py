from django.conf.urls import url

from tkweb.apps.drinks.views import Home

urlpatterns = [
    url(r'^$', Home.as_view(), name='home'),
]
