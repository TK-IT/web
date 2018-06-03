from django.db import models
from django.contrib.auth.models import User


class SharedFile(models.Model):
    file = models.FileField(upload_to="shared")
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    created_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["file"]

    def __str__(self):
        return self.file.name
