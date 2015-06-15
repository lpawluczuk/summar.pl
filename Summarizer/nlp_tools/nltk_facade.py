#-*- coding: utf-8 -*-
import nltk.data
from nltk.tokenize import word_tokenize
import paths

def segment(input):
    tokenizer = nltk.data.load(paths.NLTK_DATA)
    # print [line.decode("UTF-8").strip() for line in tokenizer.tokenize(input)]
    tokenized = tokenizer.tokenize(input)
    segments = []

    for t in tokenized:
        tmp = t
        while "\n" in tmp:
            s = tmp[:tmp.index("\n")+1]
            if s.strip():
                segments.append(s)
            tmp = tmp[tmp.index("\n")+1:]
        if tmp:
            segments.append(tmp)

    return segments
    # return [line.decode("UTF-8").strip() for line in tokenizer.tokenize(input)]

def tokenize(input):
    return word_tokenize(input)
    # return [line.decode("UTF-8").strip() for line in word_tokenize(input)]