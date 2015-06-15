#!/usr/bin/env python

import sys
import os
import copy

# Solution with no hard coded path would be welcome
sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])) + "/../")

from crf.model import Model
from crf.data.dataset import divide_in_two, labels_in_data, features_in_data
from crf.train.sgd import sgd

from ner.nerecognizer import NERecognizer
from ner.data import NerDataSet, filter_raw
from ner.labels import decode, label2tuple

from tei.corpus import read_tei_corpus
from tei.stats import name_stats, count_names
import tei.stats as stats_mod

def file_lines(filename):
    return map(lambda x: x.strip(), open(filename).readlines())

def _adorn_stats(stats):
    tagged, good, agrees = stats
    prec = stats_mod.precision(*stats)
    rec = stats_mod.recall(*stats)
    F = stats_mod.F(*stats)
    return (("Tagged", tagged),
            ("Good", good),
            ("Agrees", agrees),
            ("Precision", prec),
            ("Recall", rec),
            ("F-measure", F))

def get_overall(data, ner):
    stats = name_stats(data, ner, ignore_derivType=False)[0]
    adorned = _adorn_stats(stats)
    return {"(1) overall": adorned}

def type_eq(netype):
    return lambda ne: ne.type == netype

def nkjp_summary_groups():
    groups = [["persName"], ["geogName", "placeName"], ["orgName"],
            ["date", "time"], ["relAdj", "persDeriv"]] 
    result = []
    result.append((["persName"],
        lambda name: name.type in ["persName"]))
    result.append((["geogName", "placeName"],
        lambda name: name.type in ["geogName", "placeName"]))
    result.append((["orgName"],
        lambda name: name.type in ["orgName"]))
    result.append((["date", "time"],
        lambda name: name.type in ["date", "time"]))
    result.append((["relAdj", "persDeriv"],
        lambda name: name.derivType in ["relAdj", "persDeriv"]))
    result.append((["overall"], None))
    return result

def netypes_in_dataset(dataset):
    netypes = set()
    for (_, names), _ in dataset:
        for root in names:
            for ne in root.get_descendant_names_and_self():
                netypes.add(ne.type)
    return sorted(netypes)

def get_summary(data, ner, groups):
#    preds = [lambda name: name.type in copy.deepcopy(group)
#            for group in groups] + [None]
    preds = [pred for _, pred in groups]
    groups = [group for group, _ in groups]
    stat_list = name_stats(data, ner,
            predicates=preds, ignore_derivType=False)
    summary = {}
    for i, (stats, group) in enumerate(zip(stat_list, groups)):
        # groups + [["overall"]])):
        adorned_stats = _adorn_stats(stats)
        summary[("(%s) " % (i + 1)) + " and ".join(group)] = adorned_stats 
    return summary

def print_summary(summary):
    for category, adorned_stats in sorted(summary.iteritems()):
        print category + ":"
        for statname, val in adorned_stats:
            print statname + ":", val
        print ""

class CallBack:

    """Callback for SGD method."""

    def __init__(self, train, evl, ner, every=1):
        """
        :params:
        --------
        every : int
            Compute stats on eval part each $every iteration. 
        """
        self.train = train
        self.evl = evl
        self.ner = ner
        self.every = every
        self.prev_iter = 0.0

    def __call__(self, iter):
        if int(iter / self.every) > int(self.prev_iter / self.every):
            print "[%s]" % round(iter, 1),
            print "F(eval) =",
            stats = name_stats(self.evl, self.ner,
                    ignore_derivType=False)[0]
            adorned = _adorn_stats(stats)
            print dict(adorned)["F-measure"]
        self.prev_iter = iter

def train(data, evl, dataset, schema, ner=None, sgd_kwargs={},
        eval_every=10.0, generate_absent=False): 
    """
    Train NER tool with respect to the given data.

    :params:
    --------
    data :
        List of (sentence, labels) pairs.
    dataset : NerDataSet
        Source of both data and evl parts.
    ner : NERecognizer
        If not None, ner will be used as an initial NER model.
    """
    if ner is not None:
        model = ner.model.translated(
                from_alph=ner.alphabet,
                to_alph=dataset.alphabet)
    else:
        model = Model(features_in_data(filter_raw(data),
            generate_absent=generate_absent))

    print "Number of model parameters:", model.pn

    ner = NERecognizer(model, dataset.alphabet, schema)
    callback = CallBack(data, evl, ner, every=eval_every)
    sgd(model, filter_raw(data), callback=callback, **sgd_kwargs)
    return ner

if __name__ == "__main__":
    from optparse import OptionParser
    optparser = OptionParser(usage="""usage: %prog,
        
        Extract data from TEI corpus, divide it to training part and
        evaluation part and perform CRF model training process.""")
	
    optparser.add_option("--tei-corpus", metavar="DIR", dest="tei_corpus",
            help="Use TEI corpus as data source.")
    optparser.add_option("--schema", metavar="FILE",
            dest="schema", help="File with feature schema.")
    optparser.add_option("--generate-absent-features", default=False,
            action="store_true", dest="generate_absent",
            help="Generate features absent in data.")
    optparser.add_option("--model-out", metavar="FILE",
            dest="model_out", help="Resultant model output file.")
    optparser.add_option("--model-in", metavar="FILE", dest="model_in",
            help="Start training from initial model.")
    optparser.add_option("--ann-named", type="string",
            dest="ann_named", default="ann_named.xml",
            help="Names of input ann_named files.")
    optparser.add_option("--nkjp-summary", default=False,
            action="store_true", dest="nkjp_summary",
            help="Print summary adapted to NKJP.")
    optparser.add_option("--data-out", metavar="FILE",
            dest="data_out", help="Data output file (for debugging purpose).")
    optparser.add_option("--select", type="float", default=1.0,
            dest="select", help="Select subcorpus of given relative size.")
    optparser.add_option("--black-listed", metavar="FILE",
            dest="black_listed", help="Black listed corpus directories.")
    optparser.add_option("--relative-eval-size", type="float",
            default=0.1, dest="eval_size",
            help="Relative (to the data size) size of the eval part.")
    optparser.add_option("--evaluate-every", type="int",
            default=10, dest="eval_every",
            help="Compute stats on evaluation part every * interations.")
    optparser.add_option("--batch-size", type="int",
            default=30, dest="batch_size",
            help="Batch size in SGD method.")
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
#    optparser.add_option("--verbose_level", type="int",
#            default=1, dest="verbose_level",
#            help="0: no output, 1: ...")

    (options, args) = optparser.parse_args()
    if options.tei_corpus == None:
        optparser.print_help()
        print "\n--tei-corpus option is mandatory"
        sys.exit(0)
    if options.schema == None and options.model_in == None:
        optparser.print_help()
        print "\n--schema or --model-in option should be supplied"
        sys.exit(0)
    if options.schema != None and options.model_in != None:
        print ("WARNING: schema will be ignored, using model-in" +
                " schema instead")

    ner = None
    schema = None
    if options.model_in:
        print "Loading model from %s..." % options.model_in
        ner = NERecognizer.load(options.model_in)
        schema = ner.schema
    else:
        schema = file_lines(options.schema)

    if options.black_listed != None:
        black_listed = file_lines(options.black_listed)
    else:
        black_listed = []

    print "Reading data..."
    raw_data, dirs = read_tei_corpus(options.tei_corpus, schema,
            black_listed, options.select, ann_named=options.ann_named)
    dataset = NerDataSet(raw_data, void_label=unicode(options.void_label),
            dummy_label=unicode(options.dummy_label), dirs=dirs)
    print "Reading done\n"

#    print "Data statistics:"
#    print "Number of sentences:", len(dataset)
#    print "Number of segments:", sum(len(sent) for sent, labels in dataset)
#    print "Number of NEs:", count_names(dataset)
#    print ""
    if options.data_out:
        dataset.print_data(options.data_out)

    train_part, eval_part = dataset.divide_in_two(options.eval_size)
    print "Train part statistics:"
    print "Number of sentences:", len(train_part)
    print "Number of segments:", sum(len(segs) for (segs, _), _ in train_part)
    print "Number of labels:", len(labels_in_data(filter_raw(train_part)))
    print "Number of NEs:", count_names(train_part)
    print ""
    if len(eval_part) > 0:
        print "Evaluation part statistics:"
        print "Number of sentences:", len(eval_part)
        print "Number of segments:", sum(len(segs)
                for (segs, _), _ in eval_part)
        print "Number of NEs:", count_names(eval_part)
        print ""

    if options.pre_train:
        print "Pre-training model..."
        ner = train(train_part, eval_part, dataset, schema, ner=ner, 
                eval_every=options.eval_every,
                generate_absent=options.generate_absent,
                sgd_kwargs={
                    "iter_num": 10,
                    "batch_size": options.batch_size,
                    "tau": options.tau,
                    "scale0": 0.01,
                    "workers": options.threads,
                    "verbose": False
                    })
        print "Pre-training done\n"

    print "Training model..."
    # ner = train(train_part, eval_part, options.iter_num, dataset, schema,
    #         ner=ner, scale0=options.scale0, workers=options.threads)
    ner = train(train_part, eval_part, dataset, schema, ner=ner, 
            eval_every=options.eval_every,
            generate_absent=options.generate_absent,
            sgd_kwargs={
                "iter_num": options.iter_num,
                "batch_size": options.batch_size,
                "tau": options.tau,
                "scale0": options.scale0,
                "workers": options.threads,
                "verbose": False
                })

    if options.model_out:
        print ""
        print "Saving model in %s..." % options.model_out
        ner.save(options.model_out)
        print "Done"

    if options.nkjp_summary:
        summary_groups = nkjp_summary_groups()
    else:
        summary_groups = [([netype], type_eq(netype))
                for netype in netypes_in_dataset(dataset.iterator())]
        summary_groups += [(["overall"], None)]

    print ""
    print "====== Summary ======"
    print ""
    print "[Train part]"
    print ""
    # train_summary = get_overall(train_part, ner)
    train_summary = get_summary(train_part, ner, summary_groups)
    print_summary(train_summary)

    if len(eval_part) > 0:
        print "[Evaluation part]"
        print ""
        eval_summary = get_summary(eval_part, ner, summary_groups)
        print_summary(eval_summary)
