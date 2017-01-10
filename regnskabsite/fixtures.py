import string
import numpy as np

from regnskab.models import (
    Profile, Title, Alias, EmailTemplate,
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

    r = np.random.RandomState(42)

    def choice(iterable):
        xs = list(iterable)
        return xs[r.choice(len(xs))]

    def letter_choice():
        return choice(string.ascii_uppercase + 'ÆØÅ')

    def make_fu():
        return 'FU%s%s' % (letter_choice(), letter_choice())

    def append_bestfu(name, root, age):
        profiles.append(Profile(
            name=name,
            email='dummy%s%s@example.com' % (root, age)))
        titles.append(Title(profile=profiles[-1],
                            root=root, period=gfyear - age))

    for age in range(years):
        for root in best:
            append_bestfu('BEST%s %ssen' % (age, root), root, age)
        fu = [make_fu() for _ in range(n_fu)]
        for root in fu:
            root = make_fu()
            append_bestfu('Fjolle%s%s' % (root, age), root, age)
    for i in range(hangarounds):
        profiles.append(Profile(
            name='Hænger%s Hængersen' % i,
            email='dummyhangaround%s@example.com' % i))
    for _ in range(len(profiles)):
        profile = choice(profiles)
        root = ''.join(letter_choice() for _ in range(4))
        aliases.append(Alias(profile=profile, root=root))
    return profiles, titles, aliases


def get_default_email():
    return EmailTemplate(name=EMAIL_NAME, subject=EMAIL_SUBJECT,
                         body=EMAIL_TEXT, format=EmailTemplate.POUND)


def generate_auto_data(*args, **kwargs):
    profiles, titles, aliases = auto_data(*args, **kwargs)
    emails = [get_default_email()]
    profiles = Helper.save_all(profiles, only_new=True, unique_attrs=['email'])
    for o in profiles:
        o.save()
    titles = Helper.filter_related(profiles, titles, 'profile')
    aliases = Helper.filter_related(profiles, aliases, 'profile')
    Helper.save_all(titles, bulk=True)
    Helper.save_all(aliases, bulk=True)
    Helper.save_all(emails, unique_attrs=['name'])
