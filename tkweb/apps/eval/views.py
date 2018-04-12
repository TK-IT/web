from tkweb.apps.eval.models import WikiArticleTimeout
from django.shortcuts import render


def timeouts(request, **kwargs):
    wats = WikiArticleTimeout.objects.all()

    context = {
        'outdated': [wat for wat in wats if wat.outdated()],
        'nonoutdated': [wat for wat in wats if wat.outdated() is False],
        'notimeout': [wat for wat in wats if wat.outdated() is None],
    }

    return render(request, 'eval/timeouts.html', context)
