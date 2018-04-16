from django.core.management.base import CommandError
from ._private import RegnskabCommand

import json
from tkweb.apps.regnskab.legacy.export import export_data
from tkweb.apps.regnskab.legacy.import_sheets import import_sheets, import_profiles
from tkweb.apps.regnskab.legacy.import_aliases import import_aliases
from tkweb.apps.regnskab.legacy.import_statuses import import_statuses


class Command(RegnskabCommand):
    def add_arguments(self, parser):
        parser.add_argument('-b', '--backup-dir')
        parser.add_argument('-g', '--git-dir')
        parser.add_argument('-i', '--json-input')
        parser.add_argument('-n', '--name-trans')
        parser.add_argument('-o', '--json-output')
        parser.add_argument('-f', '--save', action='store_true')
        parser.add_argument('-p', '--save-profiles', action='store_true')

    def handle(self, *args, **options):
        input_options = 'backup_dir git_dir json_input'.split()
        output_options = 'json_output save save_profiles'.split()
        self.at_least_one(options, input_options)
        self.at_least_one(options, output_options)
        if options['json_input']:
            if options['backup_dir'] or options['git_dir']:
                raise CommandError('--json-input cannot be mixed with other ' +
                                   'input options')
            if options['name_trans']:
                raise CommandError('--json-input cannot be mixed with ' +
                                   '--name-trans')
            with open(options['json_input']) as fp:
                input_json = json.load(fp)
            sheets = input_json['sheets']
            aliases = input_json['aliases']
            statuses = input_json['statuses']
        else:
            name_trans = {}
            if options['name_trans']:
                with open(options['name_trans']) as fp:
                    for line in fp:
                        o = json.loads(line)
                        name_trans[o[0]] = o[1]
            sheets, aliases, statuses = export_data(
                git_dir=options['git_dir'], backup_dir=options['backup_dir'],
                name_trans=name_trans)
        if options['json_output']:
            with open(options['json_output'], 'w') as fp:
                json.dump(
                    dict(sheets=sheets, aliases=aliases, statuses=statuses),
                    fp, indent=2)
        if options['save_profiles']:
            import_profiles(sheets, self)
        if options['save']:
            import_sheets(sheets, self)
            import_aliases(aliases, self.stdout)
            import_statuses(statuses, self.stdout)
