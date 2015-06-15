#!/usr/bin/env python

import sys
import os

# Solution with no hard coded path would be welcome
sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])) + "/../")

from crf.data import dataset
from crf.data import rawdata
from crf.stats import stats
from crf.train.sgd import sgd
from crf.tager import Tager
from crf.api import CRF
from crf.model import Model

def file_lines(file_name):
    return map(lambda x: x.strip(), open(file_name).readlines())

class CallBack:

    def __init__(self, train, evl, tager, void_id, every=10):
        self.train = train
        self.evl = evl
        self.tager = tager
        self.void_id = void_id
        self.every = every
        self.prev_iter = 0.0

    def __call__(self, iter):
#        if i % 50 == 0:
#            print "=== Train part ==="
#            prec, rec, F = stats(self.train, self.tager, self.void_id)
#            print "Precision:", prec
#            print "Recall:", rec
#            print "F-measure:", F
#
        if int(iter / self.every) > int(self.prev_iter / self.every):
            print "=== Iteration: %s ===" % round(iter, 1)
            prec, rec, F = stats(self.evl, self.tager, self.void_id)
            print "Precision:", prec
            print "Recall:", rec
            print "F-measure:", F
        self.prev_iter = iter

if __name__ == '__main__':
    from optparse import OptionParser
    optparser = OptionParser(
        usage="""%prog TRAIN_FILE MODEL_OUTPUT_FILE,
        
        * Read data from TRAIN_FILE,
        * Divide data into two parts: train and eval,
        * Train CRF model on the train part,
        * Compute presision, recall and F-measure on both parts 
          with respect to the CRF model,
        * Save CRF model in the MODEL_OUTPUT_FILE.""")
	
    optparser.add_option("-r", "--relative_eval_size", type="float",
            default=0.1, dest="eval_size",
            help="relative (to the data size) size of the eval part")
#    optparser.add_option("-i", "--init-model", dest="init_model_dir",
#            metavar="DIR", help="directory with initial model")
    optparser.add_option("-d", "--dirs_file", dest="dirs_file",
            metavar="FILE", help="file with names of directories corresponding"
            " to sentences in the data; when supplied, data will be divided"
            " with respect to directories")
#     optparser.add_option("-s", "--save-freq", type="int",
#             dest="save_freq", help="Saving model frequency.")
#     optparser.add_option("-m", "--max-train-f", type="float", default=100.0,
#             dest="max_train_f", help="Stop when F-measure"
#                 " on train file is greater then max-train-f.")
    optparser.add_option("-b", "--batch_size", type="int",
            default=30, dest="batch_size",
            help="batch size for the SGD method")
    optparser.add_option("-n", "--max_iter_num", type="int", default=100,
            dest="max_iter_num", help="number of SGD method iterations")
    optparser.add_option("-t", "--threads", type="int", default=1,
            dest="threads", help="number of threads in parallel computation")
    optparser.add_option("--regvar", type="float", dest="regvar",
            help="regularization variance parameter, see SGD specification")
    optparser.add_option("--scale0", type="float", default=0.01,
            dest="scale0", help="scale0 parameter, see SGD specification")
    optparser.add_option("--tau", type="float", default=10.0,
            dest="tau", help="tau parameter, see SGD specification")
    optparser.add_option("--void_label", type="str", dest="void_label",
            default="O", help="label representing void information")
    optparser.add_option("--dummy_label", type="str", dest="dummy_label",
            default="DUMMY", help="label corresponding to the posision in"
            " a sentence before the first word")
    optparser.add_option("-v", "--verbose", default=False,
            action="store_true", dest="verbose")
    optparser.add_option("--pre-train", default=False,
            action="store_true", dest="pre_train",
            help="pre-train model with smaller scale0.")

    (options, args) = optparser.parse_args()
    if len(args) != 2:
        optparser.print_help()
        sys.exit()
    file_name, model_output = args

    rdata = rawdata.from_file(file_name)
    if options.dirs_file != None:
        dirs = file_lines(options.dirs_file)
    else:
        dirs = None
    ds = dataset.DataSet(rdata,
            void_label=unicode(options.void_label),
            dummy_label=unicode(options.dummy_label),
            dirs=dirs)
    train, evl = ds.divide_in_two(options.eval_size)

    model = Model(dataset.features_in_data(train))
    tager = Tager(model, ds.obtypes())
    void_id = ds.alphabet.label(unicode(options.void_label))

    callback = CallBack(train, evl, tager, void_id, every=1.0)
    if options.pre_train:
        sgd(model, train,
                iter_num=options.max_iter_num / 10.0,
                batch_size=options.batch_size,
                scale0=options.scale0 / 10.0,
                tau=options.tau, workers=options.threads,
                callback=callback, verbose=False)
    sgd(model, train, callback=callback,
            iter_num=options.max_iter_num,
            batch_size=options.batch_size,
            scale0=options.scale0,
            tau=options.tau,
            workers=options.threads,
            verbose=options.verbose)
#    sgd(model, train, max_iter_num=options.max_iter_num,
#            batch_size=options.batch_size, scale0=options.scale0,
#            tau=options.tau, workers=options.threads,
#            callback=callback, verbose=options.verbose)

    print "Saving model in %s..." % model_output
    crf = CRF(model, ds.alphabet, ds.obtypes())
    crf.save(model_output)
    print "Done"
    print ""

    prec, rec, F = stats(train, tager, void_id)
    print " === Train part ==="
    print " Precision:", prec
    print " Recall:", rec
    print " F-measure:", F

    prec, rec, F = stats(evl, tager, void_id)
    print " === Eval part ==="
    print " Precision:", prec
    print " Recall:", rec
    print " F-measure:", F
