# -*- coding: utf-8 -*-
"""
Created on Thu May 19 21:06:29 2016

@author: ALe
"""

from inspect import isfunction, ismethod, isgeneratorfunction, isgenerator, isroutine
from inspect import isabstract, isclass, ismodule, istraceback, isframe, iscode, isbuiltin
from inspect import ismethoddescriptor, isdatadescriptor, isgetsetdescriptor, ismemberdescriptor
from datetime import datetime
from datetime import timedelta as time
from timeit import Timer
from re import match, search, sub, subn, split, findall, finditer

class struct(object):
    @property
    def sets(this): return set(dir(this)) - set(dir(type(this)))
    def set(object, **fields):
        for field in fields: setattr(object, field, fields[field])
    @property
    def _clonable(of):
        sets = of.__dict__.copy()
        sets.update(type(of).__dict__.copy())
        final = sets.copy()
        for key in sets:
            v = sets[key]
            if isfunction(v) or ismethod(v) or isgeneratorfunction(v) or isgenerator(v) \
            or isroutine(v) or isabstract(v) or isclass(v) or ismodule(v) or istraceback(v) \
            or isframe(v) or iscode(v) or isbuiltin(v) or ismethoddescriptor(v) \
            or isdatadescriptor(v) or isgetsetdescriptor(v) or ismemberdescriptor(v) \
            or v is None or v == '__main__' or key == '__module__': final.pop(key)
        return final

class runtime(struct):
    def default(field, name, value):
        try: return getattr(field, name)
        except: setattr(field, name, value)
        return value
    def clear(this, *fields):
        sets = this.sets
        if not fields: fields = sets
        if fields:
            set = [field for field in fields if hasattr(this,field) and not ismethod(getattr(this, field))]
            for field in set:
                if field in sets: delattr(this, field)
                else: setattr(this,field,getattr(type(this),field))
    def get(of, all=None, any=None):
        if all: return [getattr(of,field) for field in all if field in of.__dict__]
        if any:
            try: return [getattr(of,field) for field in any if field in of.__dict__][0]
            except: pass
        return None
    def has(this, *fields):
        return all([hasattr(this, field) for field in fields])
    def hasnt(this, *fields): return not this.has(*fields)
    def check(this, **KV):
        try: check = [KV[key]==this.__dict__[key] for key in KV]
        except: return False
        return all(check)
    def clone(this): 
        clone = type(this)()
        sets = this._clonable
        clone.set(**sets)
        return clone
    @staticmethod
    def wrap(**sets):
        rt = runtime(); rt.__dict__.update(sets)
        return rt
    @staticmethod
    def take(sets, any=[], all=[]):
        sets = runtime.wrap(**sets)
        take = sets.get(all, any)
        sets.clear(*(any+all))
        return take, sets.__dict__

def select(*this, **sets):
    this, all = list(this), []
    if this is []: all, sets = runtime.take(sets, ['all'])
    default, sets = runtime.take(sets, ['d'])
    if len([key for key in sets.keys() if key in this+all])>0:
        return runtime.take(sets, this, all)
    return default, sets

class tree(runtime, dict):
    def __getitem__(this, item):
        if not item in this: this[item] = tree()
        return super(tree, this).__getitem__(item)