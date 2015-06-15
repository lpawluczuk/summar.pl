# encoding=utf-8

import gzip

from crf import const

__all__ = ['Alphabet']

def sections(predicate, iterable):
    """sections(lambda x: x % 3 == 0, range(9))
    --> [[0, 1, 2], [3, 4, 5], [6, 7, 8]]"""
    value = []
    last = None
    for x in iterable:
        if predicate(x):
            if last != None:
                value.append(last)
            last = [x]
        else:
            last.append(x)
    value.append(last)
    return value

class Alphabet:
    """ Stores:
    - Observations alphabet,
    - Labels alphabet.
    """
	
    def __init__(self, void_label=None, dummy_label="DUMMY",
            observations=None, labels=None):
    	# Dummy label -- label for word before first word in sentence.
	self.dummy_label = dummy_label
	self.void_label = void_label

	self.observations = observations if observations != None else {}
        if labels != None:
            assert labels[self.dummy_label] == const.dummy_id
            self.labels = labels
        else:
            self.labels = {self.dummy_label: const.dummy_id}
            if self.void_label != None:
                self.add_label(self.void_label)

    def save(self, filename=None, fileobj=None):
        """Save alphabet in file_name using custom format."""
        if not fileobj:
            out = gzip.open(filename, 'wb')
        else:
            out = fileobj

        def fprint(*args):
            for arg in args:
                print >> out, arg.encode('utf-8'),
            print >> out, ""
        fprint("#DUMMY LABEL:", self.dummy_label)
        fprint("#VOID LABEL:", self.void_label)
        fprint("#OBSERVATIONS:")
        for k, v in self.observations.iteritems():
            fprint(k, str(v))
        fprint("#LABELS:")
        for k, v in self.labels.iteritems():
            fprint(k, str(v))

        if not fileobj:
            out.close()

    @staticmethod
    def load(filename=None, fileobj=None):
        """Load alphabet saved in custom format from filename."""

        def parse(inp):
            for section in sections(lambda line: line.startswith("#"), inp):
                name, value = map(lambda x: x.strip(),
                        section[0].lstrip("#").split(":"))
                yield name, value, section[1:]

        if not fileobj:
            inp = gzip.open(filename, 'rb')
        else:
            inp = fileobj

        header = {}
        observations = {}
        labels = {}
        for (name, value, contents) in parse(inp):
            if name in ["OBSERVATIONS", "LABELS"]:
                d = observations if name == "OBSERVATIONS" else labels
                for line in contents:
                    key, val = line.split()
                    d[key.decode('utf-8')] = int(val)
            else:
                header[name] = value
        return Alphabet(header["VOID LABEL"], header["DUMMY LABEL"],
                observations, labels)

    def observation(self, x):
	return self.observations.get(x)

    def label(self, x):
	return self.labels.get(x)

    def translate_feature(self, feat):
        (y1, y2, x) = feat
        if y1 != -1 and not self.labels.has_key(y1):
            return None
        if not self.labels.has_key(y2):
            return None
        if not self.observations.has_key(x):
            return None

        if y1 != -1:
            y1 = self.label(y1)
        y2 = self.label(y2)
        x = self.observation(x)
        return (y1, y2, x)
 
    def _add(self, alphabet, x):
	if not alphabet.has_key(x):
	    alphabet[x] = len(alphabet)

    def add_observation(self, x):
	self._add(self.observations, x)

    def add_label(self, x):
        if x == self.dummy_label:
            raise ValueError("label should be different than dummy label")
	self._add(self.labels, x)

    def reversed(self):
	if self.void_label != None:
	    void_label_tr = self.label(self.void_label)
	else:
	    void_label_tr = None
	rev_alph = Alphabet(void_label_tr, self.label(self.dummy_label))

	for label in self.labels:
	    rev_alph.labels[ self.label(label) ] = label

	for obs in self.observations:
	    rev_alph.observations[ self.observation(obs) ] = obs

	return rev_alph
