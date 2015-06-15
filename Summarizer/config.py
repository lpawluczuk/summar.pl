import ConfigParser
from enum import Enum
from polish_summaries_corpus_reader import SummaryLength
from trainer import NeuralNetworkTrainer, SVMTrainer
from dataset_processor import WideDatasetProcessor, FractionDatasetProcessor, RatioDatasetProcessor, \
    CSVWideDatasetProcessor, DumpModelDatasetProcessor, CSVWideDumpedDatasetProcessor


class Sections(Enum):
    General = 0
    Train = 1
    Eval = 2

    def __str__(self):
        return self.name


def create_config(config_path):
    cfgfile = open(config_path, 'w')

    config = ConfigParser.ConfigParser(allow_no_value=True)

    [config.add_section(str(s)) for s in Sections]
    config.set(str(Sections.General), 'StopList', "./stop-list.txt")
    config.set(str(Sections.General), '; available options are: NN, SVM, Random, First')
    config.set(str(Sections.General), 'ModelType', "NN")
    config.set(str(Sections.General), 'length', "LONG")
    config.set(str(Sections.Train), '; available options are: NN, SVM')
    config.set(str(Sections.Train), 'TrainMethod', "NN")
    config.set(str(Sections.Train), '; available options are: Wide, Ratio, Fraction')
    config.set(str(Sections.Train), 'DirProcessor', "Wide")
    config.set(str(Sections.Train), 'DirProcessorOption', "0.8")
    config.set(str(Sections.Train), 'Dataset', "None")
    config.set(str(Sections.Train), 'DumpDataset', False)
    config.set(str(Sections.Eval), '; available options are: Strict, Corpus, Wide')
    config.set(str(Sections.Eval), 'EvalMethod', "Strict")
    config.write(cfgfile)
    cfgfile.close()


def create_config_section_map(config, section):
    dict1 = {}
    options = config.options(section)
    for option in options:
        try:
            dict1[option] = config.get(section, option)
            if dict1[option] == -1:
                print "skip: %s" % option
        except:
            print "exception on %s!" % option
            dict1[option] = None
    return dict1


def read_config(config_path):
    config = ConfigParser.ConfigParser()
    config.read(config_path)

    configuration = {str(section): create_config_section_map(config, str(section)) for section in Sections}
    configuration[str(Sections.Train)]["dumpdataset"] = config.getboolean(str(Sections.Train), "dumpdataset")
    return Configuration(configuration)


class Configuration():
    def __init__(self, configuration):
        self.configuration = configuration

    def get_option(self, section, option):
        return self.configuration[section][option]

    def get_dataset_path(self):
        return self.get_option(str(Sections.Train), "dataset")

    def get_stop_list_path(self):
        return self.get_option(str(Sections.General), "stoplist")

    def get_model_type(self):
        return self.get_option(str(Sections.General), "modeltype")

    def get_length(self):
        return SummaryLength[self.get_option(str(Sections.General), "length")]

    def get_train_method(self):
        return NeuralNetworkTrainer().train if self.get_option(str(Sections.Train),
                                                               "trainmethod") == "NN" else SVMTrainer().train()

    def get_dir_processor(self):
        dir = self.get_option(str(Sections.Train), "dirprocessor")

        if dir == "wide":
            return WideDatasetProcessor(self.get_length()).process_dir
        elif dir == "fraction":
            return FractionDatasetProcessor(self.get_length(), self.get_dir_processor_option()).process_dir
        elif dir == "ratio":
            return RatioDatasetProcessor(self.get_length(), self.get_dir_processor_option()).process_dir
        elif dir == "csvwide":
            return CSVWideDatasetProcessor(self.get_length()).process_dir
        elif dir == "dump":
            return DumpModelDatasetProcessor(self.get_length()).process_dir
        elif dir == "csvdump":
            return CSVWideDumpedDatasetProcessor(self.get_length(), True).process_dir
        return None

    def get_dir_processor_option(self):
        return self.get_option(str(Sections.Train), "dirprocessoroption")

    def get_dump_dataset(self):
        return self.get_option(str(Sections.Train), "dumpdataset")

    def get_eval_method(self):
        return self.get_option(str(Sections.Eval), "evalmethod")


if __name__ == "__main__":
    create_config("config.ini")