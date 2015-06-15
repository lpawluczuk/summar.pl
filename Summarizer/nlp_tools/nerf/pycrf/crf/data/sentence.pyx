# encoding: utf-8

from libc.stdlib cimport malloc, free

cdef class Sentence:

    def __cinit__(self):
        self.sent.length = 0
        self.sent.singles = NULL
        self.sent.snum = NULL 
        self.sent.pairs = NULL
        self.sent.pnum = NULL 
        self.sent.snum = NULL 

    def _alloc(self, size, snum, pnum):
        self.sent.singles = <int**>malloc(size * sizeof(int*))
        if self.sent.singles is NULL:
            raise MemoryError
        self.sent.pairs = <int**>malloc(size * sizeof(int*))
        if self.sent.pairs is NULL:
            raise MemoryError
        self.sent.snum = <int*>malloc(size * sizeof(int))
        if self.sent.snum is NULL:
            raise MemoryError
        self.sent.pnum = <int*>malloc(size * sizeof(int))
        if self.sent.pnum is NULL:
            raise MemoryError
        for i in range(size):
            self.sent.singles[i] = NULL
            self.sent.pairs[i] = NULL
        for i in range(size):
            self.sent.singles[i] = <int*>malloc(snum[i] * sizeof(int))
            if self.sent.singles[i] is NULL:
                raise MemoryError
            self.sent.pairs[i] = <int*>malloc(pnum[i] * sizeof(int))
            if self.sent.pairs[i] is NULL:
                raise MemoryError

    def _dealloc(self):
        if self.sent.snum is not NULL:
            free(self.sent.snum)
        if self.sent.pnum is not NULL:
            free(self.sent.pnum)
        if self.sent.singles is not NULL:
            for i in range(self.sent.length):
                if self.sent.singles[i] is not NULL:
                    free(self.sent.singles[i])
            free(self.sent.singles)
        if self.sent.pairs is not NULL:
            for i in range(self.sent.length):
                if self.sent.pairs[i] is not NULL:
                    free(self.sent.pairs[i])
            free(self.sent.pairs)

    def __dealloc__(self):
        self._dealloc()

    def __init__(self, sent):
        self._dealloc()
        self.sent.length = len(sent)
        # self._alloc(len(sent), map(len, sent))
        self._alloc(len(sent),
                [len(ss) for (ss, _) in sent],
                [len(ps) for (_, ps) in sent])
        for i, (singles, pairs) in enumerate(sent):
            self.sent.snum[i] = len(singles)
            self.sent.pnum[i] = len(pairs)
            for j, x in enumerate(singles):
                self.sent.singles[i][j] = x
            for j, x in enumerate(pairs):
                self.sent.pairs[i][j] = x

    def __getitem__(self, i):
        if i < 0 or i >= self.sent.length:
            raise IndexError
        return ([self.sent.singles[i][j] for j in range(self.sent.snum[i])],
                [self.sent.pairs[i][j] for j in range(self.sent.pnum[i])])

    def __len__(self):
        return self.sent.length
