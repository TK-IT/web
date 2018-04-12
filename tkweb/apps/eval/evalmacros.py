import datetime
import markdown
import random
import re
import shlex
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from wiki.core.plugins import registry
from wiki.core.plugins.base import BasePlugin
import tkweb.apps.tkbrand.templatetags.tkbrand as tkbrand
from constance import config

METHODS = [
    'begin_hide', 'end_hide', 'fixme', 'timeout', 'updated',
    'TK', 'TKAA', 'TKET', 'TKETAA', 'TKETs', 'TKETsAA', 'TKETS', 'TKETSAA',
    'tk_prefix', 'tk_kprefix', 'tk_postfix', 'tk_prepostfix', 'tk_email',
]

MONTHS = [('Jan', 'January', 'Januar'),
          ('Feb', 'February', 'Februar'),
          ('Mar', 'March', 'Marts'),
          ('Apr', 'April',),
          ('May', 'May', 'Maj'),
          ('Jun', 'June', 'Juni'),
          ('Jul', 'July', 'Juli'),
          ('Aug', 'August'),
          ('Sep', 'Sept', 'September'),
          ('Oct', 'October', 'Okt', 'Oktober'),
          ('Nov', 'November'),
          ('Dec', 'December')]

def _inline_error(method, error):
    html = (
        '<span class="tk-error">' +
        '<span class="btn btn-danger">%s</span>' +
        '<span class="btn btn-default">%s</span>' +
        '</span>') % (method, error)
    return html

def parseTimeoutMonth(month):

        pattern = (r"(?P<month>(%s))" %
                   '|'.join(m for ml in MONTHS for m in ml))
        mo = re.search(pattern, month, re.IGNORECASE)

        if mo is None:
            raise ValueError("\'%s\' is not a valid month" % month)

        mg = mo.group('month')

        def _convert(lst):
            dct = {}
            for i, v in enumerate(lst):
                for v in v:
                    dct[v.lower()] = i+1
            return dct

        return _convert(MONTHS)[mg]


class EvalMacroExtension(markdown.Extension):
    def extendMarkdown(self, md, md_globals):
        """ Insert EvalMacroPreprocessor before ReferencePreprocessor. """
        md.preprocessors.add(
            'tk-macros', EvalMacroPreprocessor(md), '>html_block')


class EvalMacroPreprocessor(markdown.preprocessors.Preprocessor):
    def run(self, lines):
        pattern = (
            # Start by matching one of the names in METHODS.
            r"\[(?P<macro>%s)" % '|'.join(
                re.escape(method_name) for method_name in METHODS) +
            # Then match optional arguments of at most 300 characters.
            r"(?:\s+(?P<args>[^]\n]{0,300}))?\]"
        )

        def repl(mo):
            macro = mo.group('macro')
            try:
                macro = macro.strip()
                method = getattr(self, macro)
                args_str = mo.group('args')
                args = shlex.split(args_str) if args_str else ()
                return method(*args, full=mo.group(0))
            except Exception as exn:
                return _inline_error(mo.group(0), exn)

        return [re.sub(pattern, repl, line) for line in lines]

    def get_user_groups(self):
        try:
            return self._cached_user_groups
        except AttributeError:
            self._cached_user_groups = list(
                self.markdown.user.groups.values_list('name', flat=True))
            return self._cached_user_groups

    def begin_hide(self, title='BEST', full=''):
        expanded = any(t.lower() == title.lower()
                       for t in self.get_user_groups())
        html = render_to_string(
            "evalmacros/begin_hide.html",
            context={
                'title': title,
                'id': title+'-'+str(random.randrange(9999)),
                'expanded': expanded,
            })
        return self.markdown.htmlStash.store(html, safe=False)

    def end_hide(self, full=''):
        html = render_to_string("evalmacros/end_hide.html")
        return self.markdown.htmlStash.store(html, safe=False)

    begin_hide.meta = {
        'short_description': 'Skjul en sektion',
        'help_text': ('Skjuler en sektion der kun er relevant for nogle ' +
                      'grupper eller personer. Andre kan stadig se ' +
                      'sektionen ved at trykke på en knap.'),
        'example_code': ('[begin_hide KASS]\nNoget der er ' +
                         'skjult for alle andre end KASS.\n[end_hide]'),
        'args': {
            'title': 'Personen eller gruppen indholdet ikke er skjult for.',
        },
    }

    def fixme(self, *args, full=''):
        title = 'FIXME'
        html = render_to_string(
            "evalmacros/fixme.html",
            context={
                'title': title,
                'id': title+'-'+str(random.randrange(9999)),
                'message': ' '.join(args),
            })
        return self.markdown.htmlStash.store(html, safe=False)

    fixme.meta = {
        'short_description': 'Fixme',
        'help_text': ('Tilføjer en fixme note.'),
        'example_code': ('[fixme Her mangler at blive læst korrektur.]'),
        'args': {
            'message': 'Teksten til fixme noten',
        },
    }

    def timeout(self, month, full=''):
        try:
            parseTimeoutMonth(month)
        except Exception as exn:
            return _inline_error(full, exn)
        return ''

    timeout.meta = {
        'short_description': 'Forfald',
        'help_text': (
            'Tilføjer en forfaldsdato til en artikel og tilføjer den til ' +
            'listen over forældede artikler. Dog ikke hvis den er blevet ' +
            'adjourført inden da.'),
        'example_code': ('[timeout feb]'),
        'args': {
            'month': 'Måneden hvor artiklen forfalder.',
        },
    }

    def updated(self, title, date, full=''):
        wat = self.markdown.article.wikiArticleTimeout
        html = render_to_string(
            "evalmacros/updated.html",
            context={
                'title': title,
                'updated': wat.updated,
                'timeout': wat.timeout(),
                'outdated': wat.outdated(),
            })
        return self.markdown.htmlStash.store(html, safe=False)

    updated.meta = {
        'short_description': 'Ajourførelse',
        'help_text': (
            'Adjourføre en artikel. Det fjerner artiklen fra listen over ' +
            'forældede artikler. Brug kun denne når <em>alle</em> fejl er ' +
            'blevet rettet.'),
        'example_code': ('[updated BEST 2018-05-12]'),
        'args': {
            'title': ('Navet på personen eller gruppen der har udført ' +
                      'ajourførelsen.'),
            'dato': ('Datoen, i formatet YYYY-MM-DD, hvor ajourførelsen har ' +
                     'fundet sted.'),
        },
    }

    _TKBRANDFUNCS = [tkbrand.TK, tkbrand.TKAA, tkbrand.TKET, tkbrand.TKETAA,
                     tkbrand.TKETs, tkbrand.TKETsAA, tkbrand.TKETS,
                     tkbrand.TKETSAA]

    def TK(self, full=''):
        return tkbrand.TK()

    def TKAA(self, full=''):
        return tkbrand.TKAA()

    def TKET(self, full=''):
        return tkbrand.TKET()

    def TKETAA(self, full=''):
        return tkbrand.TKETAA()

    def TKETs(self, full=''):
        return tkbrand.TKETs()

    def TKETsAA(self, full=''):
        return tkbrand.TKETsAA()

    def TKETS(self, full=''):
        return tkbrand.TKETS()

    def TKETSAA(self, full=''):
        return tkbrand.TKETSAA()

    TK.meta = {
        'short_description': '%s og venner' % tkbrand.TKET(),
        'help_text': (
            ('Brug følgende makroer til at skrive %s og ligendene med ' +
             'hoppe-danseskrift.') % tkbrand.TKET() +
            '<table class="table table-condensed">' +
            '<tr><th>Makro</th><th>Output</th></tr>' +
            ''.join(['<tr><td>[%s]</td><td>%s</td></tr>'
                     % (f.__name__, f()) for f in _TKBRANDFUNCS]) +
            '</table>'),
    }

    def _get_year(self, year):
        try:
            year = int(year)
        except:
            raise ValueError("\'%s\' is not a valid period" % year)

        if year < 56:
            year += 2000
        elif year < 100:
            year += 1900
        return year

    def tk_prefix(self, year=None, title='', full=''):
        return tkbrand.tk_prefix((title, self._get_year(year)))

    def tk_kprefix(self, year=None, title='', full=''):
        return tkbrand.tk_kprefix((title, self._get_year(year)))

    def tk_postfix(self, year=None, title='', full=''):
        return tkbrand.tk_postfix((title, self._get_year(year)))

    def tk_prepostfix(self, year=None, title='', full=''):
        if title in (None, ''):
            return _inline_error(full, '\'\' is not a valid title')
        return tkbrand.tk_prepostfix((title, self._get_year(year)))

    def tk_email(self, year=None, title='', full=''):
        if title in (None, ''):
            return _inline_error(full, '\'\' is not a valid title')
        return ('<' + tkbrand.tk_email((title, self._get_year(year))) +
                '@TAAGEKAMMERET.dk>')

    tk_prefix.meta = {
        'short_description': 'Anciennitet',
        'help_text': ('Følgene makroer giver et titel-prefix eller -postfix ' +
                      'relativt til det nuværende år. Eksempel vis bliver ' +
                      '<code>[tk_prefix 2010 VC]</code> til T²OVC. Prefixet ' +
                      'bliver automatisk opdateret ved hver GF.' +
                      '<table class="table table-condensed">' +
                      '<tr><th>Makro</th><th>Output</th></tr>' +
                      ('<tr><td>[tk_prefix 2010]VC</td><td>%sVC</td></tr>' % tkbrand.tk_prefix(('', 2010))) +
                      ('<tr><td>[tk_prefix 2010 VC]</td><td>%s</td></tr>' % tkbrand.tk_prefix(('VC', 2010))) +
                      ('<tr><td>[tk_kprefix 2016]BEST</td><td>%sBEST</td></tr>' % tkbrand.tk_kprefix(('', 2016))) +
                      ('<tr><td>[tk_kprefix 2016 BEST]</td><td>%s</td></tr>' % tkbrand.tk_kprefix(('BEST', 2016))) +
                      ('<tr><td>KA$$[tk_postfix 2017]</td><td>KA$$%s</td></tr>' % tkbrand.tk_postfix(('', 2017))) +
                      ('<tr><td>[tk_postfix 2017 KASS]</td><td>%s</td></tr>' % tkbrand.tk_postfix(('KASS', 2017))) +
                      ('<tr><td>[tk_prepostfix SEKR 2015]</td><td>%s</td></tr>' % tkbrand.tk_prepostfix(('SEKR', 2015))) +
                      ('<tr><td>[tk_email FUHØ 2010]</td><td><a href="mailto:%(e)s@TAAGEKAMMERET.dk">%(e)s@TAAGEKAMMERET.dk</a></td></tr>' % { 'e': tkbrand.tk_email(('FUHØ', 2010))}) +
                      '</table>'),
    }

class EvalMacroPlugin(BasePlugin):
    # TODO: settings.SLUG
    slug = "evalmacros"

    sidebar = {'headline': format_html('{}-makroer', mark_safe(tkbrand.TK())),
               'icon_class': 'fa-beer',
               'template': 'evalmacros/sidebar.html',
               'form_class': None,
               'get_form_kwargs': (lambda a: {})}

    markdown_extensions = [EvalMacroExtension()]


registry.register(EvalMacroPlugin)
