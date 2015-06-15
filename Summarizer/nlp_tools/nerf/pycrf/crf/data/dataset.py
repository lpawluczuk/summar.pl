# encoding: utf-8

from itertools import groupby, chain, product

import rawdata
import translate
from alphabet import Alphabet
from sentence import Sentence
from crf import const
import re

def argmin(l):
    i, x = min(enumerate(l), key=lambda (i, x): x)
    return i

def _alphabet_from_rdata(rdata, void_label, dummy_label):
    """Extract alphabet (of observations and labels) from
    given raw data."""
    alphabet = Alphabet(void_label=void_label, dummy_label=dummy_label)
    for (sent, labels) in rdata:
        for word in sent:
            for x in chain(*word):
                alphabet.add_observation(x)
        for y in labels:
            alphabet.add_label(y)
    return alphabet

#def _translate_rsent(rsent, alphabet):
#    """Translate raw sentence of words, where each word is a list
#    of observation values, with respect to the given alphabet."""
#    sentence = [[alphabet.observation(x) for x in word]
#                for (word, _) in rsent]
#    labels = [alphabet.label(label) for (_, label) in rsent]
#    return Sentence(sentence), labels

def _file_lines(file_name):
    f = open(file_name)
    try:
        value = map(lambda x: x.strip(), f.readlines())
    finally:
        f.close()
    return value

def labels_in_data(data):
    """Labels in data (without dummy label)"""
    return sorted(set(y for _, labels in data for y in labels))

def features_in_data_gen_absent(data):
    """Features present in data + absent features."""
    def add_features(word, prev_ys, ys, features):
        (singles, pairs) = word
        for x, y in product(singles, ys):
            features.add((-1, y, x))
        for x, y, py in product(pairs, ys, prev_ys):
            features.add((py, y, x))
    all_labels = labels_in_data(data)
    features = set()
    for sent, _ in data:
        prev_ys = [const.dummy_id]
        for word in sent:
            add_features(word, prev_ys, all_labels, features)
            prev_ys = all_labels
    return sorted(features)

def features_in_data_no_absent(data):
    """Features present in data; do not generate absent features."""
    features = set()
    for sent, labels in data:
        py = const.dummy_id
        for (singles, pairs), y in zip(sent, labels):
            for x in singles:
                features.add((-1, y, x))
            for x in pairs:
                features.add((py, y, x))
            py = y
    return sorted(features)

def features_in_data(data, generate_absent=False):
    """Return features present in the data."""
    if generate_absent:
        return features_in_data_gen_absent(data)
    else:
        return features_in_data_no_absent(data)

def obtypes(data):    
    """Return number of observations types -- maximum number
    of observations per word."""
    return max(len(ss) + len(ps) for sent, _ in data for ss, ps in sent)

def _dirdata(data, dirs):
    """Return data grouped with repsect to dirs."""
    dirdata = []
    for dirname, group in groupby(zip(dirs, data),
            key=lambda (dirname, sent): dirname):
        dirdata.append((dirname,
            map(lambda (dirname, sent): sent, group)))
    return sorted(dirdata, key=lambda (dirname, group): len(group),
            reverse=True)

def divide_data(data, dirs, n, stat=(lambda x: 1)):
    """
    Divide data to n parts with respect to dirnames --
    sentences from one directory will be in the same part.

    :param stat:
        Divide data with respect to given statistic, so that
        each part will have similar statistic value.
        Statistic value is computed in the following way:
            value = sum(stat(x) for x in part)
    """
    dirdata = _dirdata(data, dirs)
    parts = [[] for i in range(n)]
    stats = [0 for _ in parts]
    for (_, group) in dirdata:
        i = argmin(stats) 
        parts[i].extend(group)
        stats[i] += sum(stat(x) for x in group)
    return parts

def divide_in_two(data, dirs, r):
    """
    Divide data to 2 parts with respect to dirnames --
    sentences from one directory will be in the same part.

    :param r:
        Relative size of the second part (with respect
        to data size).
    """
    dirdata = _dirdata(data, dirs)
    parts = [[], []]
    for (_, group) in dirdata:
        if r < 1 and len(parts[1]) >= len(parts[0]) * (r / (1.0 - r)):
            parts[0].extend(group)
        else:
            parts[1].extend(group)
    return parts

class DataSet:

    def __init__(self, rdata, dummy_label=None, void_label=None, 
            alphabet=None, dirs=None):
        """Initialize data set.

        :params:
        --------
        void_label :
            Label, which represents void information.
            Set to None, when not related.
        dummy_label :
            Label related to a position before the first word in a sentence. 
            Should be different from each of the real labels. 
        alphabet :
            Use given alphabet to translate raw data. Ignore dummy_label
            and void_label parameters.
        """
        if alphabet is not None:
            self.alphabet = alphabet
        else:
            if dummy_label is None:
                raise ValueError("Dummy label should not be None")
            self.alphabet = _alphabet_from_rdata(rdata,
                    void_label, dummy_label)
        self.rev_alphabet = self.alphabet.reversed()
        self.data = [(Sentence(translate.sentence(rsent, self.alphabet)),
                    translate.labels(labels, self.alphabet))
                    for rsent, labels in rdata]
        self.dirs = dirs if dirs != None else range(len(rdata))

    @staticmethod
    def from_file(file_name, void_label, dummy_label, dirs_file=None):
        """Read dataset from file."""
        rdata = rawdata.from_file(file_name)
        dirs = _file_lines(dirs_file) if dirs_file != None else None
        return DataSet(rdata, void_label, dummmy_label, dirs=dirs)

    def divide(self, n, stat=(lambda x: 1)):
        """Divide dataset data to n parts."""
        return divide_data(self.data, self.dirs, n, stat=stat)

    def divide_in_two(self, r):
        """
        Divide dataset data to 2 parts.

        :param r:
            Relative size of the second part (with respect
            to data size).
        """
        return divide_in_two(self.data, self.dirs, r)

    def obtypes(self):
        """Return number of observations types -- maximum number
        of observations per word."""
        return obtypes(self.data)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, i):
        if i < 0 or i >= len(self.data):
            raise IndexError
        sent, labels = self.data[i]
        return (translate.sentence(sent, self.rev_alphabet),
                translate.labels(labels, self.rev_alphabet))

    def print_data(self, filename):
        file = open(filename, "w")
	for sent, labels in self:
            for (singles, pairs), y in zip(sent, labels):
		for x in singles:
                    assert not re.search("\s", x)
                    print >> file, x.encode('utf-8'),
                print >> file, "|",
		for x in pairs:
                    assert not re.search("\s", x)
                    print >> file, x.encode('utf-8'),
                print >> file, "|", y.encode('utf-8')
	    print >> file, ""
        file.close()
