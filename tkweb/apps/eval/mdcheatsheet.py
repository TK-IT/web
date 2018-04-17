from wiki.core.plugins import registry
from wiki.core.plugins.base import BasePlugin


class MdCheatSheetPlugin(BasePlugin):
    slug = "mdcheatsheet"

    sidebar = {'headline': 'Markdown cheatsheet',
               'icon_class': 'fa-info',
               'template': 'mdcheatsheet/sidebar.html',
               }


registry.register(MdCheatSheetPlugin)
