from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from django.core.files.storage import FileSystemStorage
from django.core.files import File

from .forms import BarcardGenForm
import subprocess

class BarcardSelect(FormView):
    template_name = 'drinks/home.html'
    form_class = BarcardGenForm
    success_url = 'download/'

    def form_valid(self, form):
        return super().form_valid(form)

def barcardGen(request):
    if request.method =='POST':
        card = request.POST.__getitem__('barcard')
        bashCommand = 'make -C tkweb/apps/drinks/drinkskort/'
        subprocess.call(bashCommand, shell=True)
        barFile = open('tkweb/apps/drinks/drinkskort/bar_drinks.pdf',  encoding = "ISO-8859-1")
#        mixFile = open('drinkskort/mixing_drinks.pdf')

        fs = FileSystemStorage()
        barFilename = fs.save('barkort', barFile)
#        mixFilename = fs.save(car.__str__+'_mix', mixFile)
        bar_uploaded_file_url = fs.url(barFilename)
#        mix_uploaded_file_url = fs.url(barFilename)
        return render(request, 'drinks/download.html', {
            'bar_uploaded_file_url': bar_uploaded_file_url
        })
    return render(request, 'drinks/download.html')
        
