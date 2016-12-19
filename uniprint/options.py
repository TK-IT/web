import shlex
import collections


class Option:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.key = None
        self.name = kwargs.pop('name', None)
        if kwargs:
            raise TypeError(kwargs.keys())

    def lp_options(self):
        return [o for arg in self.args for o in
                ((arg,) if isinstance(arg, str) else arg.lp_options())]

    def lp_string(self):
        return ' '.join('-o %s' % shlex.quote(s) for s in self.lp_options())

    def __str__(self):
        return self.name or self.key or self.lp_string()

    def __repr__(self):
        return '<Option %s>' % self.key if self.key else '<Option>'


def set_option_keys(cls):
    for k in dir(cls):
        v = getattr(cls, k)
        if isinstance(v, Option):
            v.key = k
    return cls


@set_option_keys
class Options:
    '''
    >>> Options.booklet.lp_string()
    '-o Booklet=Left'
    >>> Options.parse(Options.booklet.lp_string())
    [<Option booklet>]
    >>> Options.parse(Options.stapled_a5_book.lp_string())
    [<Option stapled_a5_book>]
    '''

    booklet = Option('Booklet=Left')
    a5paper = Option('PageSize=A5')
    fit_to_page = Option('fit-to-page')

    fit_a5 = Option(a5paper, fit_to_page)
    stapled_book = Option(booklet, 'SaddleStitch=On')
    stapled_a5_book = Option(stapled_book, fit_a5,
                             name='Klipset A5-hæfte')

    twosided = Option('Duplex=DuplexNoTumble', name='Tosidet')
    onesided = Option('Duplex=None', name='Enkeltsidet')

    @classmethod
    def get_options(cls):
        values = [getattr(cls, k) for k in dir(cls)]
        options = [v for v in values if isinstance(v, Option)]
        options.sort(key=lambda o: len(o.lp_options()))
        return options

    @classmethod
    def parse(cls, string):
        args = shlex.split(string)
        invalid = [o for o in args[::2] if o != '-o']
        if invalid:
            raise ValueError('Every other argument should be "-o": %s' %
                             (invalid,))
        if len(args) % 2 != 0:
            raise ValueError('Last option not supplied')
        options = args[1::2]

        remaining = collections.Counter(options)
        result = []
        for o in reversed(cls.get_options()):
            o_c = collections.Counter(o.lp_options())
            if (remaining - o_c) + o_c == remaining:
                # o_c contained in remaining
                remaining -= o_c
                result.append(o)
        if remaining:
            raise ValueError("Unrecognized: %s" %
                             ' '.join(remaining.elements()))
        return result


choices = [Options.twosided, Options.onesided, Options.stapled_a5_book]
