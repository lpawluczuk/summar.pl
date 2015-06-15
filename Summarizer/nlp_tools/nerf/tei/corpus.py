import sys
import os
import traceback
import random
import re

from ner.features import sent2features, parse_feature_names
from ner.labels import encode, tuple2label

from read import TEIReader
#from atlas import atlas_nes

# TODO: Ponizsze przeniesc do skryptu nes_from_corpus_to_corpus.
#def flatten(l):
#    v = []
#    for x in l:
#        v.extend(x)
#    return v
#
def corpus_dirs(root, ann_named="ann_named.xml"):
    for desc_dir, dirs, files in os.walk(root):
        if (('ann_morphosyntax.xml' in files or
            'ann_morphosyntax.xml.gz' in files) and
            ann_named in files):
            yield re.sub(root, "", desc_dir).lstrip("/")

def parse_dir(dirname, features, ann_named="ann_named.xml"):
    reader = TEIReader(dirname)
    names = list(reader.names(ann_named))
    names, segs = zip(*names)
    data = []
    for (sent_names, sent_segs) in zip(names, segs):
        words = sent2features(sent_segs, features)
        labels = map(tuple2label, encode(sent_names, sent_segs))
        data.append((
            (sent_segs, sent_names), (words, labels)
            ))
    return data

def read_tei_corpus(tei_corpus, schema, black_listed=[], select=1.0,
        ann_named="ann_named.xml", verbose=False):
    """
    Read data from TEI corpus.
    
    :params:
    --------
    tei_corpus : path
        Path to TEI corpus.
    schema : list
        List of observation types included.
    black_listed : list
        Skip corpus subdirectories present in the list.
    select : float in [0.0, 1.0]
        Select random $select * 100% files from corpus.
    ann_named : str
        Use this name to find NE files.
    """
    features = parse_feature_names(schema)
    raw_data, dirs = [], []
    random.seed(0)
    for dirname in corpus_dirs(tei_corpus, ann_named):
        if (any(dirname.endswith(black) for black in black_listed) or
                random.random() > select):
            if verbose:
                print "Skipping directory", dirname
            continue
        elif verbose:
            print "Reading directory", dirname
        try:
            sent_data = parse_dir(os.path.join(tei_corpus, dirname),
                    features, ann_named)
            raw_data.extend(sent_data)
            dirs.extend([dirname] * len(sent_data))
        except:
            info = sys.exc_info()
            print "Exception:", info[1]
            traceback.print_tb(info[2], file=sys.stdout)
    return raw_data, dirs

