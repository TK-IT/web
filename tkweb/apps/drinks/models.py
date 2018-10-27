from django.db import models

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
