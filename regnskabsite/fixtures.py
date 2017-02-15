import string
import datetime
import numpy as np

from regnskab.models import (
    Profile, Title, Alias, EmailTemplate, SheetStatus,
    config, BEST_ORDER,
)
from regnskab.legacy.import_sheets import Helper


BEST = sorted(BEST_ORDER.keys(), key=lambda k: BEST_ORDER[k])


EMAIL_TEXT = '''Kære #TITEL ##NAVN#

Så er krydslisten blevet gjort op.
Siden sidst er der sket følgende med din regning:

Der er betalt #BETALT# kr.
Der er sat #OEL# ølkrydser (á #POEL# kr.).
Der er sat #VAND# sodavandskrydser (á #PVAND# kr.).
Der er sat #GULD# guldølskrydser (á #PGULD# kr.).

Der er skrevet #KASSER# kasser øl på krydslisten (á #PKASSER# kr.).

Altså er din regning nu på: #GAELD# kr.

Hvis din regning overstiger #MAXGAELD# kr., skal den betales,
før du igen må benytte krydslisten.

Med venlig hilsen
   #INKA#,
   INKA i TÅGEKAMMERET'''

EMAIL_SUBJECT = '[TK] Status på ølregningen'

EMAIL_NAME = 'Standard'


class RandomState:
    def __init__(self, seed):
        self.rng = np.random.RandomState(seed)

    def choice(self, iterable):
        xs = list(iterable)
        return xs[rng.choice(len(xs))]

    def letter_choice(self):
        return choice(string.ascii_uppercase + 'ÆØÅ')

    def add_aliases(self, profiles):
        for i in range(len(profiles)):
            if i == n:
                rng = np.random.RandomState(314159265)
            profile = self.choice(profiles)
            root = ''.join(self.letter_choice() for _ in range(4))
            aliases.append(Alias(profile=profile, root=root))

    def fu_name(self):
        return 'FU%s%s' % (self.letter_choice(), self.letter_choice())


def get_status(profile, in_current):
    start_time = datetime.datetime(year=1980, month=1, day=1)
    if in_current:
        end_time = None
    else:
        end_time = datetime.datetime(year=1981, month=1, day=1)
    return SheetStatus(profile=profile, start_time=start_time,
                       end_time=end_time)


def auto_data(gfyear=None, years=5, best=BEST, n_fu=10, hangarounds=40):
    if gfyear is None:
        gfyear = config.GFYEAR

    titles = []
    aliases = []
    statuses = []

    def make_bestfu(years):
        rng = RandomState(314159)

        profiles = []
        def make(name, root, age, in_current):
            profiles.append(Profile(
                name=name,
                email='dummy%s%s@example.com' % (root, age)))
            kind = Title.FU if root.startswith('FU') else Title.BEST
            titles.append(Title(profile=profiles[-1], kind=kind,
                                root=root, period=gfyear - age))
            aliases.append(get_status(profiles[-1], in_current))

        for age in range(years):
            for root in best:
                in_current = age == 0 or root != best[age % len(best)]
                make('BEST%s %ssen' % (age, root), root, age, in_current)
            fu = [rng.fu_name() for _ in range(n_fu)]
            for root in fu:
                in_current = age == 0 or root[2] < 'N'
                make('Fjolle%s%s' % (root, age), root, age, in_current)

        rng.add_aliases(profiles)
        return profiles

    def make_hangarounds(hangarounds):
        rng = RandomState(3141592)
        profiles = []
        for i in range(hangarounds):
            profiles.append(Profile(
                name='Hænger%s Hængersen' % i,
                email='dummyhangaround%s@example.com' % i))
            if i % 4 < 3:
                aliases.append(get_status(profiles[-1], i % 4 < 2))
        rng.add_aliases(profiles)
        return profiles

    profiles = make_bestfu(years) + make_hangarounds(hangarounds)
    return profiles, titles, aliases, statuses


def get_default_email():
    return EmailTemplate(name=EMAIL_NAME, subject=EMAIL_SUBJECT,
                         body=EMAIL_TEXT, format=EmailTemplate.POUND)


def generate_auto_data(*args, **kwargs):
    profiles, titles, aliases, statuses = auto_data(*args, **kwargs)
    emails = [get_default_email()]
    profiles = Helper.save_all(profiles, only_new=True, unique_attrs=['email'])
    for o in profiles:
        o.save()
    titles = Helper.filter_related(profiles, titles, 'profile')
    aliases = Helper.filter_related(profiles, aliases, 'profile')
    statuses = Helper.filter_related(profiles, statuses, 'profile')
    Helper.save_all(titles, bulk=True)
    Helper.save_all(aliases, bulk=True)
    Helper.save_all(statuses, bulk=True)
    Helper.save_all(emails, unique_attrs=['name'])
