from django.contrib import admin

from .models import Drink, Sprut 

class SprutInline(admin.TabularInline):
    model = Sprut
    extra = 1 

class DrinkAdmin(admin.ModelAdmin):
    fieldsets = [
            (None, {'fields':
                ['name','price']}),
            ('Recipe', {'fields':
                ['serving','soda']})]
    inlines = [SprutInline]

admin.site.register(Drink, DrinkAdmin)
