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

from tkweb.apps.regnskab.legacy.base import (
    Regnskab, read_regnskab, Person, get_amount, Forbrug, alder,
)


def progress(elements, n=None):
    if n is None:
        elements = list(elements)
        n = len(elements)
    progress.active += 1
    progress.total += n
    progress.w = len(str(progress.total))
    for i, x in enumerate(elements):
        progress.current += 1
        sys.stderr.write('\r\x1B[K(%s/%s) %s' %
                         (str(progress.current).rjust(progress.w),
                          progress.total, x))
        yield x
    progress.active -= 1
    if not progress.active:
        sys.stderr.write('\n')
        progress.current = progress.total = 0


progress.active = progress.current = progress.total = 0


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
    # dates = [re.match(pattern, f.name).group(1) for f in files]
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
    if title.startswith('-'):
        return None, title.lstrip('-')
    is_title = opdater_titel_broken(title)[0]
    age, root = alder(title)
    if not is_title or root in ('', 'EFUIT'):
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
        words = a.split()
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


def get_primary_alias(persons):
    for person_history in persons:
        name = person_history[-1][0].navn

        display_titles = [
            # (t, 'real_title', p.titel.split()[0]) if p.titel else
            (t, 'blank', '') if (p.aliaser or '-').startswith('-') else
            (t, 'primary_alias', p.aliaser.split()[0])
            for p, t in person_history]

        def key(x):
            if x[1] == 'primary_alias':
                return x[2]
            else:
                return ''

        groups = itertools.groupby(display_titles, key=key)
        prev = ''
        prev_time = None
        for s, times in groups:
            time = next(times)[0]
            if prev:
                yield (name, prev_time, time, prev)
            prev = s
            prev_time = time
        if prev:
            yield (name, prev_time, None, prev)


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


def get_alias_dicts(persons, gfyears):
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
    return dicts


def get_primary_alias_dicts(persons):
    aliases = get_primary_alias(persons)
    dicts = []
    for name, start_time, end_time, root in aliases:
        dicts.append(dict(
            name=name, start_time=start_time.strftime('%Y-%m-%dT%H:%M:%S%z'),
            end_time=end_time and end_time.strftime('%Y-%m-%dT%H:%M:%S%z'),
            root=root))
    return dicts


def get_status_dicts(persons):
    statuses = get_statuses(persons)
    statuses = [
        dict(name=o['name'],
             start_time=o['start_time'] and
             o['start_time'].strftime('%Y-%m-%dT%H:%M:%S%z'),
             end_time=o['end_time'] and
             o['end_time'].strftime('%Y-%m-%dT%H:%M:%S%z'))
        for o in statuses]
    return statuses


def check_name_unique(persons):
    name_counter = collections.Counter(p[-1][0].navn for p in persons)
    name_dups = {k: v for k, v in name_counter.items() if v > 1}
    if name_dups:
        print(name_dups)
        raise Exception()


def get_gfyear(regnskab,
               base=(('Bjarke Skjernaa', 'Bjarke Skjer'), 1999, 'KASS')):
    names, year, title = base
    try:
        p = next(p for p in regnskab.personer if p.navn in names)
    except StopIteration:
        print('\n'.join(sorted(p.navn for p in regnskab.personer)))
        raise
    age, title_ = alder(p.titel)
    if title_ != title:
        raise ValueError((p, title))
    return year + age


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--git-dir')
    parser.add_argument('-b', '--backup-dir')
    args = parser.parse_args()
    if not args.git_dir and not args.backup_dir:
        parser.error("must specify at least one data source")
    output, aliases, statuses, primary_aliases = (
        export_data(args.git_dir, args.backup_dir))
    with open('regnskab-aliases.json', 'w') as fp:
        json.dump(aliases, fp, indent=2)
    with open('regnskab-statuses.json', 'w') as fp:
        json.dump(statuses, fp, indent=2)
    with open('regnskab-history.json', 'w') as fp:
        json.dump(output, fp, indent=2)
    with open('regnskab-primary-aliases.json', 'w') as fp:
        json.dump(primary_aliases, fp, indent=2)


def get_data(git_dir, backup_dir, name_trans=None):
    if name_trans is None:
        name_trans = {}
    data_sources = []
    if git_dir:
        data_sources.append(read_regnskab_revisions(git_dir))
    if backup_dir:
        data_sources.append(read_regnskab_backups(backup_dir))
    if not data_sources:
        raise ValueError("At least one data source is required")
    if len(data_sources) == 1:
        data_source = data_sources[0]
    else:
        data_source = heapq.merge(*data_sources)

    persons, regnskab_history = parse_regnskab_dat(data_source, name_trans)
    check_name_unique(persons)
    return persons, regnskab_history


def check_gfyear_sorted(iterable):
    gfyear_list = list(iterable)
    if gfyear_list != sorted(gfyear_list):
        raise Exception("gfyear not sorted")


def export_data(git_dir, backup_dir, name_trans=None):
    persons, regnskab_history = get_data(git_dir, backup_dir, name_trans)
    by_time = get_person_history(persons)
    all_times = sorted(by_time.keys())
    # The set of people is monotonically increasing,
    # so the latest regnskab has all the names.
    # all_names = sorted(by_time[all_times[-1]].keys())
    persons.sort(key=lambda ps: (ps[-1][1], ps[-1][0]))
    gfyears = {k: get_gfyear(r) for k, r in regnskab_history.items()}
    check_gfyear_sorted(gfyears[k] for k in all_times)

    def sub_all_persons(persons):
        return {n: p.total - p.senest for n, p in persons.items()}

    def allclose(a, b):
        d = []
        for n in set(a.keys()) | set(b.keys()):
            x = a.get(n, Forbrug(0, 0, 0, 0, 0, 0))
            y = b.get(n, Forbrug(0, 0, 0, 0, 0, 0))
            d.append(abs(x - y))
        return sum(v**2 for v in d) < 1e-3

    def dict_minus(a, b):
        # return {k: v - b.get(k, type(v).ZERO) for k, v in a.items()}
        return {k: a[k] - v for k, v in b.items()}

    def dict_add(a, b):
        return {k: v + a.get(k, type(v).ZERO) for k, v in b.items()}

    gfs = itertools.groupby(all_times, key=lambda t: gfyears[t])
    resets = []

    def append_reset(time, forbrug_diff):
        if resets and resets[-1]['time'].date() == time.date():
            same_date = resets.pop()
            forbrug_diff = dict_add(same_date['forbrug_diff'], forbrug_diff)
        resets.append(dict(time=time, forbrug_diff=forbrug_diff))

    for gfyear, times in gfs:
        times_subs = ((t, sub_all_persons(by_time[t]))
                      for t in times)
        t1, s1 = next(times_subs)
        for t2, s2 in times_subs:
            if not allclose(s1, s2):
                f = dict_minus(s2, s1)
                append_reset(time=t1, forbrug_diff=f)
            t1, s1 = t2, s2
        forbrug_before_gf = {name: person.senest
                             for name, person in by_time[t1].items()}
        append_reset(time=t1, forbrug_diff=forbrug_before_gf)

    KINDS = ['oel', 'xmas', 'vand', 'kasser']
    output = []
    balance = {}
    for o in resets:
        time = o['time']
        forbrug = o['forbrug_diff']
        prices = regnskab_history[time].priser
        purchase_kinds = [
            dict(key=k, price=getattr(prices, k))
            for k in KINDS]
        payments = {}
        purchases = {}
        names = {}
        emails = {}
        titles = {}
        others = {}
        corrections = {}
        for name in forbrug.keys():
            p = by_time[time][name]
            names[name] = p.navn
            emails[name] = p.email
            if p.titel and not p.titel.startswith('-'):
                titles[name] = p.titel.split()[0]
            if forbrug[name].betalt:
                payments[name] = forbrug[name].betalt
            for k in KINDS:
                a = getattr(forbrug[name], k)
                if a:
                    purchases.setdefault(name, {})[k] = a
            if forbrug[name].andet:
                others[name] = forbrug[name].andet
            purchase_amount = get_amount(prices, forbrug[name])
            new_balance = (balance.get(name, 0) +
                           (purchase_amount - forbrug[name].betalt))
            actual_balance = p.gaeld
            correction = actual_balance - new_balance
            if abs(correction) > 0.001:
                corrections[name] = correction
                new_balance += correction
            balance[name] = new_balance
        output.append(dict(
            time=time.strftime('%Y-%m-%dT%H:%M:%S%z'),
            period=gfyears[time],
            names=names,
            emails=emails,
            titles=titles,
            kinds=purchase_kinds,
            payments=payments,
            purchases=purchases,
            others=others,
            corrections=corrections,
        ))

    aliases = get_alias_dicts(persons, gfyears)
    primary_aliases = get_primary_alias_dicts(persons)
    statuses = get_status_dicts(persons)
    return output, aliases, statuses, primary_aliases


def fix_person_name(person, name_trans):
    d = person._asdict()
    for k in ('navn', 'email'):
        name = d[k]
        name = name.lstrip('\'')
        while '\b' in name:
            name = re.sub(r'.\b', '', name, 1)
        if name == 'Mette Lysgaard Schultz':
            name = 'Mette Lysgaard Schulz'
        name = name_trans.get(name, name)
        d[k] = name
    return type(person)(**d)


def fix_names(iterable, name_trans):
    for time, (personer, priser, config) in iterable:
        personer = [fix_person_name(p, name_trans) for p in personer]
        yield time, Regnskab(personer, priser, config)


def remove_duplicates(iterable):
    prev = None
    for t, r in iterable:
        if r != prev:
            yield t, r
        prev = r


def parse_regnskab_dat(regnskab_dat, name_trans):
    assert isinstance(name_trans, dict)
    regnskab_dat = fix_names(regnskab_dat, name_trans)
    regnskab_dat = remove_duplicates(regnskab_dat)
    regnskab_dat = ((t, r) for t, r in regnskab_dat
                    if t.date() != datetime.date(2008, 5, 3))
    # regnskab_dat = ((t, r) for t, r in regnskab_dat for o in [get_gfyear(r)])

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
                    assert not (alive(p) and alive(p2)), (t2, p, p2)
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
