# -*- coding: utf-8 -*-
import argparse

from postsum import PostSummarizer
from trainer import TrainerWrapper
from evaluation.evaluator import EvaluatorWrapper
from args import check_args_dict
from summarize_wrapper import SummarizationWrapper
from config import read_config

__author__ = "Łukasz Pawluczuk"
__copyright__ = "Copyright (C) 2014 Łukasz Pawluczuk"
__license__ = "Public Domain"
__version__ = "0.1"

""" Main module of program. Contains command line interface. """

MODES = ['sum', 'train', 'eval']


def check_args(args):
    if args.mode == MODES[0]:
        check_args_dict({"model": args.model, "features": args.features})
    elif args.mode == MODES[1]:
        check_args_dict({"train_dir": args.train_dir, "features": args.features})
    elif args.mode == MODES[2]:
        check_args_dict({"test_dir": args.test_dir, "model": args.model, "features": args.features})


def main(mode, file_path, model, train_dir, test_dir, features, dir_path, config):
    conf = read_config(config)

    if mode == MODES[0]:
        if file_path:
            SummarizationWrapper(model, features, conf).summarize_from_file(file_path,
                                                                            conf.get_length().value)
        elif dir_path:
            SummarizationWrapper(model, features, conf).summarize_directory(dir_path)
            # SummarizationWrapper(model, features, conf).summarize_directory_using_score_dump(dir_path)
    elif mode == MODES[1]:
        TrainerWrapper(features, conf).train(train_dir, test_dir, conf.get_dataset_path(), conf.get_dump_dataset())

        if test_dir:
            EvaluatorWrapper("./model.xml", features, conf).evaluate(test_dir)
    elif mode == MODES[2]:
        EvaluatorWrapper(model, features, conf).evaluate(test_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--mode", choices=MODES,
                        help="program mode", required=True)
    parser.add_argument("-f", "--file", help="input file")
    parser.add_argument("-a", "--dir", help="input dir")
    parser.add_argument("-m", "--model", help="model file")
    parser.add_argument("-g", "--features", help="model features file")
    parser.add_argument("-t", "--train_dir", help="train dir")
    parser.add_argument("-y", "--test_dir", help="test dir")
    parser.add_argument("-z", "--config", help="config file")

    # add evaluate method
    args = parser.parse_args()
    main(args.mode, args.file, args.model, args.train_dir, args.test_dir,
         args.features, args.dir, args.config)
