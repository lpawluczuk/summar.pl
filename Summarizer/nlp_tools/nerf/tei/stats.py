"""
Module provides methods for counting statistics both on the
level of labels and on the level on NEs.

Methods work for translated CRF data.
"""

from crf.data import translate as translate
import crf.stats

from ner.errors import errors
from ner.agreement import Agreement
from ner.data import DummySegment
from ner.labels import label2tuple, decode

def _retranslate_sent(sent, rev_alph):
    sent, labels = sent
    return (translate.sentence(sent, rev_alph),
            translate.labels(labels, rev_alph))

def label_stats(data, rev_alph, ner):
    data = (_retranslate_sent(sent, rev_alph) for sent in data)
    return crf.stats.stats(data, ner, ner.alphabet.void_label)

#def name_stats(data, ner, atlas=None, predicate=None, **kwds):
#    if atlas != None:
#        raise NotImplementedError
#    data = (_retranslate_sent(sent, ner.rev_alphabet) for sent in data)
#    agr = Agreement(**kwds)
#    tagged, good, agrees = 0, 0, 0
#    for (sent, labels) in data:
#        segs = [DummySegment(str(i)) for i in range(len(sent))]
#        labels = map(label2tuple, labels)
#        names_tagged = ner.recognize_named_entities(segs, features=sent)
#        names_good = decode(labels, segs)
#        (_tagged, _good, _ok) = agr.get_agreement(names_tagged, names_good,
#                predicate=predicate)
#        tagged += _tagged
#        good += _good
#        agrees += _ok
#
#    prec = rec = 0.0
#    if tagged > 0:
#        prec = float(agrees) / tagged
#    if good > 0:
#        rec = float(agrees) / good
#    if prec == 0.0 and rec == 0.0:
#        F = 0.0
#    else:
#        F = (2*prec*rec) / (prec + rec)
#    # return (tagged, good, agrees, prec, rec, F)
#    return (("Tagged", tagged),
#            ("Good", good),
#            ("Agrees", agrees),
#            ("Precision", prec),
#            ("Recall", rec),
#            ("F-measure", F))

def precision(tagged, good, agrees):
    if tagged > 0:
        return float(agrees) / tagged
    return 0.0

def recall(tagged, good, agrees):
    if good > 0:
        return float(agrees) / good
    return 0.0

def F(tagged, good, agrees):
    prec = precision(tagged, good, agrees)
    rec = recall(tagged, good, agrees)
    if prec == 0.0 or rec == 0.0:
        return 0.0
    else:
        return (2*prec*rec) / (prec + rec)

#def name_stats(data, ner, predicates=[None], **kwds):
#    data = (_retranslate_sent(sent, ner.rev_alphabet) for sent in data)
#    agr = Agreement(**kwds)
#
#    stats = []
#    for _ in predicates:
#        stats.append((0, 0, 0))    # tagged, good, agrees
#
#    for (sent, labels) in data:
#        segs = [DummySegment(str(i)) for i in range(len(sent))]
#        labels = map(label2tuple, labels)
#        names_tagged = ner.recognize_named_entities(segs, features=sent)
#        names_good = decode(labels, segs)
#
#        for i, pred in enumerate(predicates):
#            (tagged, good, ok) = stats[i]
#            (_tagged, _good, _ok) = agr.get_agreement(names_tagged,
#                    names_good, predicate=pred)
#            stats[i] = (tagged + _tagged, good + _good, ok + _ok)
#
#    return stats

def name_stats(data, ner, predicates=[None], **kwds):
    # data = (_retranslate_sent(sent, ner.rev_alphabet) for sent in data)
    agr = Agreement(**kwds)

    stats = []
    for _ in predicates:
        stats.append((0, 0, 0))    # tagged, good, agrees

    for (segs, names_good), _ in data:
        # segs = [DummySegment(str(i)) for i in range(len(sent))]
        # labels = map(label2tuple, labels)
        # names_tagged = ner.recognize_named_entities(segs, features=sent)
        names_tagged = ner.recognize_named_entities(segs)
        # names_good = decode(labels, segs)

        for i, pred in enumerate(predicates):
            (tagged, good, ok) = stats[i]
            (_tagged, _good, _ok) = agr.get_agreement(names_tagged,
                    names_good, predicate=pred)
            stats[i] = (tagged + _tagged, good + _good, ok + _ok)

    return stats

def _old_count_names(name):
    return 1 + sum(_old_count_names(child) for child in name.get_child_names())

def old_count_names(data, rev_alphabet=None):
    """Number of names in data."""
    value = 0
    obset = set()
    for _, (sent, labels) in data:
        segs = [DummySegment(str(i)) for i in range(len(sent))]
        if rev_alphabet is not None:
            labels = translate.labels(labels, rev_alphabet)
        labels = map(label2tuple, labels)
        names = decode(labels, segs)
        for name in names:
            value += _old_count_names(name)
    return value

#def _orth(seginfo):
#    (singles, _) = seginfo
#    for pref in ["4_", "2_"]:
#        for ob in singles:
#            if ob.startswith(pref):
#                return ob.replace(pref, "")
#    return "X"

#def _tagged_data(data, ner):
#    for (sent, labels) in data:
#        segs = [DummySegment(str(i)) for i in range(len(sent))]
#        labels = map(label2tuple, labels)
#        names_tagged = ner.recognize_named_entities(segs, features=sent)
#        names_good = decode(labels, segs)
#        yield map(_orth, sent), names_tagged, names_good

def _count_names(name):
    return len(name.get_descendant_names_and_self())

def count_names(data):
    return sum(_count_names(name)
            for ((_, names), _) in data
            for name in names)

def _tagged_data(data, ner):
    # for (sent, labels) in data:
    for (segs, names_good), _ in data:
        # segs = [DummySegment(str(i)) for i in range(len(sent))]
        # labels = map(label2tuple, labels)
        # names_tagged = ner.recognize_named_entities(segs, features=sent)
        names_tagged = ner.recognize_named_entities(segs)
        # names_good = decode(labels, segs)
        yield segs, names_tagged, names_good
        # yield map(_orth, sent), names_tagged, names_good

def count_errors(data, ner):
    # data = (_retranslate_sent(sent, ner.rev_alphabet) for sent in data)
    return errors(_tagged_data(data, ner))
