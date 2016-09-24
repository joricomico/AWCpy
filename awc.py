# -*- coding: utf-8 -*-
"""
Created on Wed Jul  6 20:58:35 2016

Licenced under GPL, Copyright 2016, Alessandro Principe
"""

from core import struct
from data import create, record
from numpy import fromfile, unpackbits, packbits

_DEBUG = 1

class bit:
    def __init__(my, size = 32): my.states = size
    def resize(this, bits):
        n, max = 0, 1
        for bit in bits:
            n += bit * max
            max <<= 1
        n = int(round(n / float(max) * this.states)) - 1
        max, bits = 1, []
        while(max < this.states):
            bits.append((n & max) / max)
            max <<= 1
        return bits

class AWC(struct, dict):
    train, limit = 10, 100
    bits = 8
    time = 8
    blur = None
    same = False
    class lnx:
        l, n = 1, 2
        @property
        def _clone(this):
            copy = lnx()
            copy.l, copy.n = this.l, this.n
            return copy
        def __add__(this, bit):
            bit, learn, limit = bit
            this.l += bit * learn
            this.n += learn
            if this.n > limit: this.n /= 2.; this.l /= 2.
        def __call__(set, weight): return set.l * weight, set.n * weight
    def __init__(context, **params):
        context.set(_codes=[], _last=None, **params)
    def clone(this, **changes):
        copy = AWC()
        copy.set(**this._clonable)
        copy.set(**changes)
        copy.update(this)
        for context in copy: copy[context] = copy[context]._clone
        return copy
    def _make(actual, set):
        actual._codes, context = [], []
        for bits in set:
            context += bits
            actual._codes.append(tuple(context))
    def __call__(actual):
        l, n, w = 1., 2., 1
        for length, context in enumerate(actual._codes):
            w *= len(context)
            if context in actual:
                _l, _n = actual[context](w)
                l += _l; n += _n
            else: actual[context] = AWC.lnx()
        return l/n
    def __add__(last, bit):
        for context in last._codes: last[context] + bit
    def learn(symbol, data=None, file=None, tell=False):
        if file: data = unpackbits(fromfile(file, dtype = 'ubyte'))
        check, to = None, 0.
        if tell: check = tell*len(data)
        train, limit = symbol.train, symbol.limit
        set, coded, time = [], [], symbol.time
        while time: set.append(list()); time -= 1
        for n, bit in enumerate(data.tolist()):
            if tell and n%check==0: print '{:.0%}|'.format(to),; to+=tell
            if symbol.same: symbol._make([[n%symbol.bits]]+set[1:])
            else: symbol._make(set)
            coded.append(symbol())
            symbol + (bit, train, limit)
            base = set[0]
            if len(base) == symbol.bits:
                if symbol.blur: base = symbol.blur.resize(base)
                set.insert(1, packbits(base).tolist())
                set.pop(-1)
                set[0] = [bit]
            else: base.append(bit)
        symbol._last = data
        return dict(code=record(coded, by=data), error=record(abs(coded-data), by=data))