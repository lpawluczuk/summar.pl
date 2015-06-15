# -*- coding: utf-8 -*-
from models import Document
from helpers import read_file
from itertools import izip
from enum import Enum

SUMMARIES_TAG = "#### SUMMARIES ####"
START_TAG = "#### SUMMARY START ####"
END_TAG = "#### SUMMARY END ####"


class SummaryLength(Enum):
    SHORT = 0  # 5%
    MEDIUM = 1  # 10%
    LONG = 2  # 20%

    def __str__(self):
        return self.name


class PSCDocument(Document):
    def __init__(self, text, document=None):
        Document.__init__(self, text[:text.index(SUMMARIES_TAG)], document.paragraphs if document else [],
                          document.tokens_map if document else {}, document.scored if document else False)
        self.summaries = self.get_summaries(
            [s.split() for s in self.get_summaries_indexes_list(text[text.index(SUMMARIES_TAG):])])

    def get_summaries(self, summaries_list):
        doc_sentences = self.get_sentences()
        summaries = []
        for summary in summaries_list:
            sentences = set()

            s_index = 0
            for ch_index in summary:
                while int(ch_index) > doc_sentences[s_index].end_index:
                    s_index += 1
                sentences.add(s_index)
            summaries.append(sentences)
        return summaries

    def get_summaries_indexes_list(self, summaries):
        summaries_list = []
        while START_TAG in summaries:
            summaries_list.append(
                summaries[summaries.index(START_TAG) + len(START_TAG):summaries.index(END_TAG)].strip())
            summaries = summaries[summaries.index(END_TAG) + len(END_TAG):]
        return summaries_list


    def get_train_data(self, summary_length, features_names=False):
        res = [1 if i in self.summaries[summary_length.value] else 0 for i in xrange(len(self.get_sentences()))]

        if features_names:
            return [(s.id, s.scores, (r,)) for s, r in izip(self.get_sentences(), res)]
        return [(tuple(s.scores.values()), (r,)) for s, r in izip(self.get_sentences(), res)]

    def get_summary(self, summary_number):
        sentences = self.get_sentences()
        return [(i, sentences[i], 0.0) for i in self.summaries[summary_number.value]]

    def get_not_summary(self, summary_number):
        sentences = self.get_sentences()
        for sentence in sentences:
            if sentence.id in self.summaries[summary_number.value]:
                continue
            yield (sentence.id, sentence, 0.0)

    def get_summaries_overlap(self):
        """ Returns overlap of single doc summaries with length 5, 10, 15 sentences """

        intersections = [float(len(self.summaries[2].intersection(self.summaries[1]))) / len(self.summaries[2]),
                         float(len(self.summaries[2].intersection(self.summaries[0]))) / len(self.summaries[2]),
                         float(len(self.summaries[1].intersection(self.summaries[0]))) / len(self.summaries[1])]

        return sum(intersections) / len(intersections)


def read_psc_file(file_path, previous_document=None):
    return PSCDocument(read_file(file_path), previous_document)
