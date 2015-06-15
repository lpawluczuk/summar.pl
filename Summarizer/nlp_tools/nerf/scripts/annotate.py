#!/usr/bin/env python

import sys
import os

# Solution with no hard coded path would be welcome
sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])) + "/../")

from optparse import OptionParser
from ner.nerecognizer import NERecognizer

from tei.annotate import TEIAnnotator

if __name__ == "__main__":
    optparser = OptionParser(usage=
    """%prog CORPUS MODEL
	            
        Recognize NEs in CORPUS subdirectories using CRF model
        from MODEL file and write output to ann_named.xml.gz
        files in respective directories.""")

    optparser.add_option("-o", "--output_root", default=None,
            dest="output_root",
            help="Use another directory to store output.")
    optparser.add_option("-r", "--overwrite", action="store_true",
            default=False,
            dest="overwrite",
            help="Overwrite existing ann_named files.")
    optparser.add_option("--processes", type="int", default=1,
            dest="processes",
            help="number of processes in parallel annotation")

    (options, args) = optparser.parse_args()
    if len(args) != 2:
        optparser.print_help()
        sys.exit()

    corpus_path, model_file = args
    # annotator = TEIAnnotator(NERecognizer.load(model_file))
    annotator = TEIAnnotator(model_file, processes=options.processes)
    annotator.annotate(corpus_path,
            options.output_root,
            overwrite=options.overwrite)
