from django.conf.urls import url
from tkweb.apps.idm import views


urlpatterns = [
    url(r'^gf/$', views.GfyearBestUpdate.as_view(), name='gfyear_best_update'),
]
