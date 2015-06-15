#-*- coding: utf-8 -*-
import operator
import codecs
from collections import Counter
from operator import xor
from helpers import read_file
from nlp_tools import NLP

""" Module contains definition of all object classes used in program. """


class Document:
    """ Class representing document """

    def __init__(self, text, paragraphs=[], tokens_map={}, scored=False):
        # a = datetime.datetime.now()
        self.text = text
        self.paragraphs = paragraphs if paragraphs else self.init_paragraphs()
        self.tokens_map = tokens_map if tokens_map else self.get_term_occurences_map()
        self.named_entities_frequency = self.count_ne_frequency()
        self.named_entities_count = self.count_ne()
        self.scored = scored
        # b = datetime.datetime.now()
        # c = (b - a).seconds
        # if c != 0:
        #     print c

    def __len__(self):
        return sum([len(p) for p in self.paragraphs])

    def init_paragraphs(self):
        paragraphs = []
        temp_text = self.text
        index = 0

        current_id = 0
        for p in NLP.Instance().paragraphs(self.text):
            paragraph = []
            sentences = NLP.Instance().segment(p)
            for s in sentences:
                index += temp_text.index(s)
                temp_text = temp_text[temp_text.index(s)+len(s):]

                if NLP.Instance().is_header(s):
                    if paragraph:
                        paragraphs.append(Paragraph(paragraph))
                        paragraph = []
                    paragraphs.append(Paragraph([Sentence(current_id, s, index, index+len(s), is_header=True)]))
                else:
                    paragraph.append(Sentence(current_id, s, index, index+len(s)))

                index += len(s)
                current_id += 1

            if paragraph:
                paragraphs.append(Paragraph(paragraph))
        return paragraphs

    def get_sentences(self):
        return [s for p in self.paragraphs for s in p.sentences]

    def get_words_count(self):
        return sum([len(s.tokens) for s in self.get_sentences()])

    def get_introduction_paragraph_number(self):
        """ Introduction paragraph is first non header one. """
        for i, p in enumerate(self.paragraphs):
            for s in p.sentences:
                if s.is_header:
                    break
                return i

    def get_conclusion_paragraph_number(self):
        """ Conclustion paragraph is last non header one. """
        for i, p in enumerate(reversed(self.paragraphs)):
            for s in p.sentences:
                if s.is_header:
                    break
                return len(self.paragraphs) - i - 1

    def get_term_occurences_map(self):
        tokens = {}
        for s in self.get_sentences():
            for token in s.lemmas:
                if token in tokens:
                    continue
                tokens[token] = sum(1.0 for s in self.get_sentences() if token in s.lemmas)
        return tokens

    def count_ne_frequency(self):
        named_entities = {}
        for s in self.get_sentences():
            for ne in s.named_entities:
                if ne in named_entities:
                    continue
                named_entities[ne] = sum(1.0 for s in self.get_sentences() if ne in s.named_entities)
        return named_entities

    def count_ne(self):
        return sum(self.named_entities_frequency[ne] for ne in self.named_entities_frequency.keys())

    def print_content(self):
        """ Method prints lists of tokens for every sentence in document. """
        print "[Document] --> print_content: "
        for s in self.get_sentences():
            print s.tokens

    def __str__(self):
        return "[Document] --> content: " + self.text


class Paragraph:
    """ Class representing paragraph """

    def __init__(self, sentences):
        self.sentences = sentences

    def __len__(self):
        return len(self.sentences)

import datetime

class Sentence:
    """ Class representing sentence """

    def __init__(self, id_sentence, sentence, start_index, end_index, is_header=False):
        self.id = id_sentence
        self.sentence = sentence
        self.tokens, self.lemmas, self.pos_tags = NLP.Instance().tokenize_lematize_pos_tags(self.sentence)
        self.tokens_lower = [x.lower() for x in self.tokens]
        self.named_entities = NLP.Instance().ner(self.sentence)
        self.start_index = start_index
        self.end_index = end_index
        self.scores = {}
        self.is_header = is_header

    def update_scores(self, key, score):
        self.scores[key] = score

    def get_tokens_counter(self):
        return Counter(self.tokens)

    def __len__(self):
        return len(self.tokens)

    def __eq__(self, other):
        for x, y in zip(self.tokens, other.tokens):
                if x != y:
                    return False
        return self.sentence==other.sentence

    def __hash__(self):
        return hash(('sentence', self.sentence)) 

    def __unicode__(self):
        return self.sentence


class Summary:
    """ Class representing summary """

    def __init__(self, document, length=10):
        self.document = document
        self.scored_sentences = {i:0.0 for i, s in enumerate(document.get_sentences())}
        self.num_to_extract = self.get_num_to_extract(length)

    def set_scores(self, scores):
        self.scored_sentences = scores

    def get_num_to_extract(self, length):
        return int((int(length)/100.0) * self.document.get_words_count())

    def get_scored(self):
        summary_sentences = []
        sorted_sentences = sorted(self.scored_sentences.items(), key=operator.itemgetter(1), reverse=True)
        current_length = 0
        sentences = self.document.get_sentences()

        while current_length < self.num_to_extract:
            s_index = sorted_sentences.pop(0)
            summary_sentences.append((s_index[0], sentences[s_index[0]], s_index[1]))
            current_length += len(summary_sentences[-1][1].tokens)
        return summary_sentences

    def get_scored_sentences(self):
        return [(s[1], s[2]) for s in self.get_scored()]

    def get_scored_sentences_numbers(self):
        return [(s[0], s[2]) for s in self.get_scored()]

    def get_scored_sentences_numbers(self, sentences_count):
        return sorted(self.scored_sentences.items(), key=operator.itemgetter(1), reverse=True)[:sentences_count]

    def get_summary(self):
        return ' '.join([i[1] for i in sorted([(sentence[0].id, str(sentence[0])) for sentence in self.get_scored_sentences()], reverse=False)]) # change this unicode

    def __unicode__(self):
        return self.get_summary()
        # return u'Original text:\n%s\nNumber of sentences: %s\n\n' % (
            # self.document.text, len(self.document)) + u'\nExtracted text:\n%s\n\nNumber of sentences: %s' % (
            # self.get_summary(), len(self.get_scored_sentences()))


class Singleton:
    """
    A non-thread-safe helper class to ease implementing singletons.
    This should be used as a decorator -- not a metaclass -- to the
    class that should be a singleton.

    The decorated class can define one `__init__` function that
    takes only the `self` argument. Other than that, there are
    no restrictions that apply to the decorated class.

    To get the singleton instance, use the `Instance` method. Trying
    to use `__call__` will result in a `TypeError` being raised.

    Limitations: The decorated class cannot be inherited from.

    """

    def __init__(self, decorated):
        self._decorated = decorated

    def Instance(self):
        """
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.

        """
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `Instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)
