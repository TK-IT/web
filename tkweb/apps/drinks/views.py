from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.generic.edit import FormView
from django.urls import reverse

from tkweb.apps.drinks.forms import BarcardGenForm
from tkweb.apps.drinks.models import Barcard


class BarcardSelect(FormView):
    template_name = "drinks/home.html"
    form_class = BarcardGenForm

    def get_success_url(self):
        return reverse("drinks:generate")


def barcard_gen(request):
    if request.method == "POST":
        card = request.POST.get("barcard")
        card_obj = get_object_or_404(Barcard, id=card)
        card_obj.generate_files()
        return HttpResponseRedirect("/drinks/download/" + card)
    else:
        return HttpResponseRedirect("/drinks/")


def download(request, barcard_id):
    if request.method == "GET":
        barcard = get_object_or_404(Barcard, pk=barcard_id)
        return render(request, "drinks/download.html", {"barcard": barcard})
    else:
        return HttpResponseRedirect("/drinks/")
