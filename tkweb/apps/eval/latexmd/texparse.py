import re


class _const:
    def __init__(self, s):
        self.s = s

    def __str__(self):
        return self.s

    def __repr__(self):
        return self.s


UNMATCHED = _const('UNMATCHED')


def get_contents_autotex(filename):
    try:
        with open(filename) as fp:
            return fp.read()
    except FileNotFoundError:
        with open(filename + '.tex') as fp:
            return fp.read()
    except Exception:
        print("In", filename)
        raise


def parse_compiled(pattern, contents, push_file, start_line=1):
    ifstack = []
    ifs = {'draftdoc': False, 'kbest': False}
    while True:
        prev_end = 0
        for mo in re.finditer(pattern, contents):
            unmatched = contents[prev_end:mo.start(0)]
            if unmatched:
                if all(ifstack):
                    yield UNMATCHED, (unmatched,)
            key = mo.lastgroup
            groups = tuple(v for v in mo.groups() if v is not None)
            if key == '_comment':
                pass
            elif key == '_escaped':
                if all(ifstack):
                    yield UNMATCHED, groups
            elif key == '_input':
                _, f = groups
                if all(ifstack):
                    push_file(f)
            elif key == '_newif':
                _, ifkey = groups
                ifs[ifkey] = False
            elif key == '_if':
                _, ifkey = groups
                ifstack.append(ifs.get(ifkey, True))
            elif key == '_else':
                try:
                    ifstack[-1] = not ifstack[-1]
                except IndexError:
                    print('Error: Unmatched \\else at line',
                          start_line + contents[:mo.start(0)].count('\n'))
                    raise
            elif key == '_fi':
                try:
                    ifstack.pop()
                except IndexError:
                    print('Error: Unmatched \\fi at line',
                          start_line + contents[:mo.start(0)].count('\n'))
                    raise
            elif key == '_setif':
                _, ifkey, ifvalue = groups
                if ifkey in ifs:
                    ifs[ifkey] = ifvalue == 'true'
                else:
                    if all(ifstack):
                        yield UNMATCHED, (_,)
            else:
                if all(ifstack):
                    yield key, groups
            prev_end = mo.end(0)
        else:
            break
    if ifstack:
        print('Warning: Unmatched \\if')
    unmatched = contents[prev_end:]
    if unmatched:
        yield UNMATCHED, (unmatched,)


class Parser:
    def __init__(self, pattern, get_contents):
        self.pattern = pattern
        self.get_contents = get_contents
        self.stack = []

    def push_file(self, filename):
        self.stack.append(
            parse_compiled(self.pattern, self.get_contents(filename),
                           self.push_file))

    def push_synthetic(self, events):
        self.stack.append(iter(events))

    def __iter__(self):
        return self

    def __next__(self):
        while self.stack:
            try:
                return next(self.stack[-1])
            except StopIteration:
                self.stack.pop()
        raise StopIteration


def parse(user_patterns, filename, get_contents=get_contents_autotex):
    '''
    >>> files = {'a.tex': r'a\input{b.tex}c', 'b.tex': 'hej'}
    >>> list(parse([], 'a.tex', files.__getitem__))
    [(UNMATCHED, ('a',)), (UNMATCHED, ('hej',)), (UNMATCHED, ('c',))]
    '''
    patterns = [
        ('_comment', r'%[^\n]*(?:\n|$)'),
        ('_input', r'\\input{([^}]*)}'),
        ('_newif', r'\\newif\\if([a-z@]+)'),
        ('_if', r'\\if([a-z@]+)'),
        ('_else', r'\\else\b'),
        ('_fi', r'\\fi\b'),
        ('_setif', r'\\([a-z@]+)(true|false)\b'),
    ] + list(user_patterns) + [
        ('_escaped', r'\\(?:\w+|.)'),
    ]
    pattern = '|'.join('(?P<%s>%s)' % (k, p) for k, p in patterns)
    parser = Parser(pattern, get_contents)
    parser.push_file(filename)
    return parser
