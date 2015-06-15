# encoding: utf-8

import sys
import os

# Solution with no hard coded path would be welcome
sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])) + "/../")

import traceback
from itertools import izip
import copy
from collections import defaultdict

from ner.data import Segment, NamedEntity

from tei.read import TEIReader
import tei.write as write
from tei.corpus import corpus_dirs

# Czy rozwiazywac ewentualne roznice pomiedzy segmentacjami ?
REPAIR = True

def flatten(l):
    result = []
    for subl in l:
        result.extend(subl)
    return result

def LCS(X, Y):
    m = len(X)
    n = len(Y)
    # An (m+1) times (n+1) matrix
    C = [[0] * (n+1) for i in range(m+1)]
    for i in range(1, m+1):
        for j in range(1, n+1):
            if X[i-1] == Y[j-1]: 
                C[i][j] = C[i-1][j-1] + 1
            else:
                C[i][j] = max(C[i][j-1], C[i-1][j])
    return C[m][n]

def sameness(s1, s2):
    lcs = float(LCS(s1, s2))
    return min(lcs / len(s1), lcs / len(s2))

def orth(x):
    return x.orth if x.nps else " " + x.orth

def getfirst(l, k):
    res = ""
    for x in l:
        res += orth(x)
        if len(res) >= k:
            break
    return res[:k]

def getlast(l, k):
    res = ""
    for x in reversed(l):
        res = orth(x) + res
        if len(res) >= k:
            break
    return res[-k:]

def signal_diff(main, other, main_done, other_done, m, n, window_width=30):
    ww = window_width
    if REPAIR and sameness(getfirst(main, ww), getfirst(other, ww)) > 0.75:
        pass
    else:
        k = m - n
        main_orth = getlast(main_done, ww) + getfirst(main, ww)
        other_orth = getlast(other_done, ww - k) + getfirst(other, ww + k)
        print "FILE1:", main_orth.encode('utf-8'), "["+str(main[0].id)+"]"
        print "FILE2:", other_orth.encode('utf-8'), "["+str(other[0].id)+"]"
        k = 6 if main[0].nps else 7
        print " " * (k + len(getlast(main_done, ww))), "▲"
        # print "[" + str(sameness(main_orth, other_orth)) + "]"
        raise Exception("synchronization error")

def orth_eq(orth1, orth2):
    orth1 = orth1.replace(u"­", "-").replace(u"–", "-")
    orth2 = orth2.replace(u"­", "-").replace(u"–", "-")
    return orth1 == orth2

def align_map(main, other):
    """
    Align two sequences of segments.

    Return map (seg \in main) -> (segs \subset other).
    """
    main = copy.copy(main)
    other = copy.copy(other)
    main_done = []
    other_done = []
    m, n = 0, 0
    map = defaultdict(set)
    # log = [] #@
    while len(main) > 0 and len(other) > 0:
        main_orth = main[0].orth
        # main_orth = orth(main[0])
        other_orth = other[0].orth
        # other_orth = orth(other[0])
        # log.append((main_orth, other_orth)) #@
        map[main[0]].add(other[0])
        imin, imax = max(m, n), min(m + len(main_orth), n + len(other_orth))
        if not orth_eq(main_orth[imin - m : imax - m],
                other_orth[imin - n : imax - n]):
            # import pdb; pdb.set_trace()
            signal_diff(main, other, main_done, other_done, m, n)
        if m + len(main_orth) == n + len(other_orth):
            m += len(main_orth); main_done.append(main.pop(0))
            n += len(other_orth); other_done.append(other.pop(0))
        elif m + len(main_orth) < n + len(other_orth):
            m += len(main_orth); main_done.append(main.pop(0))
        else:
            n += len(other_orth); other_done.append(other.pop(0))
    if max(len(main), len(other)) > 0:
        # import pdb; pdb.set_trace()
        raise Exception("synchronization failed")
    return map

def substitute_segs(name, map):
    """Substitute map[segment] for each segment descendant."""
    segs = name.get_child_segs() 
    segs = flatten(map[seg] for seg in segs)
    nes = name.get_child_names()
    nes = [substitute_segs(ne, map) for ne in nes]
    return NamedEntity(name.id,
            name.type,
            name.subtype, 
            ptrs=(nes + segs),
            base=name.base,
            derivType=name.derivType,
            derivedFrom=name.derivedFrom)

#def repair_name(name):
#    """Repair NE if corrupted after segmentation synchronization."""
#    nes_with_segs = [repair_name(ne) for ne in name.get_child_names()]
#    segs = name.get_child_segs()
#    seg_sets = dict((ne, set(ne.get_segs())) for ne in nes)
#
#    # remove NE children when their segment sets intersect
#    nes_ok = []
#    def check(ne, nes, seg_sets):
#        for other_ne in nes:
#            if len(seg_sets[ne] & seg_sets[other_ne]) > 0:
#                nes.remove(other_ne)
#                return False
#        return True
#    while len(nes) > 0:
#        ne = nes.pop()
#        if check(ne, nes, seg_sets):
#            nes_ok.append(ne)
#
#    return NamedEntity(name.id,
#            name.type,
#            name.subtype, 
#            ptrs=(nes_ok + segs),
#            base=name.base,
#            derivType=name.derivType,
#            derivedFrom=name.derivedFrom)

def _add_to_group(name, names_grouped, segmap):
    name_segs = name.get_segs()
    name_segs = set(segmap[seg] for seg in name_segs)
    if len(name_segs) > 1:
        print "WARNING: Named Entity on intersection of sentences"
        print name
        for ne in name.get_child_names():
            _add_to_group(ne, names_grouped, segmap)
    else:
        names_grouped[name_segs.pop()].append(name)

def group_names(names, segs):
    # segment -> sentence map
    segmap = {}
    names_grouped = {}
    for i, sent_seg in enumerate(segs):
        names_grouped[i] = []
        for seg in sent_seg:
            segmap[seg] = i
    for name in names:
        _add_to_group(name, names_grouped, segmap)
    return [sent_names for i, sent_names in sorted(names_grouped.items())]

#def sync_with_segs(fromnames, fromsent, tosent):
#    map = align_map(fromsent, tosent)
#    names = [substitute_segs(name, map)
#            for name in fromnames]
#    # names = [repair_name(name) for name in names]
#    # return group_names(names, morph_segs), morph_segs
#    return names

def sync_with_segs(fromnames, fromsegs, tosegs):
    map = align_map(flatten(fromsegs), flatten(tosegs))
    names = [substitute_segs(name, map)
            for sent_names in fromnames
            for name in sent_names]
    # names = [repair_name(name) for name in names]
    return group_names(names, tosegs)

#def sync_contents(from_contents, to_contents):
#    fromids, fromsents, fromnames = zip(*from_contents)
#    toids, tosents = zip(*to_contents)
#    names = sync_with_segs(fromnames, fromsents, tosents)
#    for sent_id, sent_names in zip(toids, names):
#        yield sent_id, sent_names
#
#    for (fromid, fromsent, fromnames), (toid, tosent) in izip_longest(
#            from_contents, to_contents):
#        names = sync_with_segs(fromnames, fromsent, tosent)
#        yield from, names


def sync_names(fromdir, todir, ann_named="ann_named.xml"):
    fromreader = TEIReader(fromdir)
    toreader = TEIReader(todir)

    fromnames, fromsegs = zip(*fromreader.names(ann_named))
    tosegs = list(toreader.segments())
    
    names = sync_with_segs(fromnames, fromsegs, tosegs)

    for parid, sents in toreader.paragraphs():
        snum = len(list(sents))
        yield names[:snum]
        names = names[snum:]

    assert len(names) == 0

#    for (from_parid, from_contents), (to_parid, to_contents) in izip_longest(
#            from_reader.paragraphs_with_names(ann_named),
#            to_reader.paragraphs()):
#        yield (to_parid, sync_contents(from_contents, to_contents))

def iter_contents(parcontents, parnames):
    for names, (sentid, contents) in izip(parnames, parcontents):
        yield sentid, names

def converted(fromdir, todir, ann_named="ann_named.xml"):
    names = sync_names(fromdir, todir, ann_named)
    reader = TEIReader(todir)
    for parnames, (parid, contents) in izip(names, reader.paragraphs()):
        yield (parid, iter_contents(contents, parnames))

def move_names(from_tei, to_tei, ann_named="ann_named.xml"):
    """
    Move ann_named.xml files from TEI corpus to another TEI corpus
    (with possibly different annotations on lower levels).
    
    :params:
    --------
    from_tei : path
        Path to TEI corpus.
    to_tei : path
        Path to another TEI corpus.
    ann_named : str
        Use this name to find NE files.
    """
    for dirname in corpus_dirs(from_tei, ann_named):
        print "Directory:", dirname
        try:
            fromdir = os.path.join(from_tei, dirname)
            todir = os.path.join(to_tei, dirname)
            with open(os.path.join(todir, ann_named), "w") as out:
                write.write(out, converted(fromdir, todir, ann_named))
        except:
            print traceback.format_exc()

if __name__ == "__main__":
    from optparse import OptionParser
    optparser = OptionParser(usage="""usage: %prog,

        Move ann_named.xml files from TEI corpus to another TEI corpus
        (with, possibly, different annotations on lower levels).""")
	
    optparser.add_option("--from-tei", metavar="DIR", dest="from_tei")
    optparser.add_option("--to-tei", metavar="DIR", dest="to_tei")
    optparser.add_option("--ann-named", type="string",
            dest="ann_named", default="ann_named.xml",
            help="Names of ann_named files.")

    (options, args) = optparser.parse_args()
    if options.from_tei == None:
        optparser.print_help()
        print "\n--from-tei option is mandatory"
        sys.exit(0)
    if options.to_tei == None:
        optparser.print_help()
        print "\n--to-tei option is mandatory"
        sys.exit(0)

    move_names(options.from_tei, options.to_tei, options.ann_named)
