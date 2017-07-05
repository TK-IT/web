from django import forms
from django.contrib import admin
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.models import FlatPage
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _


# Define a new FlatPageAdmin
class TKBrandFlatPageAdmin(FlatPageAdmin):
    """
    For at illustrere hvordan de forskellige tags fra tkbrand kan bruges i flatpages,
    bliver de vist på admin siden.

    For at vise guiden, laves en ny form med et help-field,
    med en widget der renderer tkbrand/templatetags.html.
    Dette field grupperes sammen med content, så de bliver vist side om side.
    """

    class FlatPageForm(forms.ModelForm):
        class Meta:
            model = FlatPage
            fields = '__all__'

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['url'].help_text = 'Eksempel: \'/om/kontakt/\'. Vær opmærksom på, at der skal være skråstreg både først og sidst.'

        class HelpWidget(forms.Widget):
            def render(self, name, value, attrs=None):
                return render_to_string('tkbrand/templatetags.html')

        content_help = forms.CharField(label='', required=False, widget=HelpWidget)

    form = FlatPageForm

    fieldsets = (
        (None, {
            'fields': ('url', 'title', ('content', 'content_help'), 'sites'),
        }),
        (_('Advanced options'), {
            'classes': ('collapse', ),
            'fields': (
                'enable_comments',
                'registration_required',
                'template_name',
            ),
        }),
    )

# Re-register FlatPageAdmin
admin.site.unregister(FlatPage)
admin.site.register(FlatPage, TKBrandFlatPageAdmin)
