# encoding: utf8
from __future__ import unicode_literals


def gfyearPP(gfyear):
    return str(gfyear)[2:] + str(gfyear + 1)[2:]


def gfyearPPslash(gfyear):
    return str(gfyear)[2:] + "/" + str(gfyear + 1)[2:]
