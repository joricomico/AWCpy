# -*- coding: utf-8 -*-
"""
Created on Sun Jul  3 17:55:04 2016

@author: ALe
"""

from core import runtime, datetime, time
from data import create, record, array
from dateutil import parser as dtp
from numpy import float32, nan

class default(dict):
    def __call__(set, default, *attributes):
        for key in attributes:
            if key in set: default = set.pop(key)
        return default

class parse(str):
    class loop: pass
    default = [' ', '\t', '\r', '\n']
    def use(this, *separators):
        next, result = [], [this]
        for parts in separators:
            for token in result:
                tokens = token.split(parts)
                if len(tokens)>1: next += [these+parts for these in tokens[:-1]] + [tokens[-1]]
                else: next += [part for part in tokens if part is not '']
            next, result = [], next
            for parts in separators:
                for token in result: next += token.partition(parts)
                next, result = [], next
            while '' in result: result.pop(result.index(''))
        return result
    def delete(this, *separators):
        return [token for token in this.use(*separators) if token not in separators]
    def __add__(this, feed):
        return type(this)(super(type(this), this).__add__(feed))
    def __(next, check, this, full = True):
        if issubclass(type(check), str):
            if full: return check == this
            else: return check in this
        next.object.append(check(this))
        return next.object[-1]
    def _(parse, this, token, using = (list, tuple)):
        partial, rule = using
        if type(this) is partial:
            last = False
            for a in this:
                last = parse.__(a, token, full = False)
                if last is False: break
            return last
        elif type(this) is rule:
            for rest in this: token = parse.__(rest, token)
            return token is True
        else: return parse.__(this, token)
    def has(this, *parts, **within):
        this.object = []
        set, parts = default(within), list(parts)
        over = set(None, 'stretch', 'skip')
        part = set(list, 'partial', 'set')
        rule = set(tuple, 'conversion', 'rule')
        seps = set(this.default, 'use', 'separator', 'list')
        all, tokens = this.use(*seps), 0
        skip, repeat, test, once = False, False, parts.pop(0), 0
        while all:
            if not repeat:
                current = all.pop(0)
                while current in seps and len(all)>0: current = all.pop(0)
            else: repeat = False
            try:
                if not this._(test, current, (part, rule)): skip = True
                else:
                    tokens, once, again = 0, 1, test
                    if len(parts)==0: return True
                    else: test = parts[0]
                    if test is not parse.loop: parts.pop(0)
                    else: test = again
            except: skip = True
            if skip:
                skip = False; tokens += 1
                if once and len(parts)>0 and parts[0] == parse.loop:
                    tokens = 0; repeat, once = True, 0
                    parts = parts[1:]
                    if len(parts)==0: return True
                    else: test = parts.pop(0)
            if tokens == over: return False
        return False

class source(runtime):
    def __init__(this, file=None, mask=3): this.set(file=file, masked=mask)
    def check(this, file):
        with open(file, 'r') as file:
            if file.read(8) == '%%%%%%%%': return True
            return False
    def open(this, file=None, verbose=True):
        if this.hasnt('start'):
            if verbose: print 'opening connection...',
            if file: this.file=file
            if this.file and this.check(this.file):
                print 'done.'
                with open(this.file, 'r') as file:            
                    while this.hasnt('start'):
                        line = parse(file.readline())
                        if this.hasnt('master') and line.has(['riginal',':'], dtp.parse, dtp.parse, use='\t'):
                            this.set(master=line.object)
                            if verbose: print 'master time set...',
                        elif this.hasnt('time') and line.has(['xport',':'], dtp.parse, dtp.parse, use='\t'):
                            this.set(time=line.object)
                            if verbose: print 'start time: {}, end time: {}.'.format(this.time[0], this.time[1])
                        elif this.hasnt('units') and line.has(['Uni',':'], str):
                            this.set(units=line.object[0])
                            if verbose: print 'units: {}.'.format(this.units)
                        elif this.hasnt('subject') and line.has(['N', 'a', 'ent', ':'], str, use = ['\t','\r','\n']):
                            name = line.object[0]
                            if not this.masked: this.set(subject=name)
                            else:
                                name,id = name.split(),''
                                name.append(name.pop(0))
                                while this.masked<len(name): name.pop(0)
                                for part in name: id+=part[0]
                                this.set(subject=id)
                            if verbose: print 'subject: {}'.format(this.subject)
                        elif this.hasnt('sampling') and line.has(float, 'Hz', use=['\t',' ','\r','\n']):
                            this.set(sampling=line.object[0])
                            if verbose: print 'sampling rate: {};'.format(this.sampling)
                        elif this.hasnt('channels') and line.has(int, parse.loop, use=['\t',' ','C']):
                            this.set(channels=line.object)
                            if verbose: print '{} channels found, from {} to {}...'.format(len(this.channels), this.channels[0], this.channels[-1]),
                        elif this.hasnt('start') and line.has(dtp.parse, int, list=['\t',' ','OFF']):
                            this.set(start=(position, line.object[1], len(line)))
                            if verbose: print 'source opened at position/tick: {}/{}.'.format(this.start[0], this.start[1])
                        position = file.tell()
            elif verbose: print 'failed!'
    def _seek(this, file, position, within=-5):
        if within>=0: within = -within
        def align(file, line):
            file.seek(file.tell()-line); file.readline()
            return file.tell()
        def tell(file, tick, line):
            file.seek(tick)
            try: return align(file, line), int(parse(file.readline()).delete('\t','OFF')[1])
            except: return random(extent=100,zero=-50)(),random(extent=100,zero=-50)()
        start, tick, length = this.start
        if tick < position:
            on, tick = tell(file, start+(position-tick)*length, length)
            to = tick-position
            while to:
                if to<0:
                    if to>=within:
                        while to: file.readline(); to+=1
                        on = file.tell(); break
                    else: on, tick = tell(file, on-to*length, length)
                else: on, tick = tell(file, on-(to+1)*length, length)
                to = tick-position
            file.seek(on)
        else: file.seek(start)
    def load(this, store=['subject', 'channels', 'units', 'sampling'], **data):
        find = default(data)
        tell = find(True, 'verbose')
        if this.hasnt('start'): this.open(verbose=tell)
        if this.has('start', 'sampling', 'time', 'channels'):
            start = find(this.time[0], 'start', 'at')
            end = find(this.time[1], 'end')
            gap = find(None, 'time', 'span')
            use = find(float32, 'type')
            if type(start) is time: start = this.time[0]+start
            init = start-this.time[0]
            if gap and type(gap) is time: end = start+gap
            if end > this.time[1]: end = this.time[1]
            gap = end-start
            init = int(init.seconds*this.sampling)+this.start[1]
            ticks = int(gap.seconds*this.sampling)
            channels = len(this.channels)
            with open(this.file, 'r') as file:
                if tell: print 'seeking record start...',
                this._seek(file, init)
                if tell: print 'done\nreading lines...',
                lines = [[0]*channels]; last = lines[-1]
                while ticks:
                    line = file.readline()
                    if line == '': break
                    line = array([t for t in line.split('\t') if t!='OFF'][2:-1])
                    if len(line)==channels:
                        line[line == 'SHORT'] = nan
                        line[line == 'AMPSAT'] = nan
                        if nan in line:
                            to = correct = line.tolist()
                            while nan in correct:
                                position = to.index(nan)
                                correct[position] = last[position]
                            line = array(correct)
                        lines.append(line.astype(use))
                        last = lines[-1]
                        ticks -= 1
                if tell: print 'done'
                data = create(record(lines[1:]).T, template=this, start=start, end=end, gap=ticks/this.sampling)
                data.clear(*list(this.sets-set(store)))
                return data
        elif tell: print 'invalid source!'
    def feed(this, start=time(), end=None, step=time(minutes=1), span=None, tell=True):
        within = span
        if not within:
            at, end = this.time
            within = end-at-step
        while start<within:
            try: yield this.load(start=start, time=step)
            except:
                if tell: print 'broken stream at {}!'.format(start)
                yield None