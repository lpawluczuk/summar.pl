# encoding: utf-8

from collections import defaultdict

"""
Module provides methods for error analisys.
"""

__all__ = ["errors"]

#FP = "false positive"
#FN = "false negative"
#OK = "ok"

def netype(ne):
    info = [ne.type, ne.subtype, ne.derivType]
    return ":".join(filter(None, info))

def map_ne(root):
    """Map recursively each ne to a pair (type, segments) and
    return created list."""
    all_nes = []
    root_segs = set() 
    for child in root.get_child_names():
        nes, segs = map_ne(child)
        all_nes.extend(nes)
        root_segs.update(segs)
    # root_segs.update(int(seg.id) for seg in root.get_child_segs())
    root_segs.update(root.get_child_segs())
    all_nes.append((netype(root), root_segs))
    return all_nes, root_segs

def map_nes(nes):
    """Map each ne in the nes structure to a pair (type, segments)."""
    value = []
    for ne in nes:
        value.extend(map_ne(ne)[0])
    return value

def dist(ne1, ne2):
    f1, s1 = ne1
    f2, s2 = ne2
    if len(s1 & s2) > 0:
        return len(s1.symmetric_difference(s2)) + int(f1 != f2)
    else:
        return float('inf')

def minarg(f, args):
    result = None
    value = float('inf')
    for arg in args:
        fval = f(arg)
        if fval < value:
            value = fval
            result = arg
    return result

def _tostr(segs):
    return "".join(seg.orth if seg.nps else " " + seg.orth
            for seg in segs).strip()

def stats(l1, l2, ok, no_corresp, pairs):
    fn_errors, subst_errors = [], []
    for ne1 in l1:
        (f1, s1) = ne1
        ne2 = minarg(lambda ne2: dist(ne1, ne2), l2)
        if ne2 is None:
            no_corresp[f1] += 1
            fn_errors.append((f1, s1))
            continue
        (f2, s2) = ne2
        if dist(ne1, ne2) == 0:
            ok[f1] += 1
        elif s1 & s2 != set():
            pairs[(f1, f2)] += 1
            subst_errors.append(((f1, s1), (f2, s2)))
        else:
            no_corresp[f1] += 1
            fn_errors.append((f1, s1))
    return fn_errors, subst_errors

def segs2str(segs):
    return "".join(("" if seg.nps else " ") + seg.orth
            for seg in segs).strip()

def sent_errors(segs, recognized, expected, tp, fp, fn, substs, pairs):
    """
    Collect and return list of errors in one sentence.
    
    :params:
    --------
    tp :
        True positives.
    fp :
        False positives.
    fn :
        False negatives.
    substs :
        Substitutions; dictionary entry for (T1, T2) key means the number
        of occurences, that instead expected T1 named entity, T2 has been
        recognized.
    pairs :
        Pairs, meaning inverse to this of substs.
    """
    # sent = " ".join(orths).encode('utf-8')
    sent = segs2str(segs).encode('utf-8')
    _recognized = map_nes(recognized)
    _expected = map_nes(expected)
    (fp_errors, pair_errors) = stats(_recognized, _expected, tp, fp, pairs)
    (fn_errors, subst_errors) = stats(_expected, _recognized,
            defaultdict(int), fn, substs)
    # fn_errors = [((f, " ".join(orths[i] for i in sorted(s))), sent)
    fn_errors = [((f, segs2str(sorted(s))), sent)
            for (f, s) in fn_errors]
    # fp_errors = [((f, " ".join(orths[i] for i in sorted(s))), sent)
    fp_errors = [((f, segs2str(sorted(s))), sent)
            for (f, s) in fp_errors]
    subst_errors = [(
        (f1, segs2str(sorted(s1))),
        (f2, segs2str(sorted(s2))),
        sent) for (f1, s1), (f2, s2) in subst_errors]
    pair_errors = [(
        (f1, segs2str(sorted(s1))),
        (f2, segs2str(sorted(s2))),
        sent) for (f1, s1), (f2, s2) in pair_errors]
    return (fn_errors, fp_errors, subst_errors, pair_errors)

def errors(data):
    """Perform error analisys given data.
    
    :params:
    --------
    data : iterable
        List of pairs (R, E), where R is a list of recognized NEs, while
        E is a list of NEs present in sentences within the gold corpus.
    """
    tp = defaultdict(int)
    fp = defaultdict(int)
    fn = defaultdict(int)
    substs = defaultdict(int)
    pairs = defaultdict(int)
    fn_errors, fp_errors, subst_errors, pair_errors = [], [], [], []
    for segs, recognized, expected in data:
        sent_fns, sent_fps, sent_substs, sent_pairs = sent_errors(segs,
                recognized, expected, tp, fp, fn, substs, pairs)
        fn_errors += sent_fns
        fp_errors += sent_fps
        subst_errors += sent_substs
        pair_errors += sent_pairs
    return tp, fp, fn, substs, pairs, fn_errors, fp_errors,\
            subst_errors, pair_errors
