from django.conf.urls import url

from tkweb.apps.drinks.views import BarcardSelect, barcard_gen, download

urlpatterns = [
    url(r"^$", BarcardSelect.as_view(), name="home"),
    url(r"^generate/$", barcard_gen, name="generate"),
    url(r"^download/(?P<barcard_id>[0-9]+)/$", download, name="downloadList"),
]
