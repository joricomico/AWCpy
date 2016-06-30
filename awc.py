# -*- coding: utf-8 -*-
"""
Created on Thu Jun 29 13:43:35 2016

@author: ALe
"""

from numpy import array, isnan, uint32, average, fromfile, unpackbits, packbits

class default(dict):
    def __call__(set, default, *attributes):
        for key in attributes:
            if key in set: default = set.pop(key)
        return default

class O1(dict):
    train, limit = 10, 100
    class lnx:
        l, n = 1, 2
        def __add__(this, bit):
            bit, learn, limit = bit
            this.l += bit * learn
            this.n += learn
            if this.n > limit: this.n /= 2.; this.l /= 2.
        def __call__(set, weight): return set.l * weight, set.n * weight
    def __init__(context, **params):
        set = default(params)
        context.bits = set(8, 'bits', 'space')
        context.time = set(8, 'time', 'past')
        context.same = set(False, 'same_front', 'fix')
        context.step = set(1, 'check', 'step')
        context.eval = set(context.time, 'error', 'average')
        train, limit = set((None, None), 'train_limit', 'learn')
        if train is not None: context.train = train
        if limit: context.limit = limit
        context._codes = []
        context._last = None
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
            else: actual[context] = O1.lnx()
        return l/n
    def __add__(last, bit):
        for context in last._codes: last[context] + bit
    def learn(symbol, **data):
        set = default(data)
        data = set(None, 'data', 'stream')
        file = set(None, 'filename', 'file')
        tell = set(False, 'verbose', 'tell')
        if file: data = unpackbits(fromfile(file, dtype = 'ubyte'))
        check, to = None, 0.
        if tell: check = tell*len(data)
        train, limit = symbol.train, symbol.limit
        set, coded, time = [], [], symbol.time
        while time: set.append(list()); time -= 1
        for n, bit in enumerate(data):
            if tell and n%check==0: print '{:.0%}|'.format(to),; to+=tell
            if symbol.same: symbol._make([[n%symbol.bits]]+set[1:])
            else: symbol._make(set)
            coded.append(symbol())
            symbol + (bit, train, limit)
            base = set[0]
            if len(base) == symbol.bits:
                set.insert(1, packbits(base).tolist())
                set.pop(-1)
                set[0] = [bit]
            else: base.append(bit)
        symbol._last = data
        return dict(code=coded, error=abs(coded-data))