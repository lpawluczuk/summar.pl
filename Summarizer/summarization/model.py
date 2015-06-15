import features
import pickle
try:
    from Summarizer.helpers import read_file_lines, load_from_file
except ImportError:
    from helpers import read_file_lines, load_from_file
import random
from fann2 import libfann

DEFAULT_FEATURES = [features.TfIdfFeature()]


class AbstractModel( object ):
    """Some description that tells you it's abstract,
    often listing the methods you're expected to supply."""
    def __init__(self):
        self.features = DEFAULT_FEATURES
        self.features_path = None
        self.model = None
        self.normalization_values = None

    def set_model(self, model_path, features_path, stop_list):
        self.set_features(features_path, stop_list)
        if model_path:
            self.model = load_from_file(model_path)
            # self.normalization_values = load_from_file(model_path.replace("model.xml", "meta_model.xml"))
            # self.normalization_values = load_from_file(model_path[:model_path.rfind("/")+1] + "meta_model.xml")

    def set_features(self, features_path, stop_list):
        if self.features_path != features_path:
            self.features = self.read_features_from_file(features_path) if features_path else DEFAULT_FEATURES
            self.features_path = features_path
        if stop_list:
            features.FeaturesConfig.Instance().set_stop_list(stop_list)

    def read_features_from_file(self, features_path):
        return [features.get_feature(f) for f in read_file_lines(features_path) if f and not f.startswith("#")]

    def activate(self, input_list):
        raise NotImplementedError("Should have implemented this")


class NeuralNetworkModel(AbstractModel):
    def activate(self, input_list):
        return self.model.activate(input_list)


class SVMModel(AbstractModel):
    def activate(self, input_list):
        return self.model.predict(input_list)


class RandomModel(AbstractModel):
    def activate(self, input_list):
        return [random.random()]


class MaximumModel(AbstractModel):
    def activate(self, input_list):
        return [1.0]


class FannModel(AbstractModel):
    def activate(self, input_list):
        # print self.model.run(input_list)
        return self.model.run(input_list)

    def set_model(self, model_path, features_path, stop_list):
        self.set_features(features_path, stop_list)
        if model_path:
            self.model = libfann.neural_net()
            self.model.create_from_file(model_path)
            self.normalization_values = [] #load_from_file(model_path.replace("model.xml", "meta_model.xml"))
            # self.normalization_values = load_from_file(model_path[:model_path.rfind("/")+1] + "meta_model.xml")