import re


def format_price(p):
    return ("%.2f" % p).replace(".", ",")


def format_price_set(ps):
    return "/".join(map(format_price, sorted(ps)))


def format_count(c):
    return ("%.2f" % c).rstrip("0").rstrip(".").replace(".", ",")


def format(template, context):
    r"""
    >>> format('Hello #TARGET#!', dict(TARGET='world'))
    'Hello world!'
    >>> format('Hello.#SKJULNUL:# Value is #V#',
    ...        dict(V='42'))
    'Hello. Value is 42'
    >>> format('Hello.#SKJULNUL:# Value is #V#\nHello again.',
    ...        dict(V='0'))
    'Hello.\nHello again.'
    >>> format('#SKJULNUL:#Values #X# #Y#',
    ...        dict(X='1', Y='2'))
    'Values 1 2'
    >>> format('#SKJULNUL:#Values #X# #Y#',
    ...        dict(X='1', Y='0'))
    ''
    """
    pattern = r"#([A-Z][^#]*)#"
    res = re.sub(r"\r\n|\n|\r", "\n", template)

    def hide_zero(s):
        if any(context[m.group(1)].strip("0,.") == "" for m in re.finditer(pattern, s)):
            return ""
        else:
            return s

    res = re.sub(r"#SKJULNUL:#(.*\n?)", lambda mo: hide_zero(mo.group(1)), res)
    res = re.sub(pattern, lambda mo: context[mo.group(1)], res)
    res = re.sub(r"\n\n+", "\n\n", res)
    return res
