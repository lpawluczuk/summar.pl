# -*- coding: utf-8 -*-
import os
from Summarizer.polish_summaries_corpus_reader import read_psc_file
from Summarizer.summarization.summarizer import Summarizer


class EvaluatorWrapper():
    def __init__(self, model, features, config):
        self.summarizer = Summarizer.Instance()
        self.summarizer.set_model(model, features, config)
        self.evaluation_method = StrictEvaluator(self.summarizer, config.get_length()).evaluate

    def evaluate(self, test_dir):
        all_tp, all_fp, all_fn, final_precision, final_recall, f_score = self.evaluation_method(test_dir)

        print "###########################################"
        print "Evaluation done."
        print "True positives: %s False positives: %s False negatives: %s" % (all_tp, all_fp, all_fn)
        print "Precision: %.2f Recall: %.2f, F-1 Score: %.2f" % (final_precision, final_recall, f_score)


def average(l):
    return sum(l) / len(l)


class EvaluationResult(object):
    def __init__(self, tp=0, fp=0, fn=0):
        self.tp = tp
        self.fp = fp
        self.fn = fn

    def get_precision(self):
        return float(self.tp) / (self.tp + self.fp) if (self.tp + self.fp) != 0 else 0

    def get_recall(self):
        return float(self.tp) / (self.tp + self.fn) if (self.tp + self.fn) != 0 else 0

    def get_f_score(self):
        precision = self.get_precision()
        recall = self.get_recall()
        return 2 * (precision * recall) / (precision + recall)

    def __str__(self):
        return "Precision: %.2f Recall: %.2f, F-1 Score: %.2f" % (
            self.get_precision(), self.get_recall(), self.get_f_score())


class AbstractEvaluator(object):
    """Some description that tells you it's abstract,
    often listing the methods you're expected to supply."""

    def __init__(self, summarizer, length):
        self.summarizer = summarizer
        self.length = length

    def evaluate(self, test_dir, model, features, stop_list):
        raise NotImplementedError("Should have implemented this")


class StrictEvaluator(AbstractEvaluator):
    def evaluate(self, test_dir):
        all_tp = 0
        all_fp = 0
        all_fn = 0
        all_precisions = []
        all_recalls = []

        for root, dirs, files in os.walk(test_dir, topdown=False):
            dir_precisions = []
            dir_recalls = []

            if not files:
                continue
            prev_doc = None
            for name in files:
                file_path = os.path.join(root, name)
                doc_psc = read_psc_file(file_path, prev_doc)
                prev_doc = doc_psc
                expected_sentences = doc_psc.summaries[self.length.value]
                scored_sentences = set([s[0] for s in
                                        self.summarizer.create_summary(doc_psc).get_scored_sentences_numbers(
                                            len(doc_psc.summaries[self.length.value]))])

                tp = len(expected_sentences.intersection(scored_sentences))
                fp = len(scored_sentences.difference(expected_sentences))
                fn = len(expected_sentences.difference(scored_sentences))
                dir_result = EvaluationResult(tp, fp, fn)

                dir_precisions.append(dir_result.get_precision())
                dir_recalls.append(dir_result.get_recall())

                all_tp += tp
                all_fp += fp
                all_fn += fn
                # print "File: ", name
                # print "TP: ", tp, " FP: ", fp, " FN: ", fn
                # print "Precision: ", precision, " Recall: ", recall
            dir_p = average(dir_precisions)
            dir_r = average(dir_recalls)
            all_precisions.append(dir_p)
            all_recalls.append(dir_r)
            print "File %s, Precision: %.2f File Recall: %.2f" % (root[-16:], dir_p, dir_r)

            # break # remove this !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        final_precision = average(all_precisions)
        final_recall = average(all_recalls)
        f_score = 2 * (final_precision * final_recall) / (final_precision + final_recall)

        # print "Max precision in file: %2f, Max recall in file: %.2f" % (max(all_precisions), max(all_recalls))
        return all_tp, all_fp, all_fn, final_precision, final_recall, f_score


class CorpusEvaluator(AbstractEvaluator):
    def evaluate(self, test_dir):
        all_tp = 0
        all_fp = 0
        all_fn = 0

        for root, dirs, files in os.walk(test_dir, topdown=False):
            if not files:
                continue
            prev_doc = None
            for name in files:
                file_path = os.path.join(root, name)
                doc_psc = read_psc_file(file_path, prev_doc)
                prev_doc = doc_psc
                expected_sentences = doc_psc.summaries[self.length.value]
                scored_sentences = set([s[0] for s in
                                        self.summarizer.create_summary(doc_psc).get_scored_sentences_numbers(
                                            len(doc_psc.summaries[self.length.value]))])

                tp = len(expected_sentences.intersection(scored_sentences))
                fp = len(scored_sentences.difference(expected_sentences))
                fn = len(expected_sentences.difference(scored_sentences))

                all_tp += tp
                all_fp += fp
                all_fn += fn
                # print "File: ", name
                # print "TP: ", tp, " FP: ", fp, " FN: ", fn
                # print "Precision: ", precision, " Recall: ", recall
            # print "File %s, Precision: %.2f File Recall: %.2f" % (root[-16:], dir_p, dir_r)
            print "File %s, evaluated" % (root[-16:],)
            # break # remove this !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        precision = float(all_tp) / (all_tp + all_fp) if (all_tp + all_fp) != 0 else 0
        recall = float(all_tp) / (all_tp + all_fn) if (all_tp + all_fn) != 0 else 0
        f_score = 2 * (precision * recall) / (precision + recall)

        # print "Max precision in file: %2f, Max recall in file: %.2f" % (max(all_precisions), max(all_recalls))
        return all_tp, all_fp, all_fn, precision, recall, f_score


class WideEvaluator(AbstractEvaluator):
    def evaluate(self, test_dir):
        all_tp = 0
        all_fp = 0
        all_fn = 0
        all_precisions = []
        all_recalls = []

        for root, dirs, files in os.walk(test_dir, topdown=False):
            dir_precisions = []
            dir_recalls = []

            if not files:
                continue
            prev_doc = None
            expected_sentences = []
            for name in files:
                file_path = os.path.join(root, name)
                doc_psc = read_psc_file(file_path, prev_doc)
                prev_doc = doc_psc
                expected_sentences += doc_psc.summaries[self.length.value]

                # print "File: ", name
                # print "TP: ", tp, " FP: ", fp, " FN: ", fn
                # print "Precision: ", precision, " Recall: ", recall

            scored_sentences = set([s[0] for s in
                                    self.summarizer.create_summary(doc_psc).get_scored_sentences_numbers(
                                        len(doc_psc.summaries[self.length.value]))])
            expected_sentences = set(expected_sentences)
            tp = len(expected_sentences.intersection(scored_sentences))
            fp = len(scored_sentences.difference(expected_sentences))
            fn = len(expected_sentences.difference(scored_sentences))
            precision = float(tp) / (tp + fp) if (tp + fp) != 0 else 0
            recall = float(tp) / (tp + fn) if (tp + fn) != 0 else 0

            all_tp += tp
            all_fp += fp
            all_fn += fn

            all_precisions.append(precision)
            all_recalls.append(recall)
            print "File %s, Precision: %.2f File Recall: %.2f" % (root[-16:], precision, recall)

            # break # remove this !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        final_precision = average(all_precisions)
        final_recall = average(all_recalls)
        f_score = 2 * (final_precision * final_recall) / (final_precision + final_recall)

        # print "Max precision in file: %2f, Max recall in file: %.2f" % (max(all_precisions), max(all_recalls))
        return all_tp, all_fp, all_fn, final_precision, final_recall, f_score