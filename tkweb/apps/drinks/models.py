from django.db import models
import subprocess
from django.core.files import File


class Drink(models.Model):
    name = models.CharField(max_length=30)
    serving = models.CharField(max_length=50)
    soda = models.CharField(max_length=50)
    price = models.IntegerField()

    def __str__(self):
        return self.name

class Sprut(models.Model):
    drink = models.ForeignKey(Drink, on_delete=models.CASCADE) 
    name = models.CharField(max_length=30)
    amount = models.IntegerField()

    def __str__(self):
        return self.name

class Barcard(models.Model):
    name = models.CharField(max_length=30)
    drinks = models.ManyToManyField(Drink)
    barcardFile = models.FileField(blank=True, upload_to='barcard') 
    mixingFile = models.FileField(blank=True, upload_to='mixing') 
    
    def __str__(self):
        return self.name

    def generateFiles(self):
        filePath = 'tkweb/apps/drinks/drinkskort/drinks.txt'
        with open(filePath, 'w') as f:
            for drink in self.drinks.all():
                f.write('= '+drink.name+'\n')
                for sprut in drink.sprut_set.all():
                    f.write('- '+str(sprut.amount)+' cl - '+sprut.name+'\n')
                f.write('-- '+drink.soda+'\n')
                f.write('! '+drink.serving+'\n')
                f.write('$ '+str(drink.price)+'\n')
        bashCommand = 'make -C tkweb/apps/drinks/drinkskort/'
        subprocess.call(bashCommand, shell=True)
        filePath =  'tkweb/apps/drinks/drinkskort/'
        barFile = open(filePath+'bar_drinks.pdf', mode='rb')
        mixFile = open(filePath+'/mixing_drinks.pdf', mode='rb')
        self.barcardFile.save(self.name+'_barcard',File(barFile))
        self.mixingFile.save(self.name+'_mixing',File(mixFile))
