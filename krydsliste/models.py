from django.db import models
from django.contrib.auth.models import User


class Sheet(models.Model):
    name = models.CharField(max_length=255)

    title = models.TextField(blank=True)
    left_label = models.TextField(blank=True)
    right_label = models.TextField(blank=True)
    column1 = models.TextField(blank=True)
    column2 = models.TextField(blank=True)
    column3 = models.TextField(blank=True)
    front_persons = models.TextField(blank=True)
    back_persons = models.TextField(blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=False, related_name='+')
    created_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
