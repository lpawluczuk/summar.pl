import os
import re
import gzip
from itertools import takewhile, repeat, starmap, imap, groupby, izip_longest
from itertools import islice
from Queue import Queue
from threading import Thread

import xml.sax

from morph_handler import MorphHandler
from names_handler import NamesHandler
from ner.labels import dicts2names

MAX_Q_SIZE = 1

def repeatfunc(func, times=None, *args):
    """Repeat calls to func with specified arguments.

    Example:  repeatfunc(random.random)
    """
    if times is None:
        return starmap(func, repeat(args))
    return starmap(func, repeat(args, times))

def queue_iterator(queue):
    return takewhile(lambda x: x != None, repeatfunc(queue.get))

def take(n, iterable):
    "Return first n items of the iterable as a list"
    return list(islice(iterable, n))

class TEIReader(object):
    '''
    classdocs
    '''

    def __init__(self, dirname):
        self._dirname = dirname
        morph_gz = os.path.join(dirname, 'ann_morphosyntax.xml.gz')
        self._gzipped = os.path.isfile(morph_gz)

    def ids(self):
        """Return paragraph id and sentence ids for each paragraph."""
	# par_start = re.compile("\s*<%s [^>]*>\s*" % "p")
	par_start = re.compile("<p ")
	par_end = re.compile("</p>")
	sent_start = re.compile("<s ")
	sent_end = re.compile("</s>")
        get_id = re.compile("xml:id=\"(.*?)\"")

        par_id = None
        sent_ids = None

        if self._gzipped:
            f = gzip.open(os.path.join(self._dirname, 'ann_morphosyntax.xml.gz'))
        else:
            f = open(os.path.join(self._dirname, 'ann_morphosyntax.xml'))

        for line in f:
	    if par_start.search(line):
                par_id = get_id.search(line).group(1)
                sent_ids = []
            elif par_end.search(line):
                yield par_id, sent_ids
	    elif sent_start.search(line):
                sent_ids.append(get_id.search(line).group(1))
        f.close()

    def segments(self):
        """Return segments for each sentence."""
        queue = Queue(maxsize=MAX_Q_SIZE)
        thread = Thread(target=self._parse_morph, args=(queue,))
        thread.start()
        for par_id, sent_id, sent_segs in queue_iterator(queue):
            yield sent_segs
        thread.join()

    def names(self, ann_named):
        """Return names for each sentence."""
        segments = self.segments()
        queue = Queue(maxsize=MAX_Q_SIZE)
        thread = Thread(target=self._parse_names, args=(ann_named, queue))
        thread.start()
        for sent_names, sent_segs in izip_longest(queue_iterator(queue), segments):
            # Probably different size of queues and different number of
            # sentences in ann_morph/ann_named files.
            assert sent_names != None and sent_segs != None
            yield dicts2names(sent_names, sent_segs), sent_segs
        thread.join()

    def paragraphs(self):
        """Return segments for each sentence for each paragraph."""
        queue = Queue(maxsize=MAX_Q_SIZE)
        thread = Thread(target=self._parse_morph, args=(queue,))
        thread.start()
        for par_id, contents in groupby(
                queue_iterator(queue),
                key=lambda elem: elem[0]):
            contents = imap(lambda elem: elem[1:], contents)
            yield (par_id, contents)
        thread.join()

    def paragraphs_with_names(self, ann_named):
        """Return segments *and* NEs for each sentence for each paragraph."""
        queue = Queue(maxsize=MAX_Q_SIZE)
        thread = Thread(target=self._parse_names, args=(ann_named, queue))
        thread.start()
        names_iterator = queue_iterator(queue)
        for par_id, par_contents in self.paragraphs():
            par_contents = list(par_contents)
            par_names = take(len(par_contents), names_iterator)
            yield (par_id, [(sent_id, sent, dicts2names(names, sent))
                for (sent_id, sent), names
                in izip_longest(par_contents, par_names)])
        thread.join()
    
    def _parse_morph(self, queue):
        if self._gzipped:
            f = gzip.open(os.path.join(self._dirname, 'ann_morphosyntax.xml.gz'))
        else:
            f = open(os.path.join(self._dirname, 'ann_morphosyntax.xml'))
        handler = MorphHandler(queue)
        xml.sax.parse(f, handler)
        f.close()
    
    def _parse_names(self, filename, queue):
        if filename.endswith(".gz"):
            f = gzip.open(os.path.join(self._dirname, filename))
        else:
            f = open(os.path.join(self._dirname, filename))
        handler = NamesHandler(queue)
        xml.sax.parse(f, handler)
        f.close()
