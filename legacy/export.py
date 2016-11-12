import os
import re
import sys
import json
import heapq
import difflib
import argparse
import datetime
import itertools
import subprocess
import collections

from legacy.base import (
    Regnskab, read_regnskab, Person, get_amount, Forbrug, alder,
)


def progress(elements, n=None):
    if n is None:
        elements = list(elements)
        n = len(elements)
    w = len(str(n))
    for i, x in enumerate(elements):
        sys.stderr.write('\r\x1B[K(%s/%s) %s' % (str(i+1).rjust(w), n, x))
        yield x
    sys.stderr.write('\n')


def read_regnskab_revisions_gitpython(gitdir):
    from git import Repo
    repo = Repo(gitdir)
    master = repo.branches[0]
    commits = [master.commit]
    while commits[-1].parents:
        commits.append(commits[-1].parents[0])
    commits.reverse()
    times = [c.authored_datetime for c in commits]
    blobs = [c.tree.join('regnskab.dat') for c in commits]

    prev_sha = None
    for t, blob in zip(progress(times), blobs):
        if blob.binsha == prev_sha:
            continue
        prev_sha = blob.binsha
        try:
            r = read_regnskab(blob.data_stream)
        except ValueError as exn:
            continue
        yield t, r


def read_regnskab_revisions(gitdir):
    def cat_file(objects, gitdir):
        for o in objects:
            p = subprocess.Popen(
                ('git', 'cat-file', 'blob', o),
                cwd=gitdir, stdout=subprocess.PIPE)
            with p:
                yield p.stdout

    proc = subprocess.Popen(
        ('git', 'log', '--pretty=%H %aI', 'HEAD', '--', 'regnskab.dat'),
        universal_newlines=True,
        cwd=gitdir, stdout=subprocess.PIPE)
    revisions = []
    times = []
    for line in proc.stdout:
        mo = re.match(r'^([0-9a-f]+) ([T0-9:-]+\+\d\d):(\d\d)$', line.strip())
        assert mo, line
        revisions.append(mo.group(1))
        times.append(datetime.datetime.strptime(
            mo.group(2) + mo.group(3), '%Y-%m-%dT%H:%M:%S%z'))
    revisions.reverse()
    times.reverse()

    objects = ['%s:regnskab.dat' % r for r in revisions]
    # progress(...) must be in first argument to zip,
    # since zip stops when first stream is exhausted.
    for fp, t in zip(cat_file(progress(objects), gitdir), times):
        try:
            r = read_regnskab(fp)
        except ValueError as exn:
            # print('\n%s: %s' % (type(exn).__name__, exn))
            continue
        yield t, r


def read_regnskab_backups(gitdir):
    pattern = r'^regnskab(\d{6})\.dat$'
    files = sorted((f for f in os.scandir(gitdir)
                    if re.match(pattern, f.name)),
                   key=lambda f: f.name)
    dates = [re.match(pattern, f.name).group(1) for f in files]
    mtimes = [f.stat().st_mtime for f in files]
    if mtimes != sorted(set(mtimes)):
        raise ValueError("Duplicate/not sorted modification times")
    mtimes = [datetime.datetime.fromtimestamp(m, datetime.timezone.utc)
              for m in mtimes]
    # expected_dates = [m.strftime('%y%m%d') for m in mtimes]
    # for f, a, b in zip(files, dates, expected_dates):
    #     if a != b:
    #         print("Date mismatch: %s != %s" % (a, b))
    # progress(...) must be in first argument to zip,
    # since zip stops when first stream is exhausted.
    for f, t in zip(progress(files), mtimes):
        with open(f.path, 'rb') as fp:
            try:
                r = read_regnskab(fp)
            except ValueError as exn:
                raise exn
                # print('\n%s: %s' % (type(exn).__name__, exn))
                # continue
            yield t, r


def match(old, new, attr):
    old_by_attr = {getattr(p, attr): p
                   for p in old}
    matched = []
    not_matched = []
    for p in new:
        try:
            matched.append((old_by_attr.pop(getattr(p, attr)), p))
        except KeyError:
            not_matched.append(p)
    return matched, not_matched, list(old_by_attr.values())


def alive(p):
    return any(p.senest) or any(p.total) or p.gaeld


def opdater_titel_broken(titel):
    """
    Returns a tuple (certain, new_title) indicating the new title
    and whether we are certain that this is the correct new title.

    >>> opdater_titel_broken('FORM')
    (True, 'GFORM')
    >>> opdater_titel_broken('GT')
    (False, 'BT')
    >>> opdater_titel_broken('TOFORM')
    (True, 'T2OFORM')

    Note the broken behavior:

    >>> opdater_titel_broken('T69OVC')
    (True, 'T79OVC')
    """
    mo = re.match(r'^[A-ZÆØÅ0-9]+$', titel)
    if mo is None:
        return (False, None)
    mo = re.match(r'^([GBO]|T[0-9]*O)?', titel)
    prefix = mo.group(0)
    rest = titel[len(prefix):]
    known_titles = 'FORM INKA KASS CERM SEKR NF VC PR'.split()
    if rest in known_titles or (len(rest) == 4 and rest.startswith('FU')):
        certain = True
    else:
        certain = False
    tr = [''] + 'G B O TO T2O'.split()
    if prefix in tr[:-1]:
        up_prefix = tr[tr.index(prefix)+1]
    else:
        mo = re.match(r'^T(\d*?)([0-8]?)(9*)O$', prefix)
        if mo.group(2):
            # This is broken if mo.group(3) is non-empty
            up_prefix = 'T%s%s%sO' % (mo.group(1),
                                      int(mo.group(2))+1,
                                      mo.group(3))
        else:
            assert mo.group(1) == mo.group(2) == ''
            up_prefix = '1' + '0' * len(mo.group(3))
    return (certain, up_prefix + rest)


def is_title(titel):
    certain, next_title = opdater_titel_broken(titel)
    age, root = alder(titel)
    if certain != (age is not None):
        raise Exception("opdater_titel and alder disagree on %s" % titel)
    return certain


def extract_alias_or_title(periods, words):
    '''
    >>> list(extract_alias_or_title([None, None, None, 2013],
    ...                             "Den harmoniske række FORM".split()))
    [(None, 'Den harmoniske række'), (2013, 'FORM')]
    >>> list(extract_alias_or_title([2013, 2014], "FUET EFUIT".split()))
    [(2013, 'FUET'), (2014, 'EFUIT')]
    '''
    i = 0
    while i < len(words):
        if periods[i] is not None:
            yield (periods[i], words[i])
            i += 1
        else:
            j = i+1
            while j < len(words) and periods[j] is None:
                j += 1
            yield (None, ' '.join(words[i:j]))
            i = j


def extract_by_time(current_times, current_words, **kwargs):
    assert len(current_times) == len(current_words)
    i = 0
    while i < len(current_times):
        j = i+1
        while j < len(current_times):
            if current_times[j] == current_times[i]:
                j += 1
            else:
                break
        remove_words = current_words[i:j]
        for period, root in extract_alias_or_title(*zip(*remove_words)):
            yield dict(period=period, root=root,
                       start_time=current_times[i],
                       **kwargs)
        i = j


def parse_alias(title, gfyear):
    FAUX = 'FUDRNF FULUBULU KBO BFUDI GT GP BETTY FUTOKASS'.split()
    age, root = alder(title)
    if age is None or root in ('', 'EFUIT') or title in FAUX:
        return None, title
    if age > 22:
        # Broken legacy handling of T19O which is upgraded to T29O
        q, r = divmod(age - 22, 10)
        if r == 0:
            age = 22 + q
    return gfyear - age, root


def extract_alias_times(aliases, **kwargs):
    current_words = []
    current_times = []
    for gfyear, t, a in aliases:
        words = [w.lstrip('-') for w in a.split() if w.lstrip('-')]
        words = [parse_alias(w, gfyear) for w in words]
        if current_words == words:
            continue
        a_copy = list(current_words)
        matcher = difflib.SequenceMatcher(
            a=a_copy, b=words)
        for op, alo, ahi, blo, bhi in matcher.get_opcodes():
            if op == 'equal':
                continue
            assert words[:blo] == current_words[:blo]
            yield from extract_by_time(current_times[blo:blo+(ahi-alo)],
                                       current_words[blo:blo+(ahi-alo)],
                                       end_time=t, **kwargs)
            current_words[blo:blo+(ahi-alo)] = words[blo:bhi]
            current_times[blo:blo+(ahi-alo)] = (bhi-blo)*[t]
        assert words == current_words


def get_aliases(persons, gfyears):
    result = []
    for person_history in persons:
        name = person_history[-1][0].navn
        aliases = ([(gfyears[t], t,
                     '%s %s' % (p.titel, p.aliaser.replace(',', ' ')))
                    for p, t in person_history] +
                   [(None, None, '')])
        result.extend(extract_alias_times(aliases, name=name))
    return result


def extract_status_times(statuses, name):
    groups = itertools.groupby(statuses, key=lambda x: x[1])
    for skjul, group in groups:
        group = list(group)
        start = group[0][0]
        end = group[-1][0]
        if not skjul:
            yield dict(name=name, start_time=start, end_time=end)


def get_statuses(persons):
    result = []
    for person_history in persons:
        name = person_history[-1][0].navn
        statuses = [(t, p.skjul) for p, t in person_history]
        statuses.append((None, person_history[-1][0].skjul))
        result.extend(extract_status_times(statuses, name=name))
    return result


def get_person_history(persons):
    h = {}
    for x in persons:
        name = x[-1][0].navn
        for p, t in x:
            h.setdefault(t, {})[name] = p
    names = [
        set(h[t].keys())
        for t in sorted(h.keys())
    ]
    for n1, n2 in zip(names[:-1], names[1:]):
        d = n1 - n2
        if d:
            raise ValueError(d)
    return h


def write_aliases(persons, gfyears):
    aliases = get_aliases(persons, gfyears)
    dicts = []
    for o in aliases:
        dicts.append(dict(
            name=o['name'],
            period=o['period'],
            root=o['root'],
            start_time=o['start_time'] and
            o['start_time'].strftime('%Y-%m-%dT%H:%M:%S%z'),
            end_time=o['end_time'] and
            o['end_time'].strftime('%Y-%m-%dT%H:%M:%S%z')))

    with open('regnskab-aliases.json', 'w') as fp:
        json.dump(dicts, fp, indent=2)


def write_statuses(persons):
    statuses = get_statuses(persons)
    statuses = [
        dict(name=o['name'],
             start_time=o['start_time'] and
             o['start_time'].strftime('%Y-%m-%dT%H:%M:%S%z'),
             end_time=o['end_time'] and
             o['end_time'].strftime('%Y-%m-%dT%H:%M:%S%z'))
        for o in statuses]

    with open('regnskab-statuses.json', 'w') as fp:
        json.dump(statuses, fp, indent=2)


def check_name_unique(persons):
    name_counter = collections.Counter(p[-1][0].navn for p in persons)
    name_dups = {k: v for k, v in name_counter.items() if v > 1}
    if name_dups:
        print(name_dups)
        raise Exception()


def get_gfyear(regnskab, base=('Bjarke Skjernaa', 1999, 'KASS')):
    name, year, title = base
    p = next(p for p in regnskab.personer if p.navn == name)
    age, title_ = alder(p.titel)
    if title_ != title:
        raise ValueError((p, title))
    return year + age


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--git-dir')
    parser.add_argument('-b', '--backup-dir')
    args = parser.parse_args()
    data_sources = []
    if args.git_dir:
        data_sources.append(read_regnskab_revisions(args.git_dir))
    if args.backup_dir:
        data_sources.append(read_regnskab_backups(args.backup_dir))
    if not data_sources:
        parser.error("must specify at least one data source")
    if len(data_sources) == 1:
        data_source = data_sources[0]
    else:
        data_source = heapq.merge(*data_sources)

    persons, regnskab_history = get_data(data_source)
    person_history = get_person_history(persons)
    persons.sort(key=lambda ps: (ps[-1][1], ps[-1][0]))
    # print('\n'.join('%s %s %s %s %s' %
    #                 (ps[-1][1], ps[0][1],
    #                  p.navn, p.aliaser, p.email)
    #                 for ps in persons
    #                 for p in [ps[-1][0]]))
    gfyears = {k: get_gfyear(r) for k, r in regnskab_history.items()}
    gfyear_list = [gfyears[k] for k in sorted(regnskab_history.keys())]
    if gfyear_list != sorted(gfyear_list):
        raise Exception("gfyear not sorted")

    write_aliases(persons, gfyears)
    write_statuses(persons)
    check_name_unique(persons)

    # TODO: Use p.gaeld to determine payments
    # rather than depending on p.senest.betalt

    # for person_history in persons:
    #     gaeld = 0
    #     p1 = Forbrug(0, 0, 0, 0, 0, 0)
    #     for p2, t in person_history:
    #         prices = regnskab_history[t].priser
    #         diff = p2.total - p1
    #         if min(diff.oel, diff.xmas, diff.vand, diff.kasser) < -0.1:
    #             diff = Forbrug(0, 0, 0, 0, 0, betalt=gaeld - p2.gaeld)
    #         p1 = p2.total
    #         gaeld += get_amount(prices, diff) - diff.betalt
    #         print('%s\t%s\t%.2f\t%.2f\t%s' %
    #               (t, person_history[-1][0].navn, gaeld, p2.gaeld, diff))
    #         if abs(gaeld - p2.gaeld) > 0.02:
    #             print("Difference too great")

    resets = {}

    for person_idx, person_history in enumerate(persons):
        name = person_history[-1][0].navn
        i = 0
        gæld = 0
        while i < len(person_history):
            p, t = person_history[i]
            if not any(p.senest):
                # Everything was just reset and we do not have any data yet
                i += 1
                continue
            d = p.total - p.senest
            j = i+1
            k = i
            prev_senest = p.senest
            while j < len(person_history):
                p2 = person_history[j][0]
                d2 = p2.total - p2.senest
                if abs(d - d2) > 0.01:
                    break
                if abs(p2.senest - prev_senest) > 0.01:
                    k = j
                prev_senest = p2.senest
                j += 1
            # "senest" was reset at time t corresponding to index i
            resets.setdefault(t, []).append((person_idx, i, k, j))
            i = j

    email_batches = []
    for t in sorted(resets):
        freeze_time = max(
            persons[person_idx][person_freeze][1]
            for person_idx, i, person_freeze, j in resets[t])
        email_persons = [(person_idx, persons[person_idx][k][0])
                         for person_idx, i, k, j in resets[t]]
        email_batches.append((freeze_time, email_persons))

    KINDS = ['oel', 'xmas', 'vand', 'kasser']
    output = []
    for freeze_time, email_persons in email_batches:
        prices = regnskab_history[freeze_time].priser
        purchase_kinds = [
            dict(key=k, price=getattr(prices, k))
            for k in KINDS]
        payments = {}
        purchases = {}
        names = {}
        emails = {}
        titles = {}
        others = {}
        for idx, p in email_persons:
            name = persons[idx][-1][0].navn
            names[name] = p.navn
            emails[name] = p.email
            if p.titel and not p.titel.startswith('-'):
                titles[name] = p.titel.split()[0]
            if p.senest.betalt:
                payments[name] = p.senest.betalt
            if p.senest.andet:
                others[name] = p.senest.andet
            for k in KINDS:
                a = getattr(p.senest, k)
                if a:
                    purchases.setdefault(name, {})[k] = a
        output.append(dict(
            time=freeze_time.strftime('%Y-%m-%dT%H:%M:%S%z'),
            names=names,
            emails=emails,
            titles=titles,
            kinds=purchase_kinds,
            payments=payments,
            purchases=purchases,
            others=others))

    with open('regnskab-history.json', 'w') as fp:
        json.dump(output, fp, indent=2)


def fix_person_name(person):
    d = person._asdict()
    for k in ('navn', 'email'):
        name = d[k]
        name = name.lstrip('\'')
        while '\b' in name:
            name = re.sub(r'.\b', '', name, 1)
        if name == 'Mette Lysgaard Schultz':
            name = 'Mette Lysgaard Schulz'
        d[k] = name
    return type(person)(**d)


def fix_names(iterable):
    for time, (personer, priser, config) in iterable:
        personer = [fix_person_name(p) for p in personer]
        yield time, Regnskab(personer, priser, config)


def remove_duplicates(iterable):
    prev = None
    for t, r in iterable:
        if r != prev:
            yield t, r
        prev = r


def get_data(regnskab_dat):
    regnskab_dat = fix_names(regnskab_dat)
    regnskab_dat = remove_duplicates(regnskab_dat)

    dead_leaves = []
    deleted_leaves = []
    leaf_navn = {}
    email_to_navn = {}
    regnskab_history = {}

    def get_predecessors(p):
        pred_navn = [p.navn]
        if p.email:
            pred_navn.append(email_to_navn.get(p.email))
        if p.navn.startswith('Søren Pingel '):
            pred_navn.append('Søren Pingel')
        elif p.navn == 'Mette Lysgaard Schultz':
            pred_navn.append('Mette Lysgaard Schulz')
        return set(n for n in pred_navn if n and n in leaf_navn)

    for i, (t2, r2) in enumerate(regnskab_dat):
        assert all(isinstance(ps, tuple) for ps in leaf_navn.values())
        assert all(isinstance(p[0], Person) and
                   isinstance(p[1], datetime.datetime)
                   for ps in leaf_navn.values() for p in ps)
        assert len(set(email_to_navn.values())) == len(email_to_navn)
        assert set(email_to_navn.values()).issubset(leaf_navn.keys())
        assert all(email_to_navn[p.email] == p.navn
                   for ps in leaf_navn.values()
                   for p in [ps[-1][0]] if p.email)

        regnskab_history[t2] = r2

        matches = {}
        forget = set()
        for p in r2.personer:
            exs = get_predecessors(p)
            if not exs:
                # New root
                continue
            elif len(exs) == 1:
                ex, = exs
            else:
                # Multiple predecessors, so at most one may be "alive"
                exs_alive = []
                for ex in exs:
                    if not any(alive(p[0]) for p in leaf_navn[ex]):
                        # print("%s is dead" % ex)
                        dead_leaves.append(leaf_navn[ex])
                        if leaf_navn[ex][-1][0].email:
                            email_to_navn.pop(leaf_navn[ex][-1][0].email)
                        leaf_navn.pop(ex)
                    else:
                        exs_alive.append(ex)
                assert len(exs_alive) == 1
                ex = exs_alive[0]

            if ex in matches:
                # Leaf with more than one successor: at most one may be alive
                p2 = matches.pop(ex)
                if not alive(p):
                    forget.add(p)
                    p = p2
                elif not alive(p2):
                    forget.add(p2)
                else:
                    assert not (alive(p) and alive(p2))
            matches[ex] = p
        match_persons = {p: ex for ex, p in matches.items()}
        new_leaves = {}
        for p in r2.personer:
            if p in forget:
                continue
            try:
                ex = match_persons.pop(p)
            except KeyError:
                history = ()
            else:
                history = leaf_navn.pop(ex)
                if history[-1][0].email:
                    email_to_navn.pop(history[-1][0].email)
            new_leaves[p.navn] = history + ((p, t2),)
            if p.email:
                email_to_navn[p.email] = p.navn
        deleted_leaves.extend(leaf_navn.values())
        for v in leaf_navn.values():
            if v[-1][0].email:
                del email_to_navn[v[-1][0].email]
        leaf_navn = new_leaves
    if deleted_leaves:
        print("%s deleted leaves, most recent on %s" %
              (len(deleted_leaves), deleted_leaves[-1][-1][1]))
    return list(leaf_navn.values()), regnskab_history


if __name__ == "__main__":
    main()
