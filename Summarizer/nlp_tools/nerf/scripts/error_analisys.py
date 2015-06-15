#!/usr/bin/env python

import sys
import os
from collections import defaultdict

# Solution with no hard coded path would be welcome
sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])) + "/../")

# from crf.data.dataset import DataSet, divide_in_two
from ner.data import NerDataSet
from ner.nerecognizer import NERecognizer
from tei.stats import count_names, count_errors
from tei.corpus import read_tei_corpus

def file_lines(filename):
    return map(lambda x: x.strip(), open(filename).readlines())

def netype(s):
    return s.split(":")[0]

def group_types(stats, by_type=False):
    result = defaultdict(int)
    for key, val in stats.iteritems():
        if by_type:
            key = netype(key)
        result[key] += val
    return result

def group_pairs(stats, by_type=False):
    result = defaultdict(int)
    for (key1, key2), val in stats.iteritems():
        if by_type:
            key1 = netype(key1)
            key2 = netype(key2)
        result[(key1, key2)] += val
    return result

def print_stats(stats):
    for key, val in reversed(sorted(stats.items(), key=lambda (k, v): v)):
        print key, "=>", val

if __name__ == "__main__":
    from optparse import OptionParser
    optparser = OptionParser(usage="""usage: %prog,
        
        Extract data from tei_corpus, divide it to training part and
        evaluation part and perform error analisys on the evaluation
        part.""")
	
    optparser.add_option("--save-errors", metavar="FILE", dest="save_errors",
            help="Save list of errors in.")
    optparser.add_option("--tei-corpus", metavar="DIR", dest="tei_corpus",
            help="Use TEI corpus as data source.")
    optparser.add_option("--select", type="float", default=1.0,
            dest="select", help="select subcorpus of a given relative size.")
    optparser.add_option("--relative-eval-size", type="float",
            default=0.1, dest="eval_size",
            help="Relative (to the data size) size of the eval part.")
    optparser.add_option("--model-in", metavar="FILE", dest="model_in",
            help="start training from initial model")
    optparser.add_option("--ann-named", type="string",
            dest="ann_named", default="ann_named.xml",
            help="Names of input ann_named files.")
    optparser.add_option("--black-listed", metavar="FILE",
            dest="black_listed", help="black listed TEI corpus directories")
#    optparser.add_option("--void-label", type="str", dest="void_label",
#            default="O", help="label representing void information")
#    optparser.add_option("--dummy-label", type="str", dest="dummy_label",
#            default="DUMMY", help="label corresponding to the posision in"
#            " a sentence before the first word")

    (options, args) = optparser.parse_args()
    if options.tei_corpus == None:
        optparser.print_help()
        print "\n--tei-corpus option is mandatory"
        sys.exit(0)
    if options.model_in == None:
        optparser.print_help()
        print "\n--model-in option should be supplied"
        sys.exit(0)

    print "Loading model from %s..." % options.model_in
    ner = NERecognizer.load(options.model_in)

    if options.black_listed != None:
        black_listed = file_lines(options.black_listed)
    else:
        black_listed = []

    print "Reading data..."
    raw_data, dirs = read_tei_corpus(options.tei_corpus, ner.schema,
            black_listed, options.select, ann_named=options.ann_named)
    dataset = NerDataSet(raw_data, alphabet=ner.alphabet, dirs=dirs)
    print "Reading done\n"

    train_part, eval_part = dataset.divide_in_two(options.eval_size)
    print "Evaluation part statistics:"
    print "Number of sentences:", len(eval_part)
    print "Number of segments:", sum(len(sent)
            for sent, labels in eval_part)
    print "Number of NEs:", count_names(eval_part)
    print ""

    tp, fp, fn, substs, pairs, fn_errors, fp_errors,\
            subst_errors, pair_errors = count_errors(eval_part, ner)
    print "=== TRUE POSITIVES ==="
    print_stats(group_types(tp))
    print "=== FALSE POSITIVES ==="
    print_stats(group_types(fp))
    print "=== FALSE NEGATIVES ==="
    print_stats(group_types(fn))
    print "=== SUBSTITUTIONS ==="
    print_stats(group_pairs(substs))
    print "=== PAIRS ==="
    print_stats(group_pairs(pairs))

    if options.save_errors is not None:
        with open(options.save_errors, "w") as f:
            print >> f, "FALSE NEGATIVE ERRORS:"
            for (t, s), sent in fn_errors:
                print >> f, "#", sent
                print >> f, t, s.encode('utf-8'), "=>"
            print >> f, "FALSE POSITIVE ERRORS:"
            for (t, s), sent in fp_errors:
                print >> f, "#", sent
                print >> f, "=>", t, s.encode('utf-8')
            print >> f, "SUBSTITUTION ERRORS:"
            for (t1, s1), (t2, s2), sent in subst_errors:
                print >> f, "#", sent
                print >> f, t1, s1.encode('utf-8'), "=>", t2, s2.encode('utf-8')
            print >> f, "PAIR ERRORS:"
            for (t1, s1), (t2, s2), sent in pair_errors:
                print >> f, "#", sent
                print >> f, t1, s1.encode('utf-8'), "=>", t2, s2.encode('utf-8')
