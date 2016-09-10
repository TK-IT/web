# encoding: utf8
from __future__ import unicode_literals


def gfyearPP(gfyear, override=None):
    if override and gfyear in override:
        return str(override[gfyear])
    return str(gfyear)[2:] + str(gfyear+1)[2:]


def gfyearPPslash(gfyear, override=None):
    if override and gfyear in override:
        return str(override[gfyear])
    return str(gfyear)[2:] + "/" + str(gfyear+1)[2:]
