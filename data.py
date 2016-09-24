# -*- coding: utf-8 -*-
"""
Created on Sun Jul  3 14:06:50 2016

@author: ALe
"""

from core import *

from numpy import ndarray, resize, linspace
from numpy import min, max, average, median, convolve, correlate, sqrt, std
from numpy import ubyte, isnan, isinf, zeros, ones, array
from numpy.random import random
from scipy.signal import firwin, lfilter
from scipy.spatial.distance import pdist

_NOTCH = _FR = 50.
_SAMPLING = 500
_CONTINUOUS = 1
_UNIT = 'ms'

class rec(runtime, ndarray):
    labels = None
    mirror = ['labels']
    tags = {}
    def __getitem__(this, id):
        if issubclass(type(id), str) and this.labels: id=this.labels.index(id)
        item = super(rec, this).__getitem__(id)
        return rec.read(item, by = this)
    def __setitem__(this, id, value):
        if issubclass(type(id), str) and this.labels: id=this.labels.index(id)
        return super(rec, this).__setitem__(id, value)
    @property
    def is_scalar(this): return this.shape is ()
    @property
    def is_vector(this): return len(this.shape)==1
    @property
    def is_matrix(this): return len(this.shape)>1
    @property
    def is_cube(this): return len(this.shape) == 3
    @property
    def is_binary(this): return this.dtype == ubyte and max(this) == 1
    @property
    def serialized(this):
        if not this.is_vector:
            this.set(_deser=this.T.shape)
            return rec.read(this.T.flatten(), copy=this)
        return this
    @property
    def deserialized(this):
        if this.has('_deser'):
            dims = this._deser; del this._deser
            return rec.read(resize(this, dims).T, copy=this)
        return this
    @property
    def as_matrix(this):
        if this.is_vector: return rec.read([this], to=type(this), by=this)
        return this
    def get_as(this, data):
        source = this
        if issubclass(type(data), ndarray): source = resize(this, data.shape)
        return rec.read(source, to=type(this), by=data)
    def tag(rows, **using):
        for tags in using:
            if issubclass(type(using[tags]), list) and len(rows.marker[0]) == len(using[tags]):
                rows.tags[tags] = using[tags]
    def use(row, marker, **labels):
        row.marker = marker
        row.tag(**labels)
    def select(data, tag, *items):
        set, tag, index = [], {}, [n for n,id in enumerate(data.tags[tag]) if id in items]
        (this, start, end), single = data.marker, len(index)==1
        for row in data:
            if data.is_cube:
                if single: set.append(row[index[0]].tolist())
                else: set.append([row[item].tolist() for item in index])
            else: 
                if single: set.append(row[this[index[0]]-start:this[index[0]]+end].tolist())
                set.append([row[this[marker]-start:this[marker]+end].tolist() for marker in index])
        for name in data.tags:
            tag[name] = [data.tags[name][item] for item in index]
        return record(set, type(data), by=data, tags=tag)
    @staticmethod
    def read(iterable, to = None, **sets):
        template, sets = runtime.take(sets, any=['template', 'by', 'copy'])
        try: sets.update(template._clonable)
        except: pass
        if not to: to = rec
        data = array(iterable).view(to)
        if issubclass(to, runtime): data.set(**sets)
        return data
    def clone(this, **sets):
        copy = this.copy().view(type(this))
        sets.update(this._clonable)
        copy.set(**sets)
        return copy
    def index(these, *labels):
        if not these.labels: return labels
        return [n for n, id in enumerate(these.labels) if id in labels]
    @property
    def _mirrored(sets):
        for set in sets.mirror:
            if hasattr(sets, set): yield rec.read(getattr(sets, set), mirror=[])
            else: yield rec.read(None, mirror=[])
    def _bind(mirror, sets):
        return {key:sets[n] for n,key in enumerate(mirror.mirror)}
    def exclude(rec, *items, **sets):
        reduced, items = [], rec.index(*items)
        sets.update(rec._bind([field.exclude(*items).tolist() for field in rec._mirrored]))
        if rec.is_matrix:
            for n,item in enumerate(rec):
                if n not in items: reduced.append(item)
        return rec.read(reduced, to=type(rec), by=rec).clone(**sets)
    def include(rec, *items, **sets):
        set, items = [], rec.index(*items)
        sets.update(rec._bind([field.include(*items).tolist() for field in rec._mirrored]))
        if rec.is_matrix:
            for item in items: set.append(rec[item])
        return rec.read(set, to=type(rec), by=rec).clone(**sets)

create = record = rec.read

class rnd_range(struct):
    items = 0
    error = .05
    clones = 0
    def __init__(_, **params): _.set(**params)
    def set(_, **params):
        update = 'items' in params
        super(type(_), _).set(**params)
        if update: _._set = [0.]*_.items; _._reset()
    def _reset(space):
        def _(n): return int(round(n))
        def check(error): return average([n-_(n) for n in error])
        set = array(space._set)-min(space._set)+1.
        error = check(set)
        while error>space.error:
            set *= round(1/error)
            error = check(set)
        prev, space._n = 0, []
        for bound in set: space._n.append(prev+_(bound)); prev=space._n[-1]
        space._end = prev
    def update(_, nodes, score):
        for node in nodes: _._set[node] += score
        _._reset()
    def next(_):
        def walk(path, up=0):
            path += up
            next = path-1
            return path, next
        def bound(space):
            bottom, up = _._n[next], _._n[check]
            if next<0: bottom=0
            if space<bottom: return -1
            if (space>bottom and space<=up) or (space==0. and check==0): return 0
            return 1
        find = random()
        (check, next), space = walk(int(find*_.items)), find*_._end
        to = bound(space)
        while to: check, next = walk(check, to); to=bound(space)
        return check
    def __call__(_, batch):
        set = []
        while batch:
            check = _.next()
            if check not in set or _.clones: set.append(check); batch-=1
        return set

class fir(struct):
    frequency = _FR
    width = 3.
    order = 2.
    def __init__(filter, **attributes): filter.set(**attributes)
    def bandstop(notch, frequency=None, sampling=None):
        if not sampling: sampling = _SAMPLING
        if not frequency: frequency = notch.frequency
        nyq, cutoff = sampling / 2., []
        for f in range(int(frequency), int(nyq) + 1, int(frequency)):
            if f + notch.width > nyq: f = nyq - 0.1 - notch.width
            cutoff += (f - notch.width, f + notch.width)
        notch.order *= sampling
        return firwin(notch.order + 1, cutoff, nyq = nyq)
    def tailed(this, vector):
        use = int(this.order/2)
        if issubclass(type(vector), ndarray): vector=vector.tolist()
        start, end = array(vector[:use]), array(vector[-use:])
        return (start+(vector[0]-start[-1])).tolist()+vector+(end+(vector[-1]-end[0])).tolist()

def _to_rec(this):
    if not issubclass(type(this), rec): return rec.read(this, by=this), rec
    return this, type(this)

def notch(this, using=None, sampling=_SAMPLING, **opts):
    data, type = _to_rec(this)
    if not using: using=fir()
    if data.has('sampling'): sampling=data.sampling
    F, rows = using.bandstop(sampling=sampling), []
    for row in data.as_matrix:
        rows.append(lfilter(F, 1., using.tailed(row))[int(using.order):])
    return rec.read(rows, to=type).get_as(data)

def binarize(this, **opts):
    data, type = _to_rec(this)
    if data.is_binary: return data
    rows = []
    for row in data.as_matrix:
        d = row - array([row[-1]]+row[:-1].tolist())
        d[d>=0] = 1; d[d<0] = 0
        rows.append(d.astype(ubyte))
    return rec.read(rows, to=type).get_as(data)

def normalize(matrix, axis = None):
    normalized, (data, type) = [], _to_rec(matrix)
    if axis == 'y': axis = 2
    if axis == 'x': axis = 1
    m, x = min(data), max(data)
    if axis == 2: data = data.T
    for n, line in enumerate(data):
        if axis: m,x=min(line),max(line)
        set = (line-m)/(x-m)
        try:set[isnan(set)]=0.
        except:
            if isnan(set): set = 0.
        normalized.append(set)
    if axis == 2: normalized = array(normalized).T.tolist()
    return rec.read(normalized,to=type).get_as(matrix)

def sliding(fx = average, on = None, window = _SAMPLING, step = _CONTINUOUS):
    coded, (stream, type) = [], _to_rec(on)
    if stream.is_vector: stream = stream.as_matrix
    if len(stream.shape) > 2:
        for dimension in stream: coded.append(sliding(fx, dimension, window, step))
    else:
        for row in stream:
            line,max = [],len(row)
            for _ in xrange(1-window, len(row), step):
                span = _
                if span < 0: span = 0
                line.append(fx(row[span:_+window]))
            coded.append(line[:max])
    return rec.read(array(coded), to=type, by=stream)

def halve(matrix):
    halved, (data, type) = [], _to_rec(matrix)
    for line in data:
        h = resize(line, (len(line)/2, 2))
        halved.append((h[:,0]+h[:,1])/2.)
    return rec.read(halved, to=type, by=data)

def check(this, event=lambda x:x>-1.5):
    data, type = _to_rec(this)
    check = ones(data.shape)
    check[event(data)] = 0
    return check

def mark(this, event, skip=100, before=100, span=500):
    data, type = _to_rec(this)
    if data.is_vector:
        data = check(this, event)
        last, marker = 0, []
        for n, tick in enumerate(data):
            if tick and skip<(n-last):
                marker.append(n); last = n
        return marker, before, span
    return None