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
        mo = p.search(self.description)
        if mo is not None:
            self.facebook = mo.group(0)
            self.description = self.description[:mo.begin(0)]

        super(Event, self).save()
