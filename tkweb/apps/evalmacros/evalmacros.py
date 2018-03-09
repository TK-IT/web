import markdown
import random
import re
from django.template.loader import render_to_string
from wiki.core.plugins import registry
from wiki.core.plugins.base import BasePlugin
from wiki.plugins.macros.mdx.macro import KWARG_RE
import tkweb.apps.tkbrand.templatetags.tkbrand as tkbrand
from constance import config
from django.conf import settings as django_settings

METHODS = ['hide_section', 'TK', 'TKAA', 'TKET', 'TKETAA', 'TKETs', 'TKETsAA',
           'TKETS', 'TKETSAA']


class EvalMacroExtension(markdown.Extension):

    """ Macro plugin markdown extension for django-wiki. """

    def extendMarkdown(self, md, md_globals):
        """ Insert MacroPreprocessor before ReferencePreprocessor. """
        md.preprocessors.add('dw-macros', EvalMacroPreprocessor(md), '>html_block')


class EvalMacroPreprocessor(markdown.preprocessors.Preprocessor):


    def run(self, lines):

        """
        Modified from
        https://github.com/django-wiki/django-wiki/blob/master/src/wiki/plugins/macros/mdx/macro.py
        This also replaces inline macros.
        """

        _MACRO_RE = re.compile(
            r'(\[(?P<macro>\w+)(?P<kwargs>\s\w+\:.+)*\])',
            re.IGNORECASE)

        def _replace(m):
            macro = m.group('macro').strip()
            if macro in METHODS and hasattr(self, macro):
                kwargs = m.group('kwargs')
                if kwargs:
                    kwargs_dict = {}
                    for kwarg in KWARG_RE.finditer(kwargs):
                        arg = kwarg.group('arg')
                        value = kwarg.group('value')
                        if value is None:
                            value = True
                        if isinstance(value, str):
                            # If value is enclosed with ': Remove and
                            # remove escape sequences
                            if value.startswith("'") and len(value) > 2:
                                value = value[1:-1]
                                value = value.replace("\\\\", "¤KEEPME¤")
                                value = value.replace("\\", "")
                                value = value.replace("¤KEEPME¤", "\\")
                        kwargs_dict[str(arg)] = value
                    return getattr(self, macro)(**kwargs_dict)
                else:
                    return getattr(self, macro)()
            else:
                return m.string

        return [_MACRO_RE.sub(_replace, line) for line in lines]


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

    _TKBRANDFUNCS = [tkbrand.TK, tkbrand.TKAA, tkbrand.TKET, tkbrand.TKETAA,
                     tkbrand.TKETs, tkbrand.TKETsAA, tkbrand.TKETS,
                     tkbrand.TKETSAA]

    def TK(self):
        return tkbrand.TK()

    def TKAA(self):
        return tkbrand.TKAA()

    def TKET(self):
        return tkbrand.TKET()

    def TKETAA(self):
        return tkbrand.TKETAA()

    def TKETs(self):
        return tkbrand.TKETs()

    def TKETsAA(self):
        return tkbrand.TKETsAA()

    def TKETS(self):
        return tkbrand.TKETS()

    def TKETSAA(self):
        return tkbrand.TKETSAA()

    TK.meta = {
        'short_description': '%s og venner' % tkbrand.TKET(),
        'help_text': (
            ('Brug følgende makroer til at skrive %s og ligendene med ' +
             'hoppe-danseskrift.') % tkbrand.TKET() +
            '<table class="table table-condensed">' +
            ''.join(['<tr><td>[%s]</td><td>%s</td></tr>'
                     % (f.__name__, f()) for f in _TKBRANDFUNCS]) +
            '</table>'),
    }
class EvalMacroPlugin(BasePlugin):

    slug = "evalmacros" #settings.SLUG

    markdown_extensions = [
        EvalMacroExtension()]

registry.register(EvalMacroPlugin)
