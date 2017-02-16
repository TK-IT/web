import string
import datetime
import itertools
import numpy as np
import collections

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
        return xs[self.rng.choice(len(xs))]

    def letter_choice(self):
        return self.choice(string.ascii_uppercase + 'ÆØÅ')

    def make_aliases(self, n):
        result = {}
        for i in range(n):
            profile = self.rng.choice(n)
            root = ''.join(self.letter_choice() for _ in range(4))
            result.setdefault(profile, []).append(root)
        return result

    def fu_name(self):
        return 'FU%s%s' % (self.letter_choice(), self.letter_choice())


PersonBase = collections.namedtuple(
    'Person', 'name email titles statuses aliases')


class Person(PersonBase):
    def models(self):
        profile = Profile(name=self.name, email=self.email)
        titles = [Title(profile=profile, root=root, period=period)
                  for root, period in self.titles]
        statuses = [SheetStatus(profile=profile,
                                start_time=start, end_time=end)
                    for start, end in self.statuses]
        aliases = [Alias(profile=profile, root=root)
                   for root in self.aliases]
        return profile, titles, statuses, aliases


def models_from_persons(persons):
    profiles = []
    extra = []
    for person in persons:
        profile, *e = person.models()
        profiles.append(profile)
        extra.append(e)
    extra_by_type = zip(*extra)
    # Each extra_by_type[i] is a list of lists (of Titles, Aliases, ...)
    extra_flat = [list(itertools.chain.from_iterable(e))
                  for e in extra_by_type]
    # Each extra_flat[i] is a flattening of extra_by_type[i]
    return (profiles,) + tuple(extra_flat)


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
        alias_dict = rng.make_aliases(profiles)

        def make(name, root, age, in_current):
            profile = Profile(
                name=name,
                email='dummy%s%s@example.com' % (root, age))
            kind = Title.FU if root.startswith('FU') else Title.BEST
            titles.append(Title(profile=profile, kind=kind,
                                root=root, period=gfyear - age))
            statuses.append(get_status(profile, in_current))
            for root in alias_dict.get(len(profiles

        for age in range(years):
            for root in best:
                in_current = age == 0 or root != best[age % len(best)]
                make('BEST%s %ssen' % (age, root), root, age, in_current)
            fu = [rng.fu_name() for _ in range(n_fu)]
            for root in fu:
                in_current = age == 0 or root[2] < 'N'
                make('Fjolle%s%s' % (root, age), root, age, in_current)

        return profiles

    def make_hangarounds(hangarounds):
        rng = RandomState(3141592)
        profiles = []
        alias_dict = rng.make_aliases(profiles)
        for i in range(hangarounds):
            profile = Profile(
                name='Hænger%s Hængersen' % i,
                email='dummyhangaround%s@example.com' % i)
            if i % 4 < 3:
                statuses.append(get_status(profile, i % 4 < 2))
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
