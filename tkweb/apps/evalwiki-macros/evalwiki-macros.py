import markdown
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

    def hide_section(self):
        html = render_to_string(
            "evalwiki-macros/hide_section.html",
            context={
                'title': "KASS",
            })
        return self.markdown.htmlStash.store(html, safe=False)

    hide_section.meta = dict(
        short_description= 'Skjul en sektion.',
        help_text= 'Insert a list of articles in this level.',
        example_code='[hide_section title:KASS]',
        args={'title': ''}
    )

class EvalMacroPlugin(BasePlugin):

    slug = "evalwiki-macros" #settings.SLUG

    sidebar = {'headline': 'Kammer macros',
               'icon_class': 'fa-play',
               #'template': 'wiki/plugins/macros/sidebar.html',
               'form_class': None,
               'get_form_kwargs': (lambda a: {})}

    markdown_extensions = [
        EvalMacroExtension()]

registry.register(EvalMacroPlugin)
