import re

from django.contrib import admin

from krydsliste.models import Sheet


class SheetAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'title',
        'left_label', 'column1', 'column2', 'column3', 'right_label',
        'front_count', 'back_count',
    )

    @staticmethod
    def person_count(t):
        n1 = len(re.findall(r'\\person', t))
        n2 = len(re.findall(r'\\lille', t))
        return '%s stor%s, %s %s' % (n1, '' if n1 == 1 else 'e',
                                     n2, 'lille' if n2 == 1 else 'små')

    def front_count(self, sheet):
        return self.person_count(sheet.front_persons)

    def back_count(self, sheet):
        return self.person_count(sheet.back_persons)


admin.site.register(Sheet, SheetAdmin)
