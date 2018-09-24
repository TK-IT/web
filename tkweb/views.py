from django.shortcuts import render
from tkweb.apps.idm.models import Profile, Title
from constance import config


def bestfu(request, **kwargs):
    period = config.GFYEAR
    if request.GET.get('y') == 'g':
        period -= 1
    best = Title.objects.filter(kind=Title.BEST,
                                period=period).select_related()
    fu = Title.objects.filter(kind=Title.FU,
                              period=period).select_related()
    context = {'best': best, 'fu': fu, }
    return render(request, 'bestfu.html', context)
