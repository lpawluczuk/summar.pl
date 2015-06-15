#-*- coding: utf-8 -*-
import argparse
import os
import numpy


def get_summaries_path_list(corpus_path):
    summaries_path = os.path.join(corpus_path, "summaries_extractive")
    return [(s, os.path.join(summaries_path, s)) for s in ["A", "B", "C", "D", "E"]]

def get_testset_indexes(text_files_len, testset_size):
    a = numpy.arange(text_files_len)
    numpy.random.shuffle(a)
    return a[:int(float(testset_size)/100*text_files_len)]

def create_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def create_test_train_dirs(output_dir):
    train_dir_path = os.path.join(output_dir, "trainset")
    test_dir_path = os.path.join(output_dir, "testset")
    create_dir(train_dir_path)
    create_dir(test_dir_path)
    return train_dir_path, test_dir_path

def create_text_file_dir(dir_path, texts_path, text_file, summaries_path_list):
    file_dir = os.path.join(dir_path, text_file)
    create_dir(file_dir)
    # os.symlink(os.path.join(texts_path, text_file), os.path.join(file_dir, text_file))
    for s in summaries_path_list:
        os.symlink(os.path.join(s[1], text_file), os.path.join(file_dir, s[0] + "_" + text_file))

def main(corpus_path, testset_size, output_dir):
    train_dir_path, test_dir_path = create_test_train_dirs(output_dir)
    texts_path = os.path.join(corpus_path, "original_texts")
    summaries_path_list = get_summaries_path_list(corpus_path)
    text_files = [ f for f in os.listdir(texts_path)]

    testset_indexes = get_testset_indexes(len(text_files), testset_size)

    for i in xrange(len(text_files)):
        create_text_file_dir(test_dir_path if i in testset_indexes else train_dir_path, texts_path, text_files[i], summaries_path_list)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--corpus", help="absolute path to corpus", required=True)
    parser.add_argument("-t", "--testset", help="testset size", default=20)    
    parser.add_argument("-o", "--output", help="absolute  path to output directory")    
    args = parser.parse_args()

    main(args.corpus, args.testset, args.output)