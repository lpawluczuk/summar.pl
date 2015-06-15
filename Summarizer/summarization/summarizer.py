#-*- coding: utf-8 -*-
import features
from model import NeuralNetworkModel, SVMModel, RandomModel, MaximumModel, FannModel
import datetime

# from helpers import normalize

try:
    from Summarizer.helpers import normalize
except ImportError:
    from helpers import normalize

try:
    from Summarizer.models import Singleton, Summary
except ImportError:
    from models import Singleton,Summary
from enum import Enum


class ModelType(Enum):
    Random = 1
    First = 2
    NN = 3
    SVM = 4
    Fann = 5

    def __str__(self):
        return self.name

@Singleton
class Summarizer:
    def __init__(self):
        self.model = NeuralNetworkModel()

    def set_model(self, model_path=None, features_path=None, config=None):
        model_type = config.get_model_type()
        if model_type == str(ModelType.Random):
            self.model = RandomModel()
        elif model_type == str(ModelType.First):
            self.model = MaximumModel()
        elif model_type == str(ModelType.NN):
            self.model = NeuralNetworkModel()
            self.model.set_model(model_path, features_path, config.get_stop_list_path())
        elif model_type == str(ModelType.SVM):
            self.model = SVMModel()
            self.model.set_model(model_path, features_path, config.get_stop_list_path())
        elif model_type == str(ModelType.Fann):
            self.model = FannModel()
            self.model.set_model(model_path, features_path, config.get_stop_list_path())
        else:
            print "Wrong model!"

    def set_features(self, features_path, stop_list):
        self.model.set_model(None, features_path, stop_list)

    def get_features(self):
        return self.model.features

    def create_summary(self, document, length=10):
        summary = Summary(self.score_document(document), length)

        # for s in summary.document.get_sentences():
        #     for i, feature in enumerate(s.scores.keys()):
        #         s.scores[feature] = normalize(s.scores[feature], self.model.normalization_values[i][0], self.model.normalization_values[i][1])

        summary.set_scores({i: self.model.activate(s.scores.values())[0] for i, s in enumerate(document.get_sentences())})
        return summary

    def score_document(self, document):
        [f.init(document) for f in self.get_features()]
            
        for paragraph_number, paragraph in enumerate(document.paragraphs):
            for sentence_number, sentence in enumerate(paragraph.sentences):
                [sentence.update_scores(f.name, f.process(sentence, paragraph, paragraph_number, sentence_number)) for f in self.get_features()]
        document.scored = True
        return document