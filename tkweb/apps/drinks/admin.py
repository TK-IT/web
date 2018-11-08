from django.contrib import admin

from tkweb.apps.drinks.models import Drink, Sprut, Barcard


class BarcardAdmin(admin.ModelAdmin):
    model = Barcard
    filter_horizontal = ("drinks",)
    exclude = ("barcard_file", "mixing_file")


class SprutInline(admin.TabularInline):
    model = Sprut
    extra = 1


class DrinkAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["name", "price"]}),
        ("Recipe", {"fields": ["serving", "soda"]}),
    ]
    inlines = [SprutInline]


admin.site.register(Barcard, BarcardAdmin)
admin.site.register(Drink, DrinkAdmin)
