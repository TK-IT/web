from django.db import models

class Event(models.Model):
    class Meta:
        ordering = ['date']

    title = models.CharField(max_length=200)
    date = models.DateField()
    description = models.TextField()
    facebook = models.CharField(max_length=200)
