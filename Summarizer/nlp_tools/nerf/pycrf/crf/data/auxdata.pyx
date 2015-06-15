# encoding: utf-8

from collections import defaultdict

from libc.stdlib cimport calloc, free

from crf import const

cdef class AuxData:

    def __cinit__(self):
        self.size = 0
        self.dummy_id = const.dummy_id
        self.fnum = NULL

    def __dealloc__(self):
        if self.fnum is not NULL:
            free(self.fnum)

    def _init_fnum(self, data, model):
        self.fnum = <int*>calloc(model.pn, sizeof(int))
        if self.fnum is NULL:
            raise MemoryError
        ignored = 0
        for (sent, labels) in data:
            py = self.dummy_id
            for (singles, pairs), y in zip(sent, labels):
                for x in singles:
                    try:
                        featid = model.feature_id((-1, y, x))
                        self.fnum[featid] += 1
                    except:
                        ignored += 1
                for x in pairs:
                    try:
                        featid = model.feature_id((py, y, x))
                        self.fnum[featid] += 1
                    except:
                        ignored += 1
                py = y
        return ignored

    def __init__(self, data, model):
        self.size = model.pn
        self._init_fnum(data, model)
