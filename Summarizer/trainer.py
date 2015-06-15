# -*- coding: utf-8 -*-
import os
import argparse
from helpers import save_to_file, load_from_file, normalize
from polish_summaries_corpus_reader import read_psc_file
from summarization.summarizer import Summarizer
from pybrain.tools.shortcuts import buildNetwork
from pybrain.datasets import SupervisedDataSet
from pybrain.supervised.trainers import BackpropTrainer
import math
import codecs

import numpy as np

from sklearn.svm import SVC
from sklearn.cross_validation import StratifiedKFold
from sklearn.grid_search import GridSearchCV


class AbstractTrainer(object):
    """Some description that tells you it's abstract,
    often listing the methods you're expected to supply."""

    def train(self, summarizer, dataset, testset, model_path):
        raise NotImplementedError("Should have implemented this")


class TrainerWrapper():
    def __init__(self, features, config):
        self.train_method = config.get_train_method()
        self.process_dir = config.get_dir_processor()
        self.summarizer = Summarizer.Instance()
        self.summarizer.set_features(features, config.get_stop_list_path())
        self.features = features

    def train(self, train_dir, test_dir, dataset_path=None, dump_dataset=True):
        testset = SupervisedDataSet(len(self.summarizer.get_features()), 1)
        min_maxs = [[100, 0] for i in range(len(self.summarizer.get_features()))]

        if dataset_path and dataset_path != 'None':
            dataset = load_from_file(dataset_path)
            min_maxs = load_from_file("meta_model.xml")  # sprawidzć ścieżke!
        else:
            dataset = SupervisedDataSet(len(self.summarizer.get_features()), 1)

            for root, dirs, files in os.walk(train_dir, topdown=False):
                for file_ds in self.process_dir(self.summarizer, root, files):
                    for ds in file_ds:
                        dataset.addSample(ds[0], ds[1])
                        min_maxs = self.update_min_maxs(min_maxs, ds[0])
                # break  # remove this !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

                # print min_maxs

            inp = []
            for d in dataset['input']:
                inp.append([normalize(val, min_maxs[i][0], min_maxs[i][1]) for i, val in enumerate(d)])

            dataset.setField("input", inp)
            # print dataset['input']


        ### TEMP
        # save_dataset_as_csv(dataset)

        if dump_dataset:
            save_to_file(dataset, "dataset.xml")

        if test_dir:
            for root, dirs, files in os.walk(test_dir, topdown=False):
                for file_ds in self.process_dir(self.summarizer, root, files):
                    for ds in file_ds:
                        testset.addSample(ds[0], ds[1])

        print "[Trainer] -> training..."
        save_to_file(min_maxs, self.features.replace("features.txt", "meta_model.xml"))

        self.train_method(self.summarizer, dataset, testset, self.features.replace("features.txt", "model.xml"))


    def update_min_maxs(self, min_maxs, ds):
        for i, d in enumerate(ds):
            if min_maxs[i][0] > d:
                min_maxs[i][0] = d
            if min_maxs[i][1] < d:
                min_maxs[i][1] = d
        return min_maxs


class NeuralNetworkTrainer(AbstractTrainer):
    def train(self, summarizer, dataset, testset, model_path):
        net = buildNetwork(len(summarizer.get_features()), 5, 5, 5, 1, bias=True)  #, hiddenclass=TanhLayer)

        trainer = BackpropTrainer(net, dataset, learningrate=0.001, momentum=0.99)
        # trainer.trainUntilConvergence()

        if testset:
            errors = trainer.trainUntilConvergence(verbose=True,
                                                   trainingData=dataset,
                                                   validationData=testset,
                                                   maxEpochs=10)
        else:
            errors = trainer.trainUntilConvergence(verbose=True,
                                                   trainingData=dataset,
                                                   validationProportion=0.1,
                                                   maxEpochs=10)

        print "[Trainer] -> training done."
        print errors
        save_to_file(net, model_path)
        print "[Trainer] -> model save to model.xml file."


class SVMTrainer(AbstractTrainer):
    def train(self, summarizer, dataset, testset, model_path):
        clf = svm.SVC(cache_size=5000, verbose=True, C=10, gamma=0.2)
        print clf.fit(dataset['input'], dataset['target'])
        save_to_file(clf, model_path)

def save_dataset_as_csv(dataset):
    file = codecs.open("dataset.csv", "w", "utf-8")
    for input, target in zip(dataset['input'], dataset['target']):
        file.write(";".join([str(i) for i in input]) + ";" + str(target[0]) + "\n")


def get_summary(root, files, not_summary=False):
    previous_document = None
    for i, name in enumerate(files):
        print "[Trainer] -> file: %s" % name
        doc_psc = read_psc_file(os.path.join(root, name), previous_document)
        previous_document = doc_psc
        # print "\n".join(unicode(s[1]) for s in doc_psc.get_not_summary(0))
        result = doc_psc.get_not_summary(0) if not_summary else doc_psc.get_summary(0)

        file = codecs.open("result.txt", "a", "utf-8")
        file.write("\n".join(unicode(s[1]) for s in result))
        file.write("\nEOF\n")


def print_summaries(train_dir, not_summary=False):
    for root, dirs, files in os.walk(train_dir, topdown=False):
        get_summary(root, files, not_summary)


############################


def check_summaries_overlap(train_dir):
    overlap = []
    var = []
    for root, dirs, files in os.walk(train_dir, topdown=False):
        previous_document = None

        summaries = []
        for i, name in enumerate(files):
            print "[Trainer] -> file: %s" % name
            doc_psc = read_psc_file(os.path.join(root, name), previous_document)
            previous_document = doc_psc
            summaries.append(doc_psc.summaries[0])

        intersections = []
        for i in range(len(summaries)):
            for j in range(len(summaries)):
                if j <= i:
                    continue
                intersections.append(float(len(summaries[i].intersection(summaries[j]))) / len(summaries[i]))

        if len(intersections) == 0:
            print "Skipping"
            continue
        o = sum(intersections) / len(intersections)
        v = sum(math.pow(i - o, 2) for i in intersections) / len(intersections)
        print "Average: ", o
        print "Var: ", v
        overlap.append(o)
        var.append(v)

    final_o = sum(overlap) / len(overlap)
    final_v = sum(var) / len(var)
    print "AVERAGE OVERLAP: %s, AVERAGE VAR: %s" % (final_o, final_v)


def main(mode, files):
    if mode == "CHECK":
        check_summaries_overlap(files)
    elif mode == "PRINT":
        print_summaries(files)
    elif mode == "PRINT_NOT":
        print_summaries(files, True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices=["CHECK", "PRINT", "PRINT_NOT"],
                        help="program mode", required=True)
    parser.add_argument("-f", "--files", help="files to process")
    args = parser.parse_args()

    main(args.mode, args.files if args.files else "/home/lukasz/Projects/PracaMagisterska/Inne/datasets/trainset/")
