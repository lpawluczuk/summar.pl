#-*- coding: utf-8 -*-

__all__ = ["TEIAnnotator"]

import os
import shutil
import gzip
from itertools import izip
from multiprocessing import JoinableQueue
from multiprocessing import Process, Lock
from ner.nerecognizer import NERecognizer
from read import TEIReader
import write

NAMES_XML = 'ann_named.xml'
NAMES_XML_GZ = NAMES_XML+'.gz'

def get_dirs(root):
    for desc_dir, dirs, files in os.walk(root):
        if any(map(
               lambda f: f in files, 
               ['ann_morphosyntax.xml', 'ann_morphosyntax.xml.gz'])):
            yield desc_dir

class NERWorker(Process):
    """Process executing tasks from a given NER tasks queue"""
    def __init__(self, model_file, tasks):
        self.model_file = model_file
        self.tasks = tasks
        Process.__init__(self)

    def _out_name(self, output_dir, save_gzipped):
        if save_gzipped:
            return os.path.join(output_dir, NAMES_XML_GZ)
        else:
            return os.path.join(output_dir, NAMES_XML)

    def _tmp_name(self, output_dir, save_gzipped):
        if save_gzipped:
            return os.path.join(output_dir, "." + NAMES_XML_GZ)
        else:
            return os.path.join(output_dir, "." + NAMES_XML)

    def _output_for(self, fname, save_gzipped):
        # fname = self._out_name(output_dir, save_gzipped)
        if save_gzipped:
            return gzip.open(fname, 'wb')
        else:
            return open(fname, 'w')

    def _annotations(self, wypluwka_dir):
        reader = TEIReader(wypluwka_dir)
        def contents_iter(contents):
            for sent_id, sent in contents:
                names = self.ner.recognize_named_entities(sent)
                yield sent_id, names
        for par_id, contents in reader.paragraphs():
            yield (par_id, contents_iter(contents))

    def annotate_dir(self, wypluwka_dir, output_dir, save_gzipped=True):
        tmp_name = self._tmp_name(output_dir, save_gzipped)
        out = self._output_for(tmp_name, save_gzipped)
        write.write(out, self._annotations(wypluwka_dir))
        out.close()
        shutil.move(tmp_name, self._out_name(output_dir, save_gzipped))
    
    def run(self):
        self.ner = NERecognizer.load(self.model_file)
        while True:
            args, kwargs = self.tasks.get()
            try:
                self.annotate_dir(*args, **kwargs)
            except Exception, e:
                print e
            self.tasks.task_done()

class NERPool:
    """Pool of ners consuming tasks from a queue"""
    def __init__(self, model_file, processes=1):
        self.tasks = JoinableQueue(processes)
        self.workers = []
        for _ in range(processes):
            worker = NERWorker(model_file, self.tasks)
            worker.start()
            self.workers.append(worker)

    def add_task(self, *args, **kwargs):
        """Add a NER task to the queue"""
        self.tasks.put((args, kwargs))

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()
        for worker in self.workers:
            worker.terminate()
        for worker in self.workers:
            worker.join()

class TEIAnnotator:
    
    def __init__(self, model_file, processes=1):
        self.nerpool = NERPool(model_file, processes)
    
    def annotate(self, 
                 wypluwka_root, 
                 output_root=None, 
                 save_gzipped=True,
                 overwrite=False, 
                 verbose=True):
        if output_root == None:
            output_root = wypluwka_root
        wypluwka_root = wypluwka_root.rstrip(os.path.sep)

        ann_named = NAMES_XML_GZ if save_gzipped else NAMES_XML
        for wypluwka_dir in get_dirs(wypluwka_root):
            output_dir = os.path.join(output_root,
                    wypluwka_dir[len(wypluwka_root)+1:])
            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)
            if overwrite == False and ann_named in os.listdir(output_dir):
                if verbose:
                    print "Skipping", wypluwka_dir
                continue
            if verbose:
                print "Annotating", wypluwka_dir
            self.nerpool.add_task(wypluwka_dir, output_dir,
                    save_gzipped=save_gzipped)
        self.nerpool.wait_completion()
