#-*- coding: utf-8 -*-

import sys
import os
import re
import string

# Solution with no hard coded path would be welcome
sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])) + "/../")

from ..ner.nerecognizer import NERecognizer
from ..ner.data import Segment
from ..ner.features import sent2features

# Word or punctuation character
word_regex = re.compile('([^%s]+|[%s])' %
        ( re.escape(string.whitespace + string.punctuation)
        , re.escape(string.punctuation)))
def words(line):
    return [(m.group(), m.span()) for m in word_regex.finditer(line)]

class SegmentStruct(Segment):

    def __init__(self, span, *args, **kwargs):
        self.span = span
        Segment.__init__(self, *args, **kwargs)

def line2sent(line):
    return [ SegmentStruct(span, id=str(i), orth=orth)
             for i, (orth, span) in enumerate(words(line)) ]

def name2str(name):
    segs = sorted(name.get_segs(), key=lambda seg: seg.span)
    npss = [True] + [prev.span[1] == curr.span[0]
                     for (prev, curr) in zip(segs, segs[1:])]
    segstr = "".join(
            ("" if nps else " ") + seg.orth
            for (seg, nps) in zip(segs, npss))
    p = min(seg.span[0] for seg in segs)
    q = max(seg.span[1] for seg in segs)
    span_str = "(" + str(p) + ", " + str(q) + ")"
    return (str(".".join(filter(lambda x: x is not None,
        [name.type, name.subtype, name.derivType])))
        + " : " + segstr + " " + span_str)

def print_names(names):
    for root_name in names:
        for name in root_name.get_descendant_names_and_self():
            print name2str(name)

if __name__ == "__main__":
    from optparse import OptionParser
    optparser = OptionParser(usage="""usage: %prog MODEL
        
        NER program, which reads text from stdin
        (each sentence in separate line) and
        writes results to stdout.""")

    (options, args) = optparser.parse_args()
    if len(args) != 1:
        optparser.print_help()
        sys.exit(0)

    model_name = args[0]
    # print "Loading model..."
    ner = NERecognizer.load(model_name)
    # print "Done\n"

    # for line in sys.stdin:
    while True:
        line = sys.stdin.readline()
        if line == "":
            break
        sent = line2sent(line.decode('utf-8').strip())
        names = ner.recognize_named_entities(sent)
        print_names(names)
        print
