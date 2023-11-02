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
    deleted_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

    @staticmethod
    def format_persons(name_list, rows=31):
        name_list = list(name_list)[:rows]
        name_list += [''] * (rows - len(name_list))
        return '\n'.join(r'\person{%s}' % name for name in name_list)
