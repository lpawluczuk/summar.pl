# -*- coding: utf-8 -*-

from polish_summaries_corpus_reader import read_psc_file
import os
from helpers import load_from_file, save_to_file, mkdir
import codecs

class AbstractDatasetProcessor(object):
    """Some description that tells you it's abstract,
    often listing the methods you're expected to supply."""

    def __init__(self, length):
        self.length = length

    def process_dir(self, summarizer, root, files):
        raise NotImplementedError("Should have implemented this")


class WideDatasetProcessor(AbstractDatasetProcessor):
    # def process_dir(self, summarizer, root, files):
    #     previous_document = None
    #     for i, name in enumerate(files):
    #         print "[Trainer] -> file: %s" % name
    #         doc_psc = read_psc_file(os.path.join(root, name), previous_document)
    #         if not doc_psc.scored:
    #             doc_psc = summarizer.score_document(doc_psc)
    #         previous_document = doc_psc
    #
    #         # file = codecs.open("result.txt", "a")
    #         # file.write("\n".join(s.sentence for s in doc_psc.get_sentences()))
    #         # file.close()
    #         # print "\n".join(s.sentence for s in doc_psc.get_sentences())
    #
    #         # for s in doc_psc.get_sentences():
    #         #     print unicode(s)
    #         yield doc_psc.get_train_data(self.length)

    def process_dir(self, summarizer, root, files):
            previous_scores = None

            for i, name in enumerate(files):
                print "[Trainer] -> file: %s" % name
                path = os.path.join("dataset_dump", os.path.join(root[root.rfind("/")+1:], name))
                path = path[:path.rfind(".")] + ".xml"
                doc_psc = load_from_file(path)
                if previous_scores:
                    for j, s in enumerate(doc_psc.get_sentences()):
                        s.scores = previous_scores[j]
                else:
                    doc_psc = summarizer.score_document(doc_psc)
                previous_scores = [s.scores for s in doc_psc.get_sentences()]
                yield doc_psc.get_train_data(self.length)


class RatioDatasetProcessor(AbstractDatasetProcessor):
    def __init__(self, length, ratio):
        super(RatioDatasetProcessor, self).__init__(length)
        if 0 < ratio <= 5:
            self.ratio = ratio
        else:
            raise Exception("Wrong ratio (1-5)")

    def process_dir(self, summarizer, root, files):
        previous_document = None
        train_data = []
        for i, name in enumerate(files):
            print "[Trainer] -> file: %s" % name
            doc_psc = read_psc_file(os.path.join(root, name), previous_document)
            previous_document = doc_psc
            train_data.append(summarizer.score_document(doc_psc).get_train_data(self.length))

        result = []
        for i, train_example in enumerate(train_data[0]):
            res_sum = 1.0 if sum(train_data[j][i][1][0] for j in range(len(train_data))) >= self.ratio else 0.0
            result.append((train_data[0][i][0], (res_sum,)))
        return [result]


class FractionDatasetProcessor(AbstractDatasetProcessor):
    def __init__(self, length, cutoff=0.0):
        super(FractionDatasetProcessor, self).__init__(length)
        if 0 <= cutoff <= 1.0:
            self.cutoff = cutoff
        else:
            raise Exception("Wrong cutoff (0.0-1.0)")

    def process_dir(self, summarizer, root, files):
        previous_document = None
        train_data = []
        for i, name in enumerate(files):
            print "[Trainer] -> file: %s" % name
            doc_psc = read_psc_file(os.path.join(root, name), previous_document)
            previous_document = doc_psc

            train_data.append(summarizer.score_document(doc_psc).get_train_data(self.length))

        result = []
        for i, train_example in enumerate(train_data[0]):
            res_sum = float(sum(train_data[j][i][1][0] for j in range(len(train_data)))) / len(train_data)
            res_sum = res_sum if res_sum >= self.cutoff else 0.0
            result.append((train_data[0][i][0], (res_sum,)))
        return [result]


class CSVWideDatasetProcessor(AbstractDatasetProcessor):
    def process_dir(self, summarizer, root, files):
        previous_document = None
        for i, name in enumerate(files):
            doc_psc = read_psc_file(os.path.join(root, name), previous_document)
            if not doc_psc.scored:
                doc_psc = summarizer.score_document(doc_psc)
            previous_document = doc_psc

            for s in doc_psc.get_train_data(self.length, True):
                print WabbitOutputFormatter().format(s[0], s[1], s[2])


class AbstractOutputFormatter(object):
    """Some description that tells you it's abstract,
    often listing the methods you're expected to supply."""

    def format(self, id, values, target):
        raise NotImplementedError("Should have implemented this")


class CSVOutputFormatter(AbstractOutputFormatter):

    def format(self, id, values, target):
        return ";".join([str(i) for i in values.values()]) + ";" + str(target[0])


class WabbitOutputFormatter(AbstractOutputFormatter):

    def format(self, id, values, target):
        feats = ["{}:{}".format(idx, values[idx]) for idx in values.keys()]
        return "{} | {} % {}".format(str(float(target[0]) + 1), ' '.join(feats), str(id)).replace("Feature.", "")


class DumpModelDatasetProcessor(AbstractDatasetProcessor):
    def process_dir(self, summarizer, root, files):
        mkdir("dataset_dump")
        mkdir(os.path.join("dataset_dump",root[root.rfind("/")+1:]))
        previous_document = None
        for i, name in enumerate(files):
            doc_psc = read_psc_file(os.path.join(root, name), previous_document)
            path = os.path.join("dataset_dump", os.path.join(root[root.rfind("/")+1:], name))
            path = path[:path.rfind(".")] + ".xml"
            print path
            save_to_file(doc_psc, path)
            previous_document = doc_psc

class DumpDatasetProcessor(AbstractDatasetProcessor):
    def __init__(self, length, to_file=False):
        self.length = length
        self.to_file = to_file
        self.dump_dir = "dataset_dump_scores"

    def mkdir(self):
        mkdir(self.dump_dir)

    def get_file_path(self, root):
        path_scores = os.path.join(self.dump_dir, root[root.rfind("/")+1:])
        mkdir(path_scores)
        return path_scores

    def dump(self, result, path_scores, name):
        if not self.to_file:
            for s in result:
                print WabbitOutputFormatter().format(s[0], s[1], s[2])
        else:
            file = codecs.open(os.path.join(path_scores, name), "w")
            file.write("\n".join(WabbitOutputFormatter().format(s[0], s[1], s[2]) for s in result))
            file.close()

class CSVWideDumpedDatasetProcessor(DumpDatasetProcessor):

    def process_dir(self, summarizer, root, files):
        previous_scores = None

        if self.to_file:
            path_scores = self.get_file_path(root)

        for i, name in enumerate(files):
            path = os.path.join("dataset_dump", os.path.join(root[root.rfind("/")+1:], name))
            path = path[:path.rfind(".")] + ".xml"
            doc_psc = load_from_file(path)
            if previous_scores:
                for j, s in enumerate(doc_psc.get_sentences()):
                    s.scores = previous_scores[j]
            else:
                doc_psc = summarizer.score_document(doc_psc)
            previous_scores = [s.scores for s in doc_psc.get_sentences()]

            self.dump(doc_psc.get_train_data(self.length, True), path_scores, name)

class CSVRatioDumpedDatasetProcessor(DumpDatasetProcessor):

    def process_dir(self, summarizer, root, files):
        previous_scores = None

        if self.to_file:
            path_scores = self.get_file_path(root)

        train_data = []
        for i, name in enumerate(files):
            path = os.path.join("dataset_dump", os.path.join(root[root.rfind("/")+1:], name))
            path = path[:path.rfind(".")] + ".xml"
            doc_psc = load_from_file(path)
            if previous_scores:
                for j, s in enumerate(doc_psc.get_sentences()):
                    s.scores = previous_scores[j]
            else:
                doc_psc = summarizer.score_document(doc_psc)
            previous_scores = [s.scores for s in doc_psc.get_sentences()]

            train_data.append(doc_psc.get_train_data(self.length, True))


        result = []
        for i, train_example in enumerate(train_data[0]):
            res_sum = 1.0 if sum(train_data[j][i][2][0] for j in range(len(train_data))) >= 3 else 0.0

            result.append((train_data[0][i][0], train_data[0][i][1], (res_sum,)))

        self.dump(doc_psc.get_train_data(self.length, True), path_scores, "ratio_" + name[2:])

class SentencesDumpDatasetProcessor(DumpDatasetProcessor):

    def process_dir(self, summarizer, root, files):
        if self.to_file:
            path_scores = self.get_file_path(root)

        path = os.path.join("dataset_dump", os.path.join(root[root.rfind("/")+1:], files[0]))
        path = path[:path.rfind(".")] + ".xml"
        doc_psc = load_from_file(path)

        file = codecs.open(os.path.join(path_scores, "sentences_" + files[0][2:]), "w")
        file.write("\n".join(str(s.id) + "\t" + s.sentence for s in doc_psc.get_sentences()))
        file.close()


class AbstractSummariesDumpDatasetProcessor(DumpDatasetProcessor):
    def __init__(self, length):
        super(AbstractSummariesDumpDatasetProcessor, self).__init__(length, True)
        self.dump_dir = os.path.join("rouge_summarization", "reference")

    def mkdir(self):
        mkdir("rouge_summarization")
        mkdir(self.dump_dir)

class SummariesDumpDatasetProcessor(AbstractSummariesDumpDatasetProcessor):
    def process_dir(self, summarizer, root, files):

        for i, name in enumerate(files):
            path = os.path.join("dataset_dump", os.path.join(root[root.rfind("/")+1:], name))
            path = path[:path.rfind(".")] + ".xml"
            doc_psc = load_from_file(path)

            file = codecs.open(os.path.join(self.dump_dir, root[root.rfind("/")+1:-4] + "_reference" + str(i+1) + ".txt"), "w")
            file.write("\n".join(s[1].sentence for s in doc_psc.get_summary(self.length)))
            file.close()

class RatioSummariesDumpDatasetProcessor(AbstractSummariesDumpDatasetProcessor):
    def process_dir(self, summarizer, root, files):

        train_data = []
        for i, name in enumerate(files):
            path = os.path.join("dataset_dump", os.path.join(root[root.rfind("/")+1:], name))
            path = path[:path.rfind(".")] + ".xml"
            doc_psc = load_from_file(path)
            train_data.append(doc_psc.get_train_data(self.length, True))

        result = []
        for i, train_example in enumerate(train_data[0]):
            res_sum = 1.0 if sum(train_data[j][i][2][0] for j in range(len(train_data))) >= 3 else 0.0
            result.append((train_data[0][i][0], train_data[0][i][1], (res_sum,)))

        sentences = doc_psc.get_sentences()

        file = codecs.open(os.path.join(self.dump_dir, root[root.rfind("/")+1:-4] + "_reference1.txt"), "w")
        file.write("\n".join(sentences[r[0]].sentence for r in result if r[2][0] == 1.0))
        file.close()
