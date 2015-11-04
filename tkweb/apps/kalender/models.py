from django.db import models
import re

class Event(models.Model):
    class Meta:
        ordering = ['date']

    title = models.CharField(max_length=200)
    date = models.DateField()
    description = models.TextField()
    facebook = models.CharField(max_length=200)

    def save(self):
        """Extract facebook url from description"""

        p = re.compile('((https?://)?(www\.)?(facebook|fb)\.com[a-z0-9/]*)')
        desc_l = p.split(self.description)
        if len(desc_l)>=2:
            self.facebook = desc_l[1]
            self.description = desc_l[0].strip()

        super(Event, self).save()
