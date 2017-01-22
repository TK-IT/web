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


def auto_data(gfyear=None, years=5, best=BEST, n_fu=10, hangarounds=40):
    if gfyear is None:
        gfyear = config.GFYEAR
    profiles = []
    titles = []
    aliases = []
    statuses = []

    rng = None  # Initialized below

    def choice(iterable):
        xs = list(iterable)
        return xs[rng.choice(len(xs))]

    def letter_choice():
        return choice(string.ascii_uppercase + 'ÆØÅ')

    def make_fu():
        return 'FU%s%s' % (letter_choice(), letter_choice())

    def current_status(profile):
        start_time = datetime.datetime(year=1980, month=1, day=1)
        return SheetStatus(profile=profile, start_time=start_time,
                           end_time=None)

    def old_status(profile):
        start_time = datetime.datetime(year=1980, month=1, day=1)
        end_time = datetime.datetime(year=1981, month=1, day=1)
        return SheetStatus(profile=profile, start_time=start_time,
                           end_time=end_time)

    def append_bestfu(name, root, age, in_current):
        profiles.append(Profile(
            name=name,
            email='dummy%s%s@example.com' % (root, age)))
        kind = Title.FU if root.startswith('FU') else Title.BEST
        titles.append(Title(profile=profiles[-1], kind=kind,
                            root=root, period=gfyear - age))
        if in_current:
            statuses.append(current_status(profiles[-1]))
        else:
            statuses.append(old_status(profiles[-1]))

    rng = np.random.RandomState(314159)
    for age in range(years):
        for root in best:
            in_current = age == 0 or root != best[age % len(best)]
            append_bestfu('BEST%s %ssen' % (age, root), root, age, in_current)
        fu = [make_fu() for _ in range(n_fu)]
        for root in fu:
            root = make_fu()
            in_current = age == 0 or root[2] < 'N'
            append_bestfu('Fjolle%s%s' % (root, age), root, age, in_current)
    n = len(profiles)
    rng = np.random.RandomState(3141592)
    for i in range(hangarounds):
        profiles.append(Profile(
            name='Hænger%s Hængersen' % i,
            email='dummyhangaround%s@example.com' % i))
        if i % 4 < 2:
            statuses.append(current_status(profiles[-1]))
        elif i % 4 < 3:
            statuses.append(old_status(profiles[-1]))
    rng = np.random.RandomState(31415926)
    for i in range(len(profiles)):
        if i == n:
            rng = np.random.RandomState(314159265)
        profile = choice(profiles)
        root = ''.join(letter_choice() for _ in range(4))
        aliases.append(Alias(profile=profile, root=root))
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
