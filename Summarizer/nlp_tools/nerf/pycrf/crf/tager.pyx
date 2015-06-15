# encoding: utf-8

from libc.stdlib cimport malloc, free

from crf.model cimport Model, Conns
from crf.data.connsbuf cimport ConnsBuf
from crf.data.auxdata cimport AuxData
from crf.data.sentence cimport Sentence

cdef extern from "sentence.h":
    ctypedef struct C_Sentence:
        pass

cdef extern from "conns.h":
    ctypedef struct C_Model:
        pass

cdef extern from "conns.h":
    ctypedef struct C_Conns:
        pass

cdef extern from "connsbuf.h":
    ctypedef struct C_ConnsBuf:
        pass

cdef extern from "utils.h":
    void tag_sent(C_Sentence* sent, C_Model* model, C_Conns* conns,
            C_ConnsBuf* connsBuf, int* labels) nogil

def tag(Sentence sent, Model model, ConnsBuf connsbuf):
    cdef int* labels = <int*>malloc(len(sent) * sizeof(int))
    if labels is NULL:
        raise MemoryError
    with nogil:
        tag_sent(&sent.sent, &model.model, &model.conns.conns,
                connsbuf.cbuf, labels)
    value = [labels[i] for i in range(len(sent))]
    free(labels)
    return value

class Tager:

    def __init__(self, model, obtypes):
        self.model = model
        self.connsbuf = ConnsBuf(model.yn, obtypes)

    def tag(self, Sentence sent):
        return tag(sent, self.model, self.connsbuf)
