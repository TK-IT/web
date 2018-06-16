from django.shortcuts import render
from tkweb.apps.idm.models import Profile, Title
from constance import config


def bestfu(request, **kwargs):
    best = Title.objects.filter(kind=Title.BEST,
                                period=config.GFYEAR).select_related()
    fu = Title.objects.filter(kind=Title.FU,
                              period=config.GFYEAR).select_related()
    context = {'best': best, 'fu': fu, }
    return render(request, 'bestfu.html', context)
