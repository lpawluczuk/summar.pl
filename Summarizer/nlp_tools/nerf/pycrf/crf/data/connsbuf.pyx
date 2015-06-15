# encoding: utf-8

cdef class ConnsBuf:

    def __cinit__(self):
        self.cbuf = NULL

    def __init__(self, yn, obstype_num):
        self.cbuf = newConnsBuf(yn, obstype_num)
        if self.cbuf is NULL:
            raise MemoryError

    def __dealloc__(self):
        if self.cbuf is not NULL:
            freeConnsBuf(self.cbuf)
