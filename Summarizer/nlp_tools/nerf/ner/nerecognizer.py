# encoding: utf-8

import os
import tarfile
from StringIO import StringIO

from crf.api import CRF
import crf.model as crfmodel
from crf.data.alphabet import Alphabet

from data import DummySegment
from features import sent2features, parse_feature_names
from labels import decode, label2tuple

class NERecognizer(CRF):

    def __init__(self, model, alphabet, schema, rev_alphabet=None):
        self.schema = schema
        self.features = parse_feature_names(schema)
        # print "number of features:", len(self.features)
        CRF.__init__(self, model, alphabet, len(self.features),
                rev_alphabet=rev_alphabet)

    def save(self, filename):
        model_file = StringIO()
        self.model.save(fileobj=model_file)
        alph_file = StringIO()
        self.alphabet.save(fileobj=alph_file)

        tar = tarfile.open(filename, "w:gz")
        self._add_to_tar(tar, model_file, "params")
        self._add_to_tar(tar, alph_file, "alphabet")
        self._add_to_tar(tar, StringIO("\n".join(self.schema)), "schema")
        tar.close()

    @staticmethod
    def load(filename):
        tar = tarfile.open(filename, "r:gz")
        modelfile = tar.extractfile("params")
        model = crfmodel.load(fileobj=modelfile)
        alphfile = tar.extractfile("alphabet")
        alphabet = Alphabet.load(fileobj=alphfile)
        featfile = tar.extractfile("schema")
        schema = map(lambda x: x.strip(), featfile.readlines())
        ner = NERecognizer(model, alphabet, schema)
        tar.close()
        return ner

    def prob(self, sent, labels, log=True):
        raise NotImplementedError
#        """Compute P(labels | sent, CRF parameters)."""
#        sent = Sentence(translate.sentence(sent, self.alphabet))
#        labels = translate.labels(labels, self.alphabet)
#        logz = count_z_stats([(sent, labels)], self.model,
#                self.tager.connsbuf)[0]
#        return self.model.prob(sent, labels, logz, log)

    def cll(self, rdata, regvar=4.0):
        raise NotImplementedError
#        """Conditional log likelihood of given data."""
#        data = [(Sentence(translate.sentence(sent, self.alphabet)),
#                translate.labels(labels, self.alphabet))
#                for (sent, labels) in rdata]
#        z_stats = count_z_stats(data, self.model, self.tager.connsbuf)
#        i_var2 = 1.0 / (regvar ** 2)
#        return self.model.cll(data, z_stats, 1.0, i_var2)

    def recognize_named_entities(self, sent, features=None):
        """
        Recognize NEs in the sentence.

        :param features:
            Feature values already extracted from sentence.
        """
        if not features:
            features = sent2features(sent, self.features)
        labels = [label2tuple(y) for y in self.tag(features)]
        return decode(labels, sent, recover_not_started=True, max_dist=2)
