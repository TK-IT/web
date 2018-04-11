from tkweb.apps.eval.models import WikiArticleTimeout
from django.shortcuts import render


def timeouts(request, **kwargs):
    wats = WikiArticleTimeout.objects.all()
    context = {'wats': wats,
    }

    return render(request, 'eval/timeouts.html', context)
