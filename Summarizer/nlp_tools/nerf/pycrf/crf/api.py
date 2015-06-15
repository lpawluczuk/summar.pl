# encoding: utf-8

import os
from StringIO import StringIO
import tarfile

import model as crfmodel
from data.dataset import DataSet
from data.alphabet import Alphabet
from data import translate
from data.sentence import Sentence
from data.auxdata import AuxData
from train.sgd import sgd
from tager import Tager
from train.gradient import count_z_stats

#ALPHABET_FILE = "alphabet.gz"
#PARAMS_FILE = "params.gz"
#MISC_FILE = "misc.txt"

def train_crf(dataset, r=0.1, **kwargs):
    train, evl = dataset.divide_in_two(r)
    model = sgd(train, **kwargs)
    return CRF(model, dataset.alphabet, dataset.obtypes(),
            rev_alphabet=dataset.rev_alphabet)

class CRF:

    def __init__(self, model, alphabet, obtypes, rev_alphabet=None):
        self.model = model
        self.alphabet = alphabet
        self.rev_alphabet = rev_alphabet
        if self.rev_alphabet == None:
            self.rev_alphabet = self.alphabet.reversed()
        self.tager = Tager(model, obtypes)

    def save(self, filename):
        model_file = StringIO()
        self.model.save(fileobj=model_file)
        alph_file = StringIO()
        self.alphabet.save(fileobj=alph_file)

        tar = tarfile.open(filename, "w:gz")
        self._add_to_tar(tar, model_file, "params")
        self._add_to_tar(tar, alph_file, "alphabet")
        tar.close()

    @staticmethod
    def load(filename, obtypes):
        tar = tarfile.open(filename, "r:gz")
        modelfile = tar.extractfile("params")
        model = crfmodel.load(fileobj=modelfile)
        alphfile = tar.extractfile("alphabet")
        alphabet = Alphabet.load(fileobj=alphfile)
        crf = CRF(model, alphabet, obtypes)
        tar.close()
        return crf

    def tag(self, sent):
        """
        Tag sentence with a most probable sequence of labels, i.e. labels,
        which maximize P(labels | sent, CRF parameters) probability
        modeled by the conditional random field.
        """
        sent = Sentence(translate.sentence(sent, self.alphabet))
        labels = self.tager.tag(sent)
        return translate.labels(labels, self.rev_alphabet)

    def prob(self, sent, labels, log=True):
        """Compute P(labels | sent, CRF parameters)."""
        sent = Sentence(translate.sentence(sent, self.alphabet))
        labels = translate.labels(labels, self.alphabet)
        logz = count_z_stats([(sent, labels)], self.model,
                self.tager.connsbuf)[0]
        return self.model.prob(sent, labels, logz, log)

    def cll(self, rdata, regvar=4.0):
        """Conditional log likelihood of given data."""
        data = [(Sentence(translate.sentence(sent, self.alphabet)),
                translate.labels(labels, self.alphabet))
                for (sent, labels) in rdata]
        z_stats = count_z_stats(data, self.model, self.tager.connsbuf)
        i_var2 = 1.0 / (regvar ** 2)
        return self.model.cll(data, z_stats, 1.0, i_var2)

    def _add_to_tar(self, tar, fileobj, name):
        """Add to tar object fileobj with given name."""
        fileobj.seek(0)
        info = tarfile.TarInfo(name=name)
        info.size = len(fileobj.buf)
        tar.addfile(tarinfo=info, fileobj=fileobj)
