from math import log10
from enum import Enum
import re
import math

try:
    from Summarizer.models import Singleton
except ImportError:
    from models import Singleton
try:
    from Summarizer.helpers import read_file_lines
except ImportError:
    from helpers import read_file_lines


class Feature(Enum):
    TfIdf = 1
    Fake = 2
    Header = 3
    SentLocPara = 4
    ParaLocSection = 5
    SentSpecialSection = 6
    SentInHighestPname = 7
    SentInHighestTitle = 8
    SentLength = 9
    SentType = 10
    Centrality = 11
    Verb = 12
    Nouns = 13
    # POSTag = 14
    AvWordLength = 15
    NER = 16
    NERTf = 17
    MetaInfo = 18
    PersNameNE = 19
    OrgNameNE = 20
    PlaceNameNE = 21
    DateNE = 22
    GeogNameNE = 23
    TimeNE = 24
    ParaLength = 25
    Pronouns = 26

class PartOfSpeech(Enum):
    verb = 1
    subst = 2
    ppron12 = 3
    ppron3 = 4
    siebie = 5

    def __str__(self):
        return self.name


class NamedEntityCategory(Enum):
    persName = 1
    orgName = 2
    placeName = 3
    date = 4
    geogName = 5
    time = 6

    def __str__(self):
        return self.name

@Singleton
class FeaturesConfig():
    def __init__(self):
        self.stop_list = None

    def set_stop_list(self, stop_list):
        self.stop_list = [line.strip() for line in read_file_lines(stop_list)]


class AbstractFeature(object):
    """Some description that tells you it's abstract,
    often listing the methods you're expected to supply."""

    def __init__(self):
        self.name = None
        raise NotImplementedError("Should have implemented this")

    def init(self, document):
        raise NotImplementedError("Should have implemented this")

    def process(self, sentence, paragraph, paragraph_number, sentence_number):
        raise NotImplementedError("Should have implemented this")


""" Thematic features """


class TfIdfFeature(AbstractFeature):
    def __init__(self):
        self.name = Feature.TfIdf
        self.stop_list = FeaturesConfig.Instance().stop_list

    def init(self, document):
        self.document = document
        self.doc_length = len(document)

    def process(self, sentence, paragraph, paragraph_number, sentence_number):
        if self.stop_list:
            sent_salience = sum(
                sentence.lemmas.count(token) * (log10(self.doc_length / self.document.tokens_map[token])) for token in
                sentence.lemmas if self.stop_list and token not in self.stop_list)
        else:
            sent_salience = sum(
                sentence.lemmas.count(token) * (log10(self.doc_length / self.document.tokens_map[token])) for token in
                sentence.lemmas)
        return (sent_salience / len(sentence) - 1)


class CentralityFeature(AbstractFeature):
    def __init__(self):
        self.name = Feature.Centrality
        self.stop_list = FeaturesConfig.Instance().stop_list

    def init(self, document):
        self.document = document
        self.doc_length = len(document)

    def process(self, sentence, paragraph, paragraph_number, sentence_number):
        c = 0.0
        for s in self.document.get_sentences():
            if sentence == s:
                continue
            c += self.similarity(sentence, s)
        return 1.0 / (self.doc_length - 1) * c

    def similarity(self, sentence1, sentence2):
        up = 0
        for w in set(sentence1.lemmas + sentence2.lemmas):
            up += (self.tf(w, sentence1) * self.tf(w, sentence2) * self.idf(w))
        down = (self.sentence_sqrt(sentence1) * self.sentence_sqrt(sentence2))
        return up / down

    def tf(self, word, sentence):
        return float(sentence.lemmas.count(word)) / len(sentence)

    def idf(self, word):
        return log10(self.doc_length / self.document.tokens_map[word])

    def sentence_sqrt(self, sentence):
        res = 0
        for word in sentence.lemmas:
            res += math.pow(self.tf(word, sentence) * self.idf(word), 2)
        return math.sqrt(res)


class SentInHighestTitleFeature(AbstractFeature):  # stop words!!!!!!!!!
    """ number of section heading or title term mentions """

    def __init__(self):
        self.name = Feature.SentInHighestTitle
        self.stop_list = FeaturesConfig.Instance().stop_list

    def init(self, document):
        self.heading_tokens = []

    def process(self, sentence, paragraph, paragraph_number, sentence_number):
        if sentence.is_header:
            self.heading_tokens = [sentence.lemmas[i] for i in range(len(sentence.tokens_lower)) if
                                   self.stop_list and sentence.tokens_lower[i] not in self.stop_list]
            return 1.0
        tokens_map = sentence.tokens_lower
        heading_tokens_count = 0
        for h in self.heading_tokens:
            heading_tokens_count += sentence.lemmas.count(h)
        return float(heading_tokens_count) / len(tokens_map)


class SentInHighestPnameFeature(AbstractFeature):
    """ number of mentions of named entities. - counting only words starting with upper case"""

    def __init__(self):
        self.name = Feature.SentInHighestPname

    def init(self, document):
        pass

    def process(self, sentence, paragraph, paragraph_number, sentence_number):
        return float(sum(1 for token in sentence.tokens if token[0].isupper())) / (len(sentence.tokens))


class HeaderFeature(AbstractFeature):
    """ 
        Is header feature:
             0.5 - sentence is header,
             -0.5 - sentence is not header.
    """

    def __init__(self):
        self.name = Feature.Header

    def init(self, document):
        pass

    def process(self, sentence, paragraph, paragraph_number, sentence_number):
        return 0.5 if sentence.is_header else -0.5


""" Location features """


class SentLocParaFeature(AbstractFeature):
    """ 
        Position of sentence in document (first, midle or last third of sentences in paragraph):
            -1 - first 1/3 of sentences,
             -0.5 - second 1/3 of sentences,
             0 - last third 1/3 of sentences.
             0.5 - sentence is header.
    """

    def __init__(self):
        self.name = Feature.SentLocPara

    def init(self, document):
        pass

    def process(self, sentence, paragraph, paragraph_number, sentence_number):
        s_count = float(len(paragraph.sentences))
        sentence_number += 1

        if sentence.is_header:
            return 0.5

        if sentence_number > (2.0 / 3.0 * s_count):
            return 0.0
        elif sentence_number > (1.0 / 3.0 * s_count):
            return -0.5
        return -1.0


class ParaLocSectionFeature(AbstractFeature):
    """ 
        Position of sentence in document (first, midle or last third of paragraphs):
            -1 - first section,
             0 - second section ,
             1 - last third section.
    """

    def __init__(self):
        self.name = Feature.ParaLocSection

    def init(self, document):
        self.p_count = float(len(document.paragraphs))

    def process(self, sentence, paragraph, paragraph_number, sentence_number):
        paragraph_number += 1
        if paragraph_number > (2.0 / 3.0 * self.p_count):
            return 1.0
        elif paragraph_number > (1.0 / 3.0 * self.p_count):
            return 0.0
        return -1.0


class SentSpecialSectionFeature(AbstractFeature):
    """ 
        Position of sentence in document:
            -1 - introduction,
             0 - conclusion,
             1 - other.
    """

    def __init__(self):
        self.name = Feature.SentSpecialSection

    def init(self, document):
        self.introduction = document.get_introduction_paragraph_number()
        self.conclusion = document.get_conclusion_paragraph_number()

    def process(self, sentence, paragraph, paragraph_number, sentence_number):
        if paragraph_number == self.introduction:
            return -1.0
        elif paragraph_number == self.conclusion:
            return 0.0
        return 1.0


class SentLengthFeature(AbstractFeature):
    """ 
        Length of sentence in document:
            -1 - less than 7,
             0 - 7-14,
             1 - more than 14.
    """

    def __init__(self):
        self.name = Feature.SentLength

    def init(self, document):
        pass

    def process(self, sentence, paragraph, paragraph_number, sentence_number):
        if len(sentence) < 7:
            return -1
        if len(sentence) >= 14:
            return 1
        return 0


class SentTypeFeature(AbstractFeature):
    """ 
        Type of sentence in document:
            -1 - ends with ?,
             -0.5 - ends with !,
             0.5 - ends with .,
             1 - other

    """

    def __init__(self):
        self.name = Feature.SentType

    def init(self, document):
        pass

    def process(self, sentence, paragraph, paragraph_number, sentence_number):
        sent_end = sentence.tokens[-1]
        if sent_end == "?":
            return -1
        if sent_end == "!":
            return -0.5
        if sent_end == ".":
            return 0.5
        return 1


""" POS tags features """


class VerbFeature(AbstractFeature):
    def __init__(self):
        self.name = Feature.Verb

    def init(self, document):
        pass

    def process(self, sentence, paragraph, paragraph_number, sentence_number):
        for pos_tag in sentence.pos_tags:
            if str(PartOfSpeech.verb) in pos_tag:
                return 1
        return -1


class NounsFeature(AbstractFeature):
    def __init__(self):
        self.name = Feature.Nouns

    def init(self, document):
        pass

    def process(self, sentence, paragraph, paragraph_number, sentence_number):
        return sum(1.0 for pos_tag in sentence.pos_tags for p in pos_tag if p == str(PartOfSpeech.subst)) / len(sentence)


class AvWordLengthFeature(AbstractFeature):
    def __init__(self):
        self.name = Feature.AvWordLength

    def init(self, document):
        pass

    def process(self, sentence, paragraph, paragraph_number, sentence_number):
        av_length = float(sum(len(token) for token in sentence.tokens)) / len(sentence)
        # av_length = av_length / 5 # ????????

        return av_length


class NERFeature(AbstractFeature):
    def __init__(self):
        self.name = Feature.NER

    def init(self, document):
        pass

    def process(self, sentence, paragraph, paragraph_number, sentence_number):
        av_length = float(len(sentence.named_entities)) / len(sentence)
        return av_length


class NERTfFeature(AbstractFeature):
    def __init__(self):
        self.name = Feature.NERTf

    def init(self, document):
        self.document = document

    def process(self, sentence, paragraph, paragraph_number, sentence_number):
        ne_count = sum(self.document.named_entities_frequency[ne] / self.document.named_entities_count for ne in sentence.named_entities)
        return ne_count


class MetaInfoFeature(AbstractFeature):
    def __init__(self):
        self.name = Feature.MetaInfo

    def init(self, document):
        pass

    def process(self, sentence, paragraph, paragraph_number, sentence_number):
        if re.match("^ROZMOWA:?(\s+NA GOR.CO)?$", sentence.sentence):
            return -1
        if re.match("RYS\..*", sentence.sentence):
            return -1
        if re.match("Rozmawia.a?:?\s+.*", sentence.sentence):
            return -1
        if re.match("(Rozmawia.a?)|(ZDJ.CIA):?\s+.*", sentence.sentence):
            return -1
        if re.match("^((\w{1,2}\.(\,?\s)?)|(((REUTERS)|(pap)|(AP)|(AFP)|(DPA)|(PAD))(\,\s)?)){2,}$", sentence.sentence):
            return -1
        if re.match("^.?Autor((ka)|(zy))?\s+((jest)|(reprezentuj.)|(by.)|(s.)|(wsp..pracuj.)|(pracuj.))", sentence.sentence):
            return -1
        return 1


class ParaLengthFeature(AbstractFeature):
    """ Paragraph length
    """

    def __init__(self):
        self.name = Feature.ParaLength

    def init(self, document):
        pass

    def process(self, sentence, paragraph, paragraph_number, sentence_number):
        length = len(paragraph)
        if length <= 1:
            return -1.0
        if 1 < length <= 5:
            return 0
        return 1


class CategoryNEFeature(AbstractFeature):

    def __init__(self):
        self.name = None
        self.category = None

    def init(self, document):
        pass

    def process(self, sentence, paragraph, paragraph_number, sentence_number):
        if len(sentence.named_entities) == 0:
            return 0
        return sum(1.0 for n in sentence.named_entities if n[1] == self.category) / len(sentence.named_entities)


class FakeFeature(AbstractFeature):
    """ 1 if sentence is in introduction, 2 if in conclusion, 3 if other."""

    def __init__(self):
        self.name = Feature.Fake

    def init(self, document):
        pass

    def process(self, sentence, paragraph, paragraph_number, sentence_number):
        return 1.0


class PersNameNEFeature(CategoryNEFeature):

    def __init__(self):
        self.name = Feature.PersNameNE
        self.category = NamedEntityCategory.persName


class OrgNameNEFeature(CategoryNEFeature):

    def __init__(self):
        self.name = Feature.OrgNameNE
        self.category = NamedEntityCategory.orgName


class PlaceNameNEFeature(CategoryNEFeature):

    def __init__(self):
        self.name = Feature.PlaceNameNE
        self.category = NamedEntityCategory.placeName


class DateNEFeature(CategoryNEFeature):

    def __init__(self):
        self.name = Feature.DateNE
        self.category = NamedEntityCategory.date


class GeogNameNEFeature(CategoryNEFeature):

    def __init__(self):
        self.name = Feature.GeogNameNE
        self.category = NamedEntityCategory.geogName


class TimeNEFeature(CategoryNEFeature):

    def __init__(self):
        self.name = Feature.TimeNE
        self.category = NamedEntityCategory.time

class PronounsFeature(AbstractFeature):

    def __init__(self):
        self.name = Feature.Pronouns

    def init(self, document):
        pass

    def process(self, sentence, paragraph, paragraph_number, sentence_number):
        return sum(1.0 for pos_tag in sentence.pos_tags for p in pos_tag if p == str(PartOfSpeech.ppron12) or p == str(PartOfSpeech.ppron3) or p == str(PartOfSpeech.siebie)) / len(sentence)


FEATURES = {str(Feature.TfIdf): TfIdfFeature(),
            str(Feature.Header): HeaderFeature(),
            str(Feature.SentLocPara): SentLocParaFeature(),
            str(Feature.ParaLocSection): ParaLocSectionFeature(),
            str(Feature.SentSpecialSection): SentSpecialSectionFeature(),
            str(Feature.SentInHighestPname): SentInHighestPnameFeature(),
            str(Feature.SentInHighestTitle): SentInHighestTitleFeature(),
            str(Feature.SentLength): SentLengthFeature(),
            str(Feature.SentType): SentTypeFeature(),
            str(Feature.Centrality): CentralityFeature(),
            str(Feature.Fake): FakeFeature(),
            str(Feature.Verb): VerbFeature(),
            str(Feature.Nouns): NounsFeature(),
            str(Feature.AvWordLength): AvWordLengthFeature(),
            str(Feature.NER): NERFeature(),
            str(Feature.NERTf): NERTfFeature(),
            str(Feature.MetaInfo): MetaInfoFeature(),
            str(Feature.PersNameNE): PersNameNEFeature(),
            str(Feature.OrgNameNE): OrgNameNEFeature(),
            str(Feature.PlaceNameNE): PlaceNameNEFeature(),
            str(Feature.DateNE): DateNEFeature(),
            str(Feature.GeogNameNE): GeogNameNEFeature(),
            str(Feature.TimeNE): TimeNEFeature(),
            str(Feature.ParaLength): ParaLengthFeature(),
            str(Feature.Pronouns) : PronounsFeature()
            }
            # str(Feature.POSTag): POSTagFeature()}


def get_feature(feature_name):
    for f in FEATURES.keys():
        if feature_name.strip() == f:
            return FEATURES[f]
    raise FeatureNotFoundException(feature_name)


class FeatureNotFoundException(Exception):
    """ FeatureNotFoundException to raise when featue listed in features file does not exist in program. """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "Feature not found: " + repr(self.value)
