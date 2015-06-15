#!/usr/bin/env python

import sys
import os

# Solution with no hard coded path would be welcome
sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])) + "/../")

from crf.data.dataset import DataSet
from crf.data import rawdata
from crf.stats import stats
from crf.train.sgd import sgd
from crf.tager import Tager
from crf.api import CRF

from crf.cross_validation import cross_validation

def file_lines(file_name):
    return map(lambda x: x.strip(), open(file_name).readlines())

def avg(l):
    return float(sum(l)) / len(l)

if __name__ == '__main__':
    from optparse import OptionParser
    optparser = OptionParser(
        usage="""%prog DATA_FILE,

        Perform cross validation on data stored in DATA_FILE.""")
	
    optparser.add_option("-k", "--k_cross_validation", type="int", default=10,
            dest="k", help="perform k-cross validation")
    optparser.add_option("-d", "--dirs_file", dest="dirs_file",
            metavar="FILE", help="file with names of directories corresponding"
            " to sentences in the data; when supplied, data will be divided"
            " with respect to directories")
    optparser.add_option("-b", "--batch_size", type="int",
            default=30, dest="batch_size",
            help="batch size for SGD method")
    optparser.add_option("-n", "--max_iter_num", type="int", default=200,
            dest="max_iter_num", help="number of SGD method iterations")
    optparser.add_option("-t", "--threads", type="int", default=1,
            dest="threads", help="number of threads in parallel computation")
#    optparser.add_option("--regvar", type="float", dest="regvar",
#            help="regularization variance parameter, see SGD specification")
    optparser.add_option("--scale0", type="float", default=0.01,
            dest="scale0", help="scale0 parameter, see SGD specification")
    optparser.add_option("--tau", type="float", default=10.0,
            dest="tau", help="tau parameter, see SGD specification")
    optparser.add_option("--void_label", type="str", dest="void_label",
            default="O", help="label representing void information")
    optparser.add_option("--dummy_label", type="str", dest="dummy_label",
            default="DUMMY", help="label corresponding to the posision in"
            " a sentence before the first word")

    (options, args) = optparser.parse_args()
    if len(args) != 1:
        optparser.print_help()
        sys.exit()
    file_name = args[0]
    rdata = rawdata.from_file(file_name)
    if options.dirs_file != None:
        dirs = file_lines(options.dirs_file)
    else:
        dirs = None
    ds = DataSet(rdata,
            void_label=unicode(options.void_label),
            dummy_label=unicode(options.dummy_label),
            dirs=dirs)
    train_stats, eval_stats = cross_validation(ds, options.k,
            iter_num=options.max_iter_num, scale0=options.scale0,
            tau=options.tau, workers=options.threads)
    (train_prec, train_rec, train_F) = train_stats
    (eval_prec, eval_rec, eval_F) = eval_stats
    print "====== On average ======"
    print ""
    print "Train part:"
    print "Precision:", avg(train_prec)
    print "Recall:", avg(train_rec)
    print "F-measure:", avg(train_F)
    print ""
    print "Eval part:"
    print "Precision:", avg(eval_prec)
    print "Recall:", avg(eval_rec)
    print "F-measure:", avg(eval_F)
    print ""
