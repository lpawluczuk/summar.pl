# -*- coding: utf-8 -*-

from config import read_config
from trainer import TrainerWrapper
import os
import argparse
from dataset_processor import CSVRatioDumpedDatasetProcessor, SentencesDumpDatasetProcessor, SummariesDumpDatasetProcessor, RatioSummariesDumpDatasetProcessor
from polish_summaries_corpus_reader import SummaryLength

class ToFileTrainerWrapper(TrainerWrapper):

    def train(self, train_dir, test_dir, dataset_path=None, dump_dataset=True):
        for root, dirs, files in os.walk(train_dir, topdown=False):
            # processor = CSVRatioDumpedDatasetProcessor(SummaryLength.LONG, True)
            # processor.mkdir()
            # processor.process_dir(self.summarizer, root, files)
            # self.process_dir(self.summarizer, root, files)
            # SentencesDumpDatasetProcessor(SummaryLength.LONG, True).process_dir(self.summarizer, root, files)
            # break  # remove this !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

            processor = RatioSummariesDumpDatasetProcessor(SummaryLength.LONG)
            processor.mkdir()
            processor.process_dir(self.summarizer, root, files)

        ### TEMP
        # save_dataset_as_csv(dataset)


def main(features, config, train_dir):
    conf = read_config(config)
    ToFileTrainerWrapper(features, conf).train(train_dir, None, conf.get_dataset_path(), conf.get_dump_dataset())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--features", help="model features file")
    parser.add_argument("-t", "--train_dir", help="train dir")
    parser.add_argument("-z", "--config", help="config file")
    args = parser.parse_args()
    main(args.features, args.config, args.train_dir)

