#!/usr/bin/env python

import sys
import os

# Solution with no hard coded path would be welcome
sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])) + "/../")

from crf.model import Model
from crf.data.dataset import features_in_data
from crf.train.sgd import sgd

from ner.nerecognizer import NERecognizer
from ner.data import NerDataSet, filter_raw

from tei.corpus import read_tei_corpus
from tei.stats import name_stats, count_names, old_count_names
from train import get_summary, get_overall, print_summary, nkjp_summary_groups
from train import CallBack

def flatten(l):
    result = []
    for subl in l:
        result.extend(subl)
    return result

def file_lines(filename):
    return map(lambda x: x.strip(), open(filename).readlines())

def avg(l):
    return float(sum(l)) / len(l)

def cross_validation(dataset, schema, k, save_models_in=None,
        pre_train=False, sgd_kwargs={}, eval_every=10.0):
    """Perform k-cross validation on the given dataset."""
    if save_models_in is not None:
        if not os.path.isdir(save_models_in):
            os.mkdir(save_models_in)

    void_id = dataset.alphabet.label(unicode(dataset.alphabet.void_label))
    parts = dataset.divide(k,
            # stat=lambda x: old_count_names([x], dataset.rev_alphabet))
            stat=lambda x: count_names([x]))

    print "Data statistics:"
    for i in range(k):
        print "Part %s:" % i
        print "Number of sentences:", len(parts[i])
        # print "Number of NEs:", count_names(parts[i], dataset.rev_alphabet)
        print "Number of NEs:", count_names(parts[i])
    print ""

    summaries = []
    for i in range(k):
        print "======== Part %s =========" % i
        print ""

        evl = parts[i]
        train = flatten(parts[:i] + parts[i+1:])
        # if i > 2:
        if True:
            model = Model(features_in_data(filter_raw(train)))
            ner = NERecognizer(model, dataset.alphabet, schema)
            callback = CallBack(train, evl, ner, every=eval_every)

            if pre_train:            
                print "Pre-training model..."
                sgd(model, filter_raw(train), callback=callback, **{
                    "iter_num": 10,
                    "batch_size": sgd_kwargs["batch_size"],
                    "tau": sgd_kwargs["tau"],
                    "scale0": 0.01,
                    "workers": sgd_kwargs["workers"],
                    "verbose": sgd_kwargs["verbose"],
                    })
                print "Pre-training done\n"

            print "Training model..."
            sgd(model, filter_raw(train), callback=callback, **sgd_kwargs)
            print "Training done\n"

            if save_models_in is not None:
                save_path = os.path.join(save_models_in, "model%s.tgz" % i)
                print "\nSaving model in %s..." % save_path
                ner.save(save_path)
                print "Done"
        else:
            assert save_models_in is not None
            path = os.path.join(save_models_in, "model%s.tgz" % i)
            print "Loading model from %s..." % path
            ner = NERecognizer.load(path)
            print "Done"

        print ""
        print "==== Summary for part %s ====" % i
        print ""
        print "[Train part]"
        print ""
        train_summary = get_overall(train, ner)
        print_summary(train_summary)

        print "[Evaluation part]"
        print ""
        eval_summary = get_summary(evl, ner, nkjp_summary_groups())
        print_summary(eval_summary)

        summaries.append((train_summary, eval_summary))
    return summaries

def averaged_summary(summaries):
    results = {}
    cats = set()
    for summary in summaries:
        for category, stats in summary.iteritems():
            cats.add(category)
            if not results.has_key(category):
                results[category] = []
            results[category].append(stats)
    averaged = {}
    for category in cats:
        # lista wszytkich statystyk (prec, recall, ...) na kolejnych czesciach
        stat_list = results[category]

        types = ["Precision", "Recall", "F-measure"]
        cat_averaged = []
        for type in types:
            val = avg([dict(stats)[type] for stats in stat_list])
            cat_averaged.append((type, val))

        averaged[category] = tuple(cat_averaged)
    return averaged

if __name__ == "__main__":
    from optparse import OptionParser
    optparser = OptionParser(usage="""usage: %prog,
        
        Extract data from corpus, divide it to k parts and
        perform k-cross validation.""")
	
    optparser.add_option("-k", "--k-cross-validation", type="int", default=10,
            dest="k", help="Perform k-cross validation.")
    optparser.add_option("--tei-corpus", metavar="DIR", dest="tei_corpus",
            help="Use TEI corpus as data source.")
    optparser.add_option("--ann-named", type="string",
            dest="ann_named", default="ann_named.xml",
            help="Names of input ann_named files.")
    optparser.add_option("--data-out", metavar="FILE",
            dest="data_out", help="Data output file (for debugging purpose).")
    optparser.add_option("--select", type="float", default=1.0,
            dest="select", help="Select subcorpus of given relative size.")
    optparser.add_option("--schema", metavar="FILE",
            dest="schema", help="File with feature schema.")
    optparser.add_option("--black-listed", metavar="FILE",
            dest="black_listed", help="Black listed corpus directories.")
    optparser.add_option("--batch-size", type="int",
            default=30, dest="batch_size",
            help="Batch size in SGD method.")
    optparser.add_option("--evaluate-every", type="int",
            default=10, dest="eval_every",
            help="Compute stats on evaluation part every * interations.")
    optparser.add_option("--iter-num", type="int", default=100,
            dest="iter_num", help="Number of SGD method iterations.")
    optparser.add_option("--threads", type="int", default=1, dest="threads",
            help="Number of threads in parallel computation.")
    optparser.add_option("--regvar", type="float", dest="regvar",
            help="Regularization variance parameter, see SGD specification.")
    optparser.add_option("--scale0", type="float", default=0.01,
            dest="scale0", help="Scale0 parameter, see SGD specification.")
    optparser.add_option("--tau", type="float", default=10.0,
            dest="tau", help="Tau parameter, see SGD specification.")
    optparser.add_option("--pre-train", default=False,
            action="store_true", dest="pre_train",
            help="Pre-train model on input data with predefined," +
                    " small scale0 value.")
    optparser.add_option("--void-label", type="str", dest="void_label",
            default="O", help="Label representing void information.")
    optparser.add_option("--dummy-label", type="str", dest="dummy_label",
            default="DUMMY", help="Label corresponding to the posision in"
            " a sentence before the first word.")
    optparser.add_option("--save-models-in", metavar="DIR",
            dest="save_models_in",
            help="Save models created during the process in given directory.")

    (options, args) = optparser.parse_args()
    if options.tei_corpus == None:
        optparser.print_help()
        print "\n--tei_corpus option is mandatory"
        sys.exit(0)
    if options.schema == None:
        optparser.print_help()
        print "\n--schema option should be supplied"
        sys.exit(0)

    if options.black_listed != None:
        black_listed = file_lines(options.black_listed)
    else:
        black_listed = []

    print "Reading data..."
    schema = file_lines(options.schema)
    raw_data, dirs = read_tei_corpus(options.tei_corpus, schema,
            black_listed, options.select, ann_named=options.ann_named)
    dataset = NerDataSet(raw_data, void_label=unicode(options.void_label),
            dummy_label=unicode(options.dummy_label), dirs=dirs)
    print "Reading done\n"

    if options.data_out:
        dataset.print_data(options.data_out)

    summaries = cross_validation(dataset, schema, options.k,
            save_models_in=options.save_models_in,
            pre_train=options.pre_train,
            eval_every=options.eval_every,
            sgd_kwargs={
                "iter_num": options.iter_num,
                "batch_size": options.batch_size,
                "tau": options.tau,
                "scale0": options.scale0,
                "workers": options.threads,
                "verbose": False
                })

    print "====== On average ======"
    print ""
    print "[Train part]"
    print ""
    print_summary(averaged_summary(train_summ for train_summ, _ in summaries))

    print "[Evaluation part]"
    print ""
    print_summary(averaged_summary(eval_summ for _, eval_summ in summaries))
