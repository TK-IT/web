class Container:
    def __init__(self):
        self.parts = []

    def append(self, v):
        self.parts.append(v)

    def __bool__(self):
        return True

    def __len__(self):
        return len(self.parts)

    def __getitem__(self, idx):
        return self.parts[idx]

    def to_list(self):
        def gen():
            b = []
            for j, v in enumerate(self.parts):
                if isinstance(v, Container):
                    v = v.to_list()
                if isinstance(v, str):
                    b.append(v)
                else:
                    t = ''.join(b)
                    if t:
                        yield t
                    yield v
                    del b[:]
            t = ''.join(b)
            if t:
                yield t

        res = list(gen())
        return res[0] if len(res) == 1 else '' if len(res) == 0 else res

    def size(self):
        return sum(len(v) if isinstance(v, str) else v.size() for v in self)

    def iter_sections(self, level):
        for v in self.iter_containers():
            yield from v.iter_sections(level)

    def iter_containers(self):
        return (v for v in self
                if isinstance(v, Container) and not isinstance(v, Leaf))


class Root(Container):
    pass


class Preamble(Container):
    def to_list(self):
        return ('Preamble',)

    def size(self):
        return 0


class Standalone(Container):
    level = -1

    def iter_sections(self, level):
        if level >= self.level:
            yield self
        if level > self.level:
            for v in self.iter_containers():
                yield from v.iter_sections(level)


class Document(Standalone):
    pass


class DocSection(Container):
    def __init__(self, level, name, star):
        super().__init__()
        self.level = level
        self.name = name
        self.star = star

    def append(self, v):
        if isinstance(v, DocSection):
            assert v.level >= self.level
        super().append(v)

    def to_list(self):
        return (self.level, self.name.to_list(), super().to_list())

    def iter_sections(self, level):
        if level >= self.level:
            yield self
        if level > self.level:
            yield from super().iter_sections(level)


class DocPostamble(Container):
    def append(self, v):
        if not isinstance(v, str) or v.strip():
            print(v)
            raise Exception('Postamble must only contain whitespace')
        super().append(v)


class DocListItem(Container):
    def to_list(self):
        return (super().to_list(),)


class DocList(Container):
    def __init__(self, kind):
        super().__init__()
        self.preamble = DocListItem()
        self.kind = kind

    def to_list(self):
        return (self.kind, super().to_list())


class DocBraced(Container):
    pass


class Leaf(Container):
    def __init__(self, *args):
        super().__init__()
        self.args = args

    def append(self, v):
        raise Exception('Cannot append to a leaf')

    def to_list(self):
        res = [self.__class__.__name__]
        for v in self.args:
            if isinstance(v, Container):
                res.append(v.to_list())
            else:
                res.append(v)
        return tuple(res)


class Label:
    def __init__(self):
        self._target = None

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        self._target = value


class DocReference(Leaf):
    def __init__(self, kind, target):
        super().__init__()
        assert isinstance(target, Label)
        self.kind = kind
        self.target = target

    def to_list(self):
        target = self.target.target
        if isinstance(target, DocSection):
            return ('Reference', self.kind, target.name.to_list())
        else:
            return ('Reference', self.kind, repr(target))


class DocAnonBreak(Leaf):
    pass


class DocFormatted(Leaf):
    def to_list(self):
        return ('DocFormatted', self.args[0], self.args[1].to_list())


class DocVerbatim(Leaf):
    pass


class DocFixme(Leaf):
    pass


class DocFootnote(Leaf):
    pass


class DocAbbreviation(Leaf):
    tr = {
        'dots': '...',
        'TK': 'TÅGEKAMMER',
        'TKET': 'TÅGEKAMMERET',
        'TKETAA': 'TAAGEKAMMERET',
        'TKurl': 'https://www.TAAGEKAMMERET.dk',
        'KASS': 'KA$$',
        'CERM': 'CERM',
        'VC': 'VC',
        '``': '\N{LEFT DOUBLE QUOTATION MARK}',
        "''": '\N{RIGHT DOUBLE QUOTATION MARK}',
        '"`': '\N{LEFT DOUBLE QUOTATION MARK}',
        '"\'': '\N{RIGHT DOUBLE QUOTATION MARK}',
        '`': '\N{LEFT SINGLE QUOTATION MARK}',
        "'": '\N{RIGHT SINGLE QUOTATION MARK}',
        '\\\\': '\n',
    }

    def to_list(self):
        return self.tr[self.args[0]] + self.args[1]


class DocSpacing(Leaf):
    pass
