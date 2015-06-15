# encoding: utf-8

from train.sgd import sgd
from tager import Tager
from stats import stats
from model import Model
from data.dataset import features_in_data

def flatten(l):
    v = []
    for x in l:
        v.extend(x)
    return v

def cross_validation(dataset, k, *sgd_args, **sgd_kwargs):
    """Perform k-cross validation on the given dataset."""
    train_prec = []
    train_rec = []
    train_F = []
    eval_prec = []
    eval_rec = []
    eval_F = []

    void_id = dataset.alphabet.label(unicode(dataset.alphabet.void_label))
    parts = dataset.divide(k)
    obtypes = dataset.obtypes()
    for i in range(k):
        print "======== Part %s ========" % i
        print ""

        evl = parts[i]
        train = flatten(parts[:i] + parts[i+1:])
        model = Model(features_in_data(train))
        sgd(model, train, *sgd_args, **sgd_kwargs)
        tager = Tager(model, obtypes)

        _prec, _rec, _F = stats(train, tager, void_id)
        print "Train part:"
        print "Precision:", _prec
        print "Recall:", _rec
        print "F-measure:", _F
        print ""
        train_prec.append(_prec)
        train_rec.append(_rec)
        train_F.append(_F)

        _prec, _rec, _F = stats(evl, tager, void_id)
        print "Eval part:"
        print "Precision:", _prec
        print "Recall:", _rec
        print "F-measure:", _F
        print ""
        eval_prec.append(_prec)
        eval_rec.append(_rec)
        eval_F.append(_F)

    train_stats = (train_prec, train_rec, train_F)
    eval_stats = (eval_prec, eval_rec, eval_F)
    return train_stats, eval_stats
