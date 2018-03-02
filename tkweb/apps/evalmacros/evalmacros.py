import markdown
import random
from django.template.loader import render_to_string
from wiki.core.plugins import registry
from wiki.core.plugins.base import BasePlugin
from wiki.plugins.macros.mdx.macro import MacroPreprocessor


class EvalMacroExtension(markdown.Extension):

    """ Macro plugin markdown extension for django-wiki. """

    def extendMarkdown(self, md, md_globals):
        """ Insert MacroPreprocessor before ReferencePreprocessor. """
        md.preprocessors.add('dw-macros', EvalMacroPreprocessor(md), '>html_block')


class EvalMacroPreprocessor(MacroPreprocessor):

    def hide_section(self, title='BEST', message=''):
        html = render_to_string(
            "evalmacros/hide_section.html",
            context={
                'title': title,
                'message': message,
                'id': title+'-'+str(random.randrange(9999)),
                'expanded': self.markdown.user.groups.filter(name__iexact=title).exists()
            })
        return self.markdown.htmlStash.store(html, safe=False)

    hide_section.meta = {
        'short_description': 'Skjul en sektion',
        'help_text': ('Skjuler en sektion der kun er relevant for nogle '\
                      'grupper eller personer. Andre kan stadig se sektionen '\
                      'ved at trykke på en knap.'),
        'example_code': ('[hide_section message:\'Noget der er '\
                         'skjult for alle andre end BEST.]\n'
                         '[hide_section title:\'KASS\' message:\'Noget der er '\
                         'skjult for alle andre end KASS.]'),
        'args': {'title': ('Personen eller gruppen indholdet ikke er skjult '\
                           'for. Standard: BEST'),
                 'message': 'Teksten der skal skjules.',
        },
    }

class EvalMacroPlugin(BasePlugin):

    slug = "evalmacros" #settings.SLUG

    markdown_extensions = [
        EvalMacroExtension()]

registry.register(EvalMacroPlugin)
