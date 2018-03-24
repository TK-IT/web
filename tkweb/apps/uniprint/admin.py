from django.contrib import admin
from .models import (
    Document, Printer, Printout,
)


admin.site.register(Document)
admin.site.register(Printer)
admin.site.register(Printout)
