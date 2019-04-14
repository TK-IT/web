import collections
import datetime
import markdown
import random
import re
import shlex
from django.template.loader import render_to_string
from django.utils import dateparse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from wiki.core.plugins import registry
from wiki.core.plugins.base import BasePlugin
import tkweb.apps.tkbrand.templatetags.tkbrand as tkbrand
from constance import config

METHODS = [
    'begin_hide', 'end_hide', 'begin_fixme', 'end_fixme', 'timeout', 'updated',
    'TK', 'TKAA', 'TKET', 'TKETAA', 'TKETs', 'TKETsAA', 'TKETS', 'TKETSAA',
    'tk_prefix', 'tk_kprefix', 'tk_postfix', 'tk_prepostfix', 'tk_email',
    'eps', 'remtor',
]

MONTHS = [('Jan', 'January', 'Januar'),
          ('Feb', 'February', 'Februar'),
          ('Mar', 'March', 'Marts'),
          ('Apr', 'April', 'KBEST'),  # NB: KBEST
          ('May', 'May', 'Maj'),
          ('Jun', 'June', 'Juni'),
          ('Jul', 'July', 'Juli'),
          ('Aug', 'August'),
          ('Sep', 'Sept', 'September', 'GF'),  # NB: GF
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
    for i, month_names in enumerate(MONTHS):
        for name in month_names:
            if name.lower() == month.lower():
                return i + 1
    raise ValueError("'%s' is not a valid month" % month)


class EvalMacroPattern(markdown.inlinepatterns.Pattern):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hide_stack = []

    @staticmethod
    def _get_pattern(method_names):
        pattern = (
            # Start by matching one of the names in method_names.
            r"\[(?P<macro>%s)" % '|'.join(
                re.escape(method_name) for method_name in method_names) +
            # Then match optional arguments of at most 300 characters.
            r"(?:\s+(?P<args>[^]\n]{0,300}))?\]"
        )
        return pattern

    MacroInvocation = collections.namedtuple(
        'MacroInvocation', 'macro args full')

    @staticmethod
    def _parse_match(mo):
        macro = mo.group('macro')
        macro = macro.strip()
        args_str = mo.group('args')
        args = shlex.split(args_str) if args_str else ()
        full = mo.group(2)
        return EvalMacroPattern.MacroInvocation(macro, args, full)

    @staticmethod
    def find_macro_invocations(article_content, method_name):
        pattern = EvalMacroPattern._get_pattern([method_name])
        return [EvalMacroPattern._parse_match(mo)
                for mo in re.finditer(pattern, article_content)]

    def handleMatch(self, mo):
        try:
            match = self._parse_match(mo)
            method = getattr(self, match.macro)
            return method(*match.args, full=match.full)
        except Exception as exn:
            return _inline_error(mo.group(2), exn)

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
        self.hide_stack.append(title)
        return self.markdown.htmlStash.store(html, safe=False)

    def end_hide(self, title='', full=''):
        html = render_to_string("evalmacros/end_hide.html")
        if self.hide_stack:
            expected_title = self.hide_stack.pop()
            if title and title != expected_title:
                html += _inline_error(
                    full, 'Expected [end_hide %s]' % expected_title
                )
        else:
            html += _inline_error(full, 'Unmatched [end_hide]')

        return self.markdown.htmlStash.store(html, safe=False)

    begin_hide.meta = {
        'short_description': 'Skjul en sektion',
        'help_text': ('Skjuler en sektion der kun er relevant for nogle ' +
                      'grupper eller personer. Andre kan stadig se ' +
                      'sektionen ved at trykke på en knap.'),
        'example_code': ('[begin_hide KASS]\nNoget der er ' +
                         'skjult for alle andre end KASS.\n[end_hide KASS]'),
        'args': {
            'title': 'Personen eller gruppen indholdet ikke er skjult for.',
        },
    }

    def begin_fixme(self, full=""):
        title = "FIXME"
        html = render_to_string(
            "evalmacros/begin_fixme.html",
            context={"title": title, "id": title + "-" + str(random.randrange(9999))},
        )
        return self.markdown.htmlStash.store(html, safe=False)

    def end_fixme(self, full=""):
        html = render_to_string("evalmacros/end_fixme.html")
        return self.markdown.htmlStash.store(html, safe=False)

    begin_fixme.meta = {
        "short_description": "Fixme",
        "help_text": "Tilføjer en fixme note.",
        "example_code": "[begin_fixme]\nHer mangler at blive læst korrektur.\n[end_fixme]",
    }

    def timeout(self, month, full=''):
        try:
            parseTimeoutMonth(month)
        except Exception as exn:
            return _inline_error(full, exn)
        # The output of timeout and updated is handled by
        # templates/eval/includes/updated.html
        return ''

    timeout.meta = {
        'short_description': 'Forfald',
        'help_text': (
            'Tilføjer en forfaldsdato til en artikel og tilføjer den til ' +
            'listen over forældede artikler. Dog ikke hvis den er blevet ' +
            'ajourført inden da.'),
        'example_code': ('[timeout feb]'),
        'args': {
            'month': 'Måneden hvor artiklen forfalder.',
        },
    }

    def updated(self, title, date, full=''):
        try:
            if dateparse.parse_date(date) is None:
                raise ValueError('%s is not a valid date' % date)
        except Exception as exn:
            return _inline_error(full, exn)
        # The output of timeout and updated is handled by
        # templates/eval/includes/updated.html
        return ''

    updated.meta = {
        'short_description': 'Ajourføring',
        'help_text': (
            'Ajourføre en artikel. Det fjerner artiklen fra listen over ' +
            'forældede artikler. Brug kun denne når <em>alle</em> fejl er ' +
            'blevet rettet.'),
        'example_code': ('[updated BEST 2018-05-12]'),
        'args': {
            'title': ('Navet på personen eller gruppen der har udført ' +
                      'ajourføringen.'),
            'dato': ('Datoen, i formatet YYYY-MM-DD, hvor ajourføringen har ' +
                     'fundet sted.'),
        },
    }

    _TKBRANDFUNCS = [tkbrand.TK, tkbrand.TKAA, tkbrand.TKET, tkbrand.TKETAA,
                     tkbrand.TKETs, tkbrand.TKETsAA, tkbrand.TKETS,
                     tkbrand.TKETSAA]

    def TK(self, full=''):
        return self.markdown.htmlStash.store(tkbrand.TK())

    def TKAA(self, full=''):
        return self.markdown.htmlStash.store(tkbrand.TKAA())

    def TKET(self, full=''):
        return self.markdown.htmlStash.store(tkbrand.TKET())

    def TKETAA(self, full=''):
        return self.markdown.htmlStash.store(tkbrand.TKETAA())

    def TKETs(self, full=''):
        return self.markdown.htmlStash.store(tkbrand.TKETs())

    def TKETsAA(self, full=''):
        return self.markdown.htmlStash.store(tkbrand.TKETsAA())

    def TKETS(self, full=''):
        return self.markdown.htmlStash.store(tkbrand.TKETS())

    def TKETSAA(self, full=''):
        return self.markdown.htmlStash.store(tkbrand.TKETSAA())

    TK.meta = {
        'short_description': '%s og venner' % tkbrand.TKET(),
        'help_text': (
            ('Brug følgende makroer til at skrive %s og lignende med ' +
             'hoppe-danseskrift.') % tkbrand.TKET() +
            '<table class="table table-condensed">' +
            '<tr><th>Makro</th><th>Output</th></tr>' +
            ''.join(['<tr><td>[%s]</td><td>%s</td></tr>'
                     % (f.__name__, f()) for f in _TKBRANDFUNCS]) +
            '</table>'),
    }

    def remtor(self, full=''):
        return self.markdown.htmlStash.store('R&straightepsilon;mToR')

    def eps(self, full=''):
        return self.markdown.htmlStash.store('&straightepsilon;')

    remtor.meta = {
        'short_description': 'R&straightepsilon;mToR',
        'help_text': (
            'Brug følgende makroer til at skrive R&straightepsilon;mToR.' +
            '<table class="table table-condensed">' +
            '<tr><th>Makro</th><th>Output</th></tr>' +
            '<tr><td>[remtor]</td><td>R&straightepsilon;mToR</td></tr>' +
            '<tr><td>[eps]</td><td>&straightepsilon;</td></tr>' +
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
        if not year:
            return _inline_error(full, 'First argument is required')
        if not title:
            email = year
        else:
            email = tkbrand.tk_email((title, self._get_year(year)))
        return self.markdown.htmlStash.store(
            '<a href="mailto:%s@TAAGEKAMMERET.dk">%s@%s.dk</a>' %
            (email, email, tkbrand.TKETAA())
        )

    tk_prefix.meta = {
        'short_description': 'Anciennitet',
        'help_text': ('Følgene makroer giver et titel-prefix eller -postfix ' +
                      'relativt til det nuværende år. Eksempelvis bliver ' +
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
                      ('<tr><td>[tk_prepostfix 2015 SEKR]</td><td>%s</td></tr>' % tkbrand.tk_prepostfix(('SEKR', 2015))) +
                      ('<tr><td>[tk_email 2010 FUHØ]</td><td><a href="mailto:%(e)s@TAAGEKAMMERET.dk">%(e)s@TAAGEKAMMERET.dk</a></td></tr>' % { 'e': tkbrand.tk_email(('FUHØ', 2010))}) +
                      '</table>'),
    }


class EvalMacroExtension(markdown.Extension):
    def extendMarkdown(self, md, md_globals):
        md.inlinePatterns.add(
            'tk-macros',
            EvalMacroPattern(EvalMacroPattern._get_pattern(METHODS), md),
            '>escape',
        )


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
