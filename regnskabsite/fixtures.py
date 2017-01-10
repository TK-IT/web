import string
import numpy as np

from regnskab.models import Profile, Title, Alias, config, BEST_ORDER
from regnskab.legacy.import_sheets import Helper


BEST = sorted(BEST_ORDER.keys(), key=lambda k: BEST_ORDER[k])


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


def generate_auto_data(*args, **kwargs):
    profiles, titles, aliases = auto_data(*args, **kwargs)
    profiles = Helper.save_all(profiles, only_new=True, unique_attrs=['email'])
    for o in profiles:
        o.save()
    titles = Helper.filter_related(profiles, titles, 'profile')
    aliases = Helper.filter_related(profiles, aliases, 'profile')
    Helper.save_all(titles, bulk=True)
    Helper.save_all(aliases, bulk=True)
