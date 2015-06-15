# encoding: utf-8

import re
from itertools import izip

from crf.data.dataset import DataSet, divide_data, divide_in_two

CASES = ["nom", "gen", "dat", "acc", "inst", "loc", "voc"]
CASE_REGEX = re.compile("(^|:)(%s)($|:)" % '|'.join(CASES))

class Segment(object):
    
    def __init__(self, id, orth="?", base="?", pos="?", morph="?", nps=False):
        self._id = id
        self._nps = nps
        self._orth = orth
        self._base = base
        self._pos = pos
        self._morph = morph
        self._case = self._get_case(morph)
    
    @property
    def id(self):
        return self._id
    
    @property
    def nps(self):
        return self._nps
    
    @property
    def orth(self):
        return self._orth
    
    @property
    def base(self):
        return self._base
    
    @property
    def pos(self):
        return self._pos

    def _get_case(self, morph):
        match = CASE_REGEX.search(morph)
        assert match != None if self._pos in ["subst", "depr", "ger",
                "ppron12", "ppron3", "num", "numcol", "adj", "pact",
                "ppas", "prep", "siebie"] else match == None
        if match != None:
            return match.group(2)
        return None

    @property
    def case(self):
        return self._case
    
    @property
    def morph(self):
        return self._morph
    
    def __eq__(self, other):
        return (self.id, self.orth, self.base, self.pos, self.morph) \
            == (other.id, other.orth, other.base, other.pos, other.morph)
    
    def __hash__(self):
        return hash(self.id)
    
    def __repr__(self):
        return ('Segment(id=%s, orth=%s, interp=%s)' \
                % (self.id,
                   self.orth, 
                   ':'.join([self.base, self.pos, self.morph]))) \
                .encode('utf-8', 'ignore')

class DummySegment(Segment):

    def __init__(self, id):
        Segment.__init__(self, id, "?", "?", "?", "?")

    def __repr__(self):
        return "DummySegment(id=%s)" % self.id

class NamedEntity(object):
    
    def __init__(self, 
                 id, 
                 type, 
                 subtype, 
                 ptrs, 
                 base=None,
                 derivType=None, 
                 derivedFrom=None):
        self._id = id
        self._type = type
        self._subtype = subtype
        self._ptrs = ptrs
        self._base = base
        self._derivType = derivType
        self._derivedFrom = derivedFrom
    
    @property
    def id(self):
        return self._id
    
    @id.setter
    def id(self, id):
        self._id = id
    
    @property
    def type(self):
        return self._type
    
    @property
    def subtype(self):
        return self._subtype
    
    @property
    def ptrs(self):
        return self._ptrs
    
    @property
    def derivType(self):
        return self._derivType
    
    @property
    def derivedFrom(self):
        return self._derivedFrom
    
    @property
    def base(self):
        return self._base
    
    def get_segs(self):
        res = []
        for ptr in self.ptrs:
            if isinstance(ptr, Segment):
                res.append(ptr)
            else: 
                res.extend(ptr.get_segs())
        return res

    def get_child_segs(self):
        return [ptr for ptr in self.ptrs if isinstance(ptr, Segment)]
    
    def get_child_names(self):
        return [ptr for ptr in self.ptrs if isinstance(ptr, NamedEntity)]
    
    def get_descendant_names_and_self(self):
        return [self] + self.get_descendant_names()
    
    def get_descendant_names(self):
        res = []
        for name in self.get_child_names():
            res.extend(name.get_descendant_names_and_self())
        return res
    
    def get_label(self):
        if self.subtype != None:
            out = self.type + "." + self.subtype
        else:
            out = self.type
        if self.derivType != None:
            out = out + "@" + self.derivType
        return out

    def _get_orth(self):
        out = []
        for ptr in self.ptrs:
            if isinstance(ptr, NamedEntity):
                out.append(ptr._get_orth())
            else:
                if not ptr.nps:
                    out.append(' ')
                out.append(ptr.orth)
        return ''.join(out)
    
    @property
    def orth(self):
        return self._get_orth().strip()
    
    def __eq__(self, other):
        return self is other
    
    def __hash__(self):
        return hash(self.id)
    
    def _ptrs_str(self):
        res = ['[']
        for ptr in self.ptrs:
            res.append(ptr.id)
            if len(self.ptrs) > 1:
                res.append(', ')
        res.append(']')
        return ''.join(res)
    
    def __repr__(self):
        out = ['NamedEntity(']
        out.append('id=%s, type=%s, ' % (self.id, self.type))
        if self.subtype is not None:
            out.append('subtype=%s, ' % self.subtype)
        if self.base is not None:
            out.append('base=%s, ' % self.base)
        if self.derivType is not None:
            out.append('derivType=%s, ' % self.derivType)
        if self.derivedFrom is not None:
            out.append('derivedFrom=%s, ' % self.derivedFrom)
        out.append('ptrs=%s)' % self._ptrs_str())
        return ''.join(out)

    def __str__(self):
        val = ""
        for seg in sorted(self.get_segs(), key=lambda seg: seg.id):
            val += str(seg) + "\n"
        return val.strip()

def flatten(l):
    result = []
    for subl in l:
        result.extend(subl)
    return result

def join_names(names1, names2, discard_nested=True):
    """Try to put NEs from names2 list to names1 list; return joined lists."""
    if discard_nested != True:
        raise NotImplementedError
    coverage = set(flatten(ne.get_segs() for ne in names1))
    result = names1
    for ne in names2:
        if set(ne.get_segs()) & coverage == set():
            result.append(ne)
    return result

class NerDataSet(DataSet):

    """CRF DataSet extended with NEs for each sentence."""

    def __init__(self, rdata, *args, **kwargs):
        self.raw_data = [raw_sent for raw_sent, _ in rdata]
        DataSet.__init__(self, [sent for _, sent in rdata], *args, **kwargs)

    def iterator(self):
        return ((raw_sent, sent)
                for raw_sent, sent
                in izip(self.raw_data, self.data))

    def divide(self, n, stat=(lambda x: 1)):
        """Divide dataset data to n parts."""
        return divide_data(self.iterator(), self.dirs, n, stat=stat)

    def divide_in_two(self, r):
        return divide_in_two(self.iterator(), self.dirs, r)

def filter_raw(data):
    return [sent for (raw_sent, sent) in data]
