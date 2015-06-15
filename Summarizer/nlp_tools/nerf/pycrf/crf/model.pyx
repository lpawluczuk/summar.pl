# encoding: utf-8

"""
Representation of CRF model.
"""

import os
import gzip
import math
import const
from collections import defaultdict

from libc.stdlib cimport malloc, free

include "conns.pxi"

class ParamsIter:
    def __init__(self, model):
        self.model = model
        self.idx = -1
    def next(self):
        self.idx += 1
        if self.idx >= self.model.pn:
            raise StopIteration
        return (self.model.feature(self.idx), self.model.value(self.idx))

def load(filename=None, fileobj=None):
    """Load CRF model saved using custom format."""
    if not fileobj:
        inp = gzip.open(filename, 'rb')
    else:
        inp = fileobj
    features = []
    values = []
    for line in inp:
        f1, f2, f3, val = line.strip().split()
        features.append(map(int, (f1, f2, f3)))
        values.append(float(val))
    cdef Model model = Model(features)
    for i, v in zip(range(model.pn), values):
        model.model.values[i] = v
    return model

cdef class Model:

    """
    Class representing CRF model parameters.

    Representation of CRF model consists of two elements:
    * Alphabet, or map, from strings to observation/label indices.
    * Model parameters, that is list of (feature, value) pairs.
    The Model class is responsible for the representation of the
    second element from the list above.

    Let X be a set of observation indices and Y a set of label indices.
    The following assumptions has to be satisfied:
    * X = {0, 1, ..., |X| - 1}
    * Y = {0, 1, ..., |Y| - 1}

    Model features are of one of the forms:
    * Simple featuer -- (-1, y, x).
    * Compound feature -- (py, y, x),
    """

    def __cinit__(self):
        self.model.pn = 0
        self.model.xn = 0
        self.model.yn = 0
        self.model.dummy_id = 0
        self.model.features = NULL
        self.model.values = NULL
        self.conns = None
        self.fmap = {}

    def _dealloc(self):
        self.fmap.clear()
        if self.model.features is not NULL:
            free(self.model.features)
        if self.model.values is not NULL:
            free(self.model.values)

    def __dealloc__(self):
        self._dealloc()

    def _create_map(self):
        self.fmap.clear()
        for i in range(self.pn):
            feature = self.feature(i)
            self.fmap[feature] = i

    def _observations(self, features):
        value = set()
        for (py, y, x) in features:
            value.add(x)
        return value

    def _labels(self, features):
        value = set()
        for (py, y, x) in features:
            if py != -1:
                value.add(py)
            value.add(y)
        return value

    def __init__(self, features, values=None):
        if values is None:
            values = [0.0] * len(features)
        assert len(features) == len(values)

        self._dealloc()

        # Hard-codding dummy label id. Note, that this has to be
        # consistent with alphabet ! (see alphabet.py)
        self.model.dummy_id = const.dummy_id
        self.model.pn = len(features)

        oset = self._observations(features)
        self.model.xn = max(oset) + 1
        assert oset <= set(range(self.model.xn))
        lset = self._labels(features)
        self.model.yn = max(lset) + 1
        assert lset <= set(range(self.model.yn))

        self.model.features = <int*>malloc(3 * self.pn * sizeof(int))
        if self.model.features is NULL:
            raise MemoryError
        self.model.values = <double*>malloc(self.pn * sizeof(double))
        if self.model.values is NULL:
            raise MemoryError

        for i, (py, y, x) in enumerate(features):
            k = i * 3
            self.model.features[k] = py
            self.model.features[k + 1] = y
            self.model.features[k + 2] = x
        for i, v in enumerate(values):
            self.model.values[i] = v

        self._create_map()
        self.conns = Conns(self)

    property pn:
        def __get__(self):
            return self.model.pn

    property xn:
        def __get__(self):
            return self.model.xn

    property yn:
        def __get__(self):
            return self.model.yn

    property dummy_id:
        def __get__(self):
            return self.model.dummy_id

    def feature(self, i):
        """i-th feature"""
        if i < 0 or i >= self.pn:
            raise ValueError
        value = (self.model.features[i*3],
                self.model.features[i*3 + 1],
                self.model.features[i*3 + 2])
        return value

    def value(self, i):
        """value for the i-th feature"""
        if i < 0 or i >= self.pn:
            raise ValueError
        return self.model.values[i]

    def feature_id(self, feature):
        return self.fmap[feature]

    def __getitem__(self, feature):
        i = self.fmap[feature]
        return self.model.values[i]

    def get(self, feature, default=None):
        try:
            return self[feature]
        except:
            return default

    def __iter__(self):
        return ParamsIter(self)

    def save(self, filename=None, fileobj=None):
        """Save CRF model using custom format."""
        if not fileobj:
            out = gzip.open(filename, 'wb')
        else:
            out = fileobj

        for feature, value in self:
            print >> out, ' '.join(map(str, list(feature) + [value]))

        if not fileobj:
            out.close()

    def log_phi(self, py, y, word):
        value = 0.0
        singles, pairs = word
        for x in singles:
            feature = (-1, y, x)
            value += self.get(feature, 0.0)
        for x in pairs:
            feature = (py, y, x)
            value += self.get(feature, 0.0)
        return value

    # TODO: Count Z constant within the method.
    def prob(self, sentence, labels, log_z, log=True):
        """Probability of the sentence and labels with respect to the model.
        
        :param log_z:
            Logarithm of a Z contstant related to the sentence.
            See CRF specification for more details.
        """
        value = 0.0

        # prev_y = self.alphabet.label(self.alphabet.dummyLabel)
        py = self.dummy_id
        for word, y in zip(sentence, labels):
            value += self.log_phi(py, y, word);
            py = y
            
        value -= log_z
        #if value > 0.:
        #	print 'value > 0 !'
        #	print 'value: ' + str(value)
        #	print 'logZx: ' + str(logZx)
        if not log:
            return math.exp(value)
        return value

    def cll(self, data, z_stats, double i_var2, double coef=1.0):
        """
        :param coef:
            Relative (to the size of entire training set) size of the data.
        """
        cdef double value = 0.0
        cdef int i
        cdef double v

        fl = False
        for (i, (sent, labels)) in enumerate(data):
            logp = self.prob(sent, labels, z_stats[i])
            if logp > 0.0:
                #logp = 0.
                fl = True
            value += logp
            
        coef = coef * 0.5 * i_var2
        for i from 0 <= i < self.pn:
            v = self.model.values[i]
            value -= (v*v) * coef

        if fl:
            print 'problems with numbers precision'
        return value

    def norm_2(self):
        sum2 = 0.0
        for i in range(self.pn):
            v = self.model.values[i]
            sum2 += v*v
        return math.sqrt(sum2)

    def translated(self, from_alph, to_alph):
        """
        Translate model to a new alphabet.
        
        Parameters, which cannot be translated to the new alphabet,
        will be discarded.
        """
        rev_from = from_alph.reversed()
        features, values = [], []
        for feature, value in self:
            feature = rev_from.translate_feature(feature)
            feature = to_alph.translate_feature(feature)
            if feature != None:
                features.append(feature)
                values.append(value)
        return Model(features, values=values)
