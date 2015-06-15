#-*- coding: utf-8 -*-

import sys
import os
import time
import re
from threading import Thread
from Queue import Queue
import string
from ner_io import line2sent, name2str
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

class NERService(object):

    def __init__(self, ner, input, output):
        self.ner = ner
        self.input = input
        self.output = output
    
    def group_input(self):
        result = []
        while True:
            line = self.input.get()
            if line is None:
                break
            yield [SegmentStruct(span, id=str(i), orth=orth)
                for i, (orth, span) in enumerate(words(line))]

    def name2str(self, name):
        segs = sorted(name.get_segs(), key=lambda seg: seg.span)
        npss = [True] + [prev.span[1] == curr.span[0]
                         for (prev, curr) in zip(segs, segs[1:])]
        segstr = "".join(
                ("" if nps else " ") + seg.orth
                for (seg, nps) in zip(segs, npss))
        p = min(seg.span[0] for seg in segs)
        q = max(seg.span[1] for seg in segs)
        span_str = "(" + str(p) + ", " + str(q) + ")"
        return (".".join(filter(lambda x: x is not None,
            [name.type, name.subtype, name.derivType]))
            + " : " + segstr + " " + span_str)
    
    def output_names(self, root_names):
        names = [ name
                  for root_name in root_names
                  for name in root_name.get_descendant_names_and_self() ]
        self.output.put(len(names))
        for name in names:
            namestr = self.name2str(name)
            self.output.put(namestr)
    
    def run(self):
        for sent in self.group_input():
            print "."
#            features = sent2features(sent, self.ner.features)
#            print >> self.output, "FEATURES:"
#            for elem in features:
#                print >> self.output, " ".join(elem).encode('utf-8')
            names = self.ner.recognize_named_entities(sent)
            self.output_names(names)


def init_model(model_name):
    print "Loading NER model..."
    ner = NERecognizer.load(model_name)
    print "Done\n"
    return ner


def recognize(ner, sentence):
    line = sentence
    sent = line2sent(line.strip())
    names = ner.recognize_named_entities(sent)
    res = print_names(names)

    result = []
    for r in res:
        cat = r[:r.index(":")]
        cat = cat[:cat.index(".")].strip() if "." in cat else cat.strip()
        result.append((r[r.index(":")+2:r.index("(")].strip(), cat))
    return result
    #return [r[r.index(":")+2:r.index("(")].strip() for r in res]

def print_names(names):
    for root_name in names:
        for name in root_name.get_descendant_names_and_self():
            yield name2str(name)


if __name__ == "__main__":
    from optparse import OptionParser
    optparser = OptionParser(usage="""usage: %prog MODEL
        
        Run NER service using given model.""")

    (options, args) = optparser.parse_args()
    if len(args) != 1:
        optparser.print_help()
        sys.exit(0)

    model_name = args[0]
    print "Loading model..."
    ner = NERecognizer.load(model_name)
    print "Done\n"

    input = Queue()
    output = Queue()
    service = NERService(ner, input=input, output=output)
    thread = Thread(target=service.run, args=())
    thread.start()

    try:
        while True:
            line = raw_input("> ")
            input.put(line.decode('utf-8'))
            k = output.get()
            for _ in range(k):
                print output.get().encode('utf-8')
    except KeyboardInterrupt:
        input.put(None)

    thread.join()
