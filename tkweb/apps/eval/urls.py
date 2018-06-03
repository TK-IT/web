from django.conf.urls import url
from django.views.generic.base import RedirectView
from django_nyt.urls import get_pattern as get_nyt_pattern
from wiki.urls import get_pattern as get_wiki_pattern
import tkweb.apps.eval.views

urlpatterns = [
    url(
        r"^$",
        RedirectView.as_view(url="/eval/wiki/", permanent=False),
        name="evalindex",
    ),
    # django-wiki urls
    url(r"wiki/", get_wiki_pattern()),
    url(r"notifications/", get_nyt_pattern()),
    # Other urls
    url(r"^timeouts/$", tkweb.apps.eval.views.timeouts, name="eval_timeouts"),
]
