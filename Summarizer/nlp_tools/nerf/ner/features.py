#-*- coding: utf-8 -*-

import re
from itertools import groupby

# Represents an abstract "feature".
class Feature(object):
    def value(self, sent, idx):
        raise NotImplementedError("Should use subclass")
    def prefix(self, i):
        return None

# word itself. For segment with orth='Polski' --> 'Polski'
class WORD(Feature):
    def __init__(self, lower=True):
        self.lower = lower

    def value(self, sent, idx):
        orth = sent[idx].orth
        if len(orth) == 0:
            return None
        # return "W_" + (orth.lower() if self.lower else orth)
        return orth.lower() if self.lower else orth

class UPPER_WORD(Feature):
    """Orthografic form, only if has upper character. None otherwise."""
    def value(self, sent, idx):
        orth = sent[idx].orth
        if orth.lower() == orth:
            return None
        # return "UW_" + orth
        return orth

# base form of a word. For segment with orth='Polski' --> 'Polska'
class LEMMA(Feature):
    def __init__(self, lower=True):
        self.lower = lower

    def value(self, sent, idx):
        base = sent[idx].base
        if len(base) == 0:
            return None
        # return "L_" + (base.lower() if self.lower else base)
        return base.lower() if self.lower else base

# specifies if a word starts with capital letter.
# For segment with orth='Polski' --> True
class CAPITALIZED(Feature):
    def value(self, sent, idx):
        orth = sent[idx].orth
        return "CAPITALIZED" if orth[0].isupper() else None

# pecifies if a word contains only capital letters.
# for segment with orth='Polski' --> False
# for segment with orth='POLSKI' --> True
class UPPER_CASE(Feature):
    def value(self, sent, idx):
        return "UPPER" if sent[idx].orth.isupper() else None

# returns word suffix with given lenght.
# for segment with orth='Polski' and n=3 --> 'ski'
class SUFFIX(Feature):
    def __init__(self, n, lower=True):
        self.n = n
        self.lower = lower
        
    def value(self, sent, idx):
        orth = sent[idx].orth
        if abs(self.n) < len(orth):
            suf = orth[-self.n:]
            # return "SUF_" + (suf.lower() if self.lower else suf)
            return suf.lower() if self.lower else suf
        else:
            return None

    def prefix(self, i):
        return "SUF" + str(i)

# returns word prefix with given lenght.
# for segment with orth='Polski' and n=3 --> 'Pol'
class PREFIX(Feature):
    def __init__(self, n, lower=True):
        self.n = n
        self.lower = lower

    def value(self, sent, idx):
        orth = sent[idx].orth
        if abs(self.n) < len(orth):
            pref = orth[:self.n]
            # return "PREF_" + (pref.lower() if self.lower
            #         else pref)
            return pref.lower() if self.lower else pref
        else:
            return None

    def prefix(self, i):
        return "PREF" + str(i)

class SUFFIX_PRIM(SUFFIX):
    def prefix(self, i):
        return "SUFP" + str(i)

class DUMMY_SUFFIX(Feature):
    def __init__(self, lower=True):
        self.lower = lower

    def value(self, sent, idx):
        suf = sent[idx].orth
        return suf.lower() if self.lower else suf

    def prefix(self, i):
        return "SUF" + str(i)

class DUMMY_PREFIX(Feature):
    def __init__(self, lower=True):
        self.lower = lower

    def value(self, sent, idx):
        pref = sent[idx].orth
        return pref.lower() if self.lower else pref

    def prefix(self, i):
        return "PREF" + str(i)

# returns a neighbor word.
# for segment with orth='Polski' and n=-2 in sentence 'Wracam do Polski' --> 'Wracam'
class NEIGHBOR_WORD(Feature):
    def __init__(self, n, lower=True):
        self.n = n
        self.lower = lower
        
    def value(self, sent, idx):
        my_idx = idx
        sent_len = len(sent)
        word_idx = my_idx + self.n
        # feat_pref = ("NEXTW%s_" % self.n) if self.n > 0 else\
        #             ("PREVW%s_" % -self.n)
        if word_idx in range(sent_len):
            orth = sent[word_idx].orth
            # return feat_pref + (orth.lower() if self.lower else orth)
            return orth.lower() if self.lower else orth
        else:
            return None

# returns a neighbor lemma.
# for segment with orth='Polski' and n=-2 in sentence 'Wracam do Polski' --> 'Wracać'
class NEIGHBOR_LEMMA(Feature):
    def __init__(self, n, lower=True):
        self.n = n
        self.lower = lower

    def value(self, sent, idx):
        my_idx = idx
        sent_len = len(sent)
        word_idx = my_idx + self.n
        # feat_pref = ("NEXTL%s_" % self.n) if self.n > 0 else\
        #             ("PREVL%s_" % -self.n)
        if word_idx in range(sent_len):
            base = sent[word_idx].base
            # return feat_pref + (base.lower() if self.lower else base)
            return base.lower() if self.lower else base
        else:
            return None

# returns a part of speech of a word
# for segment with orth='fajny' --> 'adj'
class POS(Feature):
    def _value(self, sent, idx):
        pos = sent[idx].pos
        # return "POS_" + pos if len(pos) > 0 else None
        if len(pos) == 0:
            raise Exception, "empty pos for word " + sent[idx].orth
        return pos
    def value(self, sent, idx):
        # return "POS_" + self._value(sent, idx)
        return self._value(sent, idx)

class POS_PAIR(POS):
    def value(self, sent, idx):
        if idx == 0:
            return None
        # return "PPR_" + (POS._value(self, sent, idx - 1) +
        #         "_" + POS._value(self, sent, idx))
        return (POS._value(self, sent, idx - 1) +
                "_" + POS._value(self, sent, idx))

class CASE(Feature):
    def value(self, sent, idx):
        case = sent[idx].case
        # return "CASE_" + case if case is not None else None
        return case if case is not None else None

class CASE_PAIR(Feature):
    def value(self, sent, idx):
        if idx == 0:
            return None
        pcase = sent[idx - 1].case
        case = sent[idx].case
        if pcase is not None and case is not None:
            # return "CPR_" + pcase + "_" + case
            return pcase + "_" + case
        return None

class POS_CASE(Feature):
    def _value(self, sent, idx):
        pos = sent[idx].pos
        case = sent[idx].case
        if pos != None:
            if case != None:
                return pos + ":" + case
            return pos
        return None
    def value(self, sent, idx):
        val = self._value(sent, idx)
        # return "PC_" + val if val else None
        return val if val else None

class POS_CASE_PAIR(POS_CASE):
    def value(self, sent, idx):
        if idx == 0:
            return None
        # return "PCPR_" + (POS_CASE._value(self, sent, idx - 1) +
        return (POS_CASE._value(self, sent, idx - 1) +
                "_" + POS_CASE._value(self, sent, idx))

# specifies if a space precedes a given word.
# for segment 'Fajny' in sentence 'Fajny samochód.' --> False
# for segment '.' in sentence 'Fajny samochód.' --> True
class NPS(Feature):
    def value(self, sent, idx):
        return sent[idx].nps

class ID(Feature):
    def value(self, sent, idx):
        return "I"

class SHAPE(Feature):
    def _charmap(self, char):
        if char.islower():
            return "l"
        if char.isupper():
            return "u"
        if char.isdigit():
            return "d"
        return "x"
    def _value(self, sent, idx):
        orth = sent[idx].orth
        return ''.join(self._charmap(char) for char in orth)
    def value(self, sent, idx):
        # return "SH_" + self._value(sent, idx)
        return self._value(sent, idx)

class PACKED_SHAPE(SHAPE):
    def _value(self, sent, idx):
        orth = sent[idx].orth
        shape = [self._charmap(char) for char in orth]
        return ''.join(k for k, g in groupby(shape))
    def value(self, sent, idx):
        # return "PSH_" + self._value(sent, idx)
        return self._value(sent, idx)

class SHAPE_PAIR(SHAPE):
    def value(self, sent, idx):
        if idx == 0:
            return None
        # return "SHPR_" + (SHAPE._value(self, sent, idx - 1) +
        return (SHAPE._value(self, sent, idx - 1) +
                "_" + SHAPE._value(self, sent, idx))

class PACKED_SHAPE_PAIR(PACKED_SHAPE):
    def value(self, sent, idx):
        if idx == 0:
            return None
        # return "PSHPR_" + (PACKED_SHAPE._value(self, sent, idx - 1) +
        return (PACKED_SHAPE._value(self, sent, idx - 1) +
                "_" + PACKED_SHAPE._value(self, sent, idx))

#def _seg2f(sent, idx, fname):
#    feature = None # cobym nie mial bledu w Eclipse
#    ran = None
#    exec("feature, ran = " + fname)
#    value = [(feature.value(sent, idx + i), i)
#            for i in ran if idx + i >= 0 and
#            idx + i < len(sent)]
#    return [str(i) + fval for (fval, i) in value if fval != None]

def _seg2f(sent, idx, feature, i):
    if idx + i >= 0 and idx + i < len(sent):
        return feature.value(sent, idx + i)
    return None

def _prepare_features(features):
    return tuple(re.sub("\s+", "_", feat) for feat in features)

def _seg2features(sent, idx, features):
    singles, pairs = [], []
    for k, (is_pair, feature, i) in enumerate(features):
        featval = _seg2f(sent, idx, feature, i)
        if featval != None:
            if feature.prefix(i) is not None:
                featval = feature.prefix(i) + "_" + featval
            else:
                featval = str(k + 1) + "_" + featval
            if is_pair:
                pairs.append(featval)
            else:
                singles.append(featval)
    return _prepare_features(singles), _prepare_features(pairs)

def sent2features(sent, features):
    words = []
    for idx in range(len(sent)):
        words.append(_seg2features(sent, idx, features))
    return words

def _file_lines(filename):
    return map(lambda x: x.strip(), open(filename).readlines())

# Should be implemented in more elegant manner...
def parse_feature_names(featnames):
    result = []
    for line in featnames:
        feature, ran = None, None
        SINGLE = False
        PAIR = True
        exec("is_pair, feature, ran = " + line)
        for i in ran:
            result.append((is_pair, feature, i))
    return result
