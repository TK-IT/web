from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, ListView
from django.views.generic.edit import FormView

from django.core.files.storage import FileSystemStorage
from django.core.files import File

from .forms import BarcardGenForm
from .models import Barcard
import subprocess

class BarcardSelect(FormView):
    template_name = 'drinks/home.html'
    form_class = BarcardGenForm
    success_url = 'generate/'

    def form_valid(self, form):
        return super().form_valid(form)

def barcardGen(request):
    if request.method =='POST':
        card = request.POST.get('barcard')
        card_obj = Barcard.objects.get(id=card)
        barcardName = card_obj.name
        card_obj.generateFiles()
        return HttpResponseRedirect('/drinks/download/'+card)
    else:
        return HttpResponseRedirect('/drinks/')

def download(request, barcard_id):
    if request.method == 'GET':
        barcard = get_object_or_404(Barcard, pk=barcard_id)
        return render(request, 'drinks/download.html', {'barcard':barcard})
    else:
        return HttpResponseRedirect('/drinks/')
