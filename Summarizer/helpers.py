import codecs
import pickle
import os

def read_file(file_path):
    """ Method reads file into string. """
    f = codecs.open(file_path)
    data = ''
    for line in f:
        data += line + '\n'
    return data


def read_file_lines(file_path):
    """ Method reads file into list of lines. """
    return [line for line in codecs.open(file_path, encoding='utf-8')]


def load_from_file(path):
    fileObject = open(path, 'r')
    dataset = pickle.load(fileObject)
    fileObject.close()
    return dataset


def save_to_file(data, path):
    fileObject = open(path, mode='w')
    pickle.dump(data, fileObject)
    fileObject.close()


def normalize(value, min, max):
    if max == 0 and min == 0:
        return 0
    return -1.0 + ((value - min)*2.0) / (max-min)


def mkdir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
