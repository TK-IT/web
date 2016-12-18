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
        return [o for arg in args
                for o in ((arg,) if isinstance(arg, str) else arg.options())]

    def lp_string(self):
        return ' '.join('-o %s' % shlex.quote(s) for s in self.lp_options())


def set_option_keys(cls):
    for k in dir(cls):
        v = getattr(cls, k)
        if isinstance(v, Option):
            v.key = k
    return cls


@set_option_keys
class Options:
    booklet = Option('Booklet=Left')
    a5paper = Option('PageSize=A5')
    fit_to_page = Option('fit-to-page')

    fit_a5 = Option(a5paper, fit_to_page)
    stapled_book = Option(booklet, 'SaddleStitch=On')
    stapled_a5_book = Option(stapled_book, fit_a5,
                             name='Klipset A5-hæfte')

    twosided = Option('Duplex=DuplexNoTumble', name='Tosidet')
    onesided = Option('Duplex=None', name='Enkeltsidet')


choices = [getattr(Options, name)
           for name in 'twosided onesided stapled_a5_book'.split()]
