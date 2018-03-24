import math
import struct
import functools
import collections


PersonBase = collections.namedtuple(
    'Person',
    'navn titel aliaser email senest total gaeld skjul sendEmail')

ForbrugBase = collections.namedtuple(
    'Forbrug', 'kasser xmas oel vand andet betalt')

PriserBase = collections.namedtuple(
    'Priser', 'oel xmas vand kasser')

ConfigBase = collections.namedtuple(
    'Config', ('visXmas', 'visAndet', 'visBetalt', 'gemSomTekst',
               'caseSensitiv', 'nulGraense', 'graense', 'visSkjulte',
               'emailhvem', 'sendmail', 'emailskabelon', 'version'))

Regnskab = collections.namedtuple('Regnskab', 'personer priser config')


class Person(PersonBase):
    SM_ALDRIG, SM_AENDRING, SM_ALTID = range(3)


class Forbrug(ForbrugBase):
    FMT = '>fiiiff'
    ZERO = object()

    def __add__(self, other):
        if other is Forbrug.ZERO:
            return self
        if type(self) != type(other):
            raise TypeError(type(other))
        return type(self)(*[a+b for a, b in zip(self, other)])

    def __sub__(self, other):
        if other is Forbrug.ZERO:
            return self
        if type(self) != type(other):
            raise TypeError(type(other))
        return type(self)(*[a-b for a, b in zip(self, other)])

    def __le__(self, other):
        if type(self) != type(other):
            raise TypeError(type(other))
        return all(a <= b for a, b in zip(self, other))

    def __abs__(self):
        return math.sqrt(sum(v**2 for v in self))


class Priser(PriserBase):
    FMT = '>ffff'


def get_amount(priser, forbrug):
    return sum(getattr(priser, k) * getattr(forbrug, k)
               for k in Priser._fields) + forbrug.andet


class Config(ConfigBase):
    SSKJUL, SKURSIV, SNORMAL = range(3)
    SM_ALLE, SM_TILMELDTE, SM_NORMAL, SM_TEST, SM_SPOERG = range(5)


def read_regnskab(fp):
    def read_line_break(k):
        if version < 3:
            return
        o = fp.read(1)
        if o != b'\n':
            raise ValueError("Bad line break after %s: %r" % (k, o))

    def unpack(fmt):
        try:
            n = struct.calcsize(fmt)
        except struct.error:
            print(repr(fmt))
            raise
        buf = fp.read(n)
        if len(buf) != n:
            # print("Length is %d" % fp.tell())
            raise ValueError("Read only %d bytes, needed %d" % (len(buf), n))
        o = struct.unpack(fmt, buf)
        if len(o) == 1:
            return o[0]
        else:
            return o

    def unpack_type(t):
        fmt = t.FMT
        o = unpack(fmt)
        return t(*o)

    def unpack_string():
        length = unpack('B')
        s = fp.read(length).decode('latin1')
        read_line_break('string')
        return s

    header = b'TKDATA'
    header1 = header[0:4]
    header2 = header[4:6]
    o1 = fp.read(len(header1))
    if o1 == b'<<<<':
        raise ValueError(
            "Data starts with '<<<<', merge conflict?")
    if o1 != header1:
        if len(o1) != len(header1):
            raise ValueError(
                "Incomplete read: %d != %d" % (len(o1), len(header1)))
        version = 0
        personantal, = struct.unpack('>i', o1)
    else:
        o2 = fp.read(len(header2))
        if o2 != header2:
            raise ValueError("Bad header: %r != %r" % (o2, header2))
        version_byte = fp.read(1)
        V = {b'1': 1, b'2': 2, b'3': 3}
        version = V[version_byte]
        personantal = unpack('>i')
    read_line_break('header')

    personer = []
    if personantal > 1000:
        raise ValueError(personantal, version)
    for i in range(personantal):
        navn = unpack_string()
        email = unpack_string()
        titel = unpack_string()
        aliaser = unpack_string()
        senest = unpack_type(Forbrug)
        read_line_break('senest')
        total = unpack_type(Forbrug)
        read_line_break('total')
        gaeld = unpack('>f')
        read_line_break('gaeld')
        skjul = unpack('>i')
        read_line_break('skjul')
        if version >= 2:
            sendEmail = unpack('>i')
            read_line_break('sendEmail')
        else:
            sendEmail = Person.SM_ALDRIG
        personer.append(
            Person(navn, titel, aliaser, email, senest, total, gaeld, skjul,
                   sendEmail))

    priser = unpack_type(Priser)
    read_line_break('priser')

    if version >= 2:
        visXmas, visAndet, visBetalt, gemSomTekst = unpack('4B')
        caseSensitiv = unpack('4B')
        nulGraense, graense, visSkjulte, emailhvem = unpack('>4i')
        read_line_break('config')
        sendmail = unpack_string()
        emailskabelon = unpack_string()
    elif version == 1:
        visXmas, visAndet, visBetalt, gemSomTekst = unpack('4B')
        caseSensitiv = unpack('4B')
        nulGraense, graense, visSkjulte = unpack('>3i')
        emailhvem = Config.SM_NORMAL
        sendmail = 'sendmail'
        emailskabelon = 'Standard'
    else:
        # version == 0
        visXmas, visAndet = unpack('>2i')
        visBetalt = 1
        gemSomTekst = 0
        caseSensitiv = 1, 1, 1, 1
        nulGraense = graense = 0
        visSkjulte = Config.SSKJUL
        emailhvem = Config.SM_NORMAL
        sendmail = 'sendmail'
        emailskabelon = 'Standard'
    config = Config(visXmas, visAndet, visBetalt, gemSomTekst, caseSensitiv,
                    nulGraense, graense, visSkjulte, emailhvem, sendmail,
                    emailskabelon, version)

    return Regnskab(personer, priser, config)


def person_key(p):
    if p.titel:
        a, t = alder(p.titel)
        titler = 'FORM INKA KASS NF CERM SEKR PR VC'.split()
        try:
            i = titler.index(t)
        except ValueError:
            i = len(titler)
        return (0, a, i, t)
    else:
        if p.aliaser and not p.aliaser.startswith('-'):
            n = p.aliaser
        else:
            n = p.navn
        return (1, n.lower())


def write_regnskab(fp, regnskab):
    def pack(fmt, *args):
        fp.write(struct.pack(fmt, *args))

    # int
    pack_i = functools.partial(pack, '>i')
    # float
    pack_f = functools.partial(pack, '>f')
    # byte
    pack_b = functools.partial(pack, 'B')

    # string
    def pack_s(s):
        pack_b(len(s))
        fp.write(s.encode('latin1'))

    # object
    def pack_o(o):
        pack(o.FMT, *o)

    fp.write(b'TKDATA3')
    pack_i(len(regnskab.personer))
    fp.write(b'\n')
    for p in sorted(regnskab.personer, key=person_key):
        pack_s(p.navn)
        fp.write(b'\n')
        pack_s(p.email)
        fp.write(b'\n')
        pack_s(p.titel)
        fp.write(b'\n')
        pack_s(p.aliaser)
        fp.write(b'\n')
        pack_o(p.senest)
        fp.write(b'\n')
        pack_o(p.total)
        fp.write(b'\n')
        pack_f(p.gaeld)
        fp.write(b'\n')
        pack_i(p.skjul)
        fp.write(b'\n')
        pack_i(p.sendEmail)
        fp.write(b'\n')

    pack_o(regnskab.priser)
    fp.write(b'\n')

    c = regnskab.config
    pack('4B', c.visXmas, c.visAndet, c.visBetalt, c.gemSomTekst)
    pack('4B', *c.caseSensitiv)
    pack('>4i', c.nulGraense, c.graense, c.visSkjulte, c.emailhvem)
    fp.write(b'\n')
    pack_s(c.sendmail)
    fp.write(b'\n')
    pack_s(c.emailskabelon)
    fp.write(b'\n')


def alder(titel):
    if titel != titel.upper():
        return None, titel
    if titel.startswith('G'):
        return 1, titel[1:]
    if titel.startswith('B'):
        return 2, titel[1:]
    if titel.startswith('O'):
        return 3, titel[1:]
    if titel.startswith('TO'):
        return 4, titel[2:]
    if titel.startswith('T'):
        try:
            O = titel.index('O')
        except ValueError:
            return None, titel
        return 3 + int(titel[1:O]), titel[O+1:]
    if titel.startswith('FU'):
        return 0, titel
    if titel.startswith('EFU'):
        return 0, titel
    if titel in 'CERM FORM INKA KASS NF PR SEKR VC'.split():
        return 0, titel
    return None, titel
