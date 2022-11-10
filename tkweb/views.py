from django.shortcuts import render
from tkweb.apps.idm.models import Profile, Title
from constance import config


def bestfu(request, **kwargs):
    period = config.GFYEAR
    if request.GET.get('y') == 'g':
        period -= 1
    best = Title.objects.filter(kind=Title.BEST,
                                period=period).select_related()
    if period == 2022 and config.GINKA_STANDIN_2022:
        best = [b for b in best if b.root != "INKA"]
    fu = Title.objects.filter(kind=Title.FU,
                              period=period).select_related()
    if request.GET.get('y') == 'g':
        best = list(best)
        fu = list(fu)
        for title in best + fu:
            title.period += 1
    context = {'best': best, 'fu': fu, }
    return render(request, 'bestfu.html', context)
