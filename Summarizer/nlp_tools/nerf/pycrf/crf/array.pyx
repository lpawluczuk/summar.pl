# encoding: utf-8

from libc.stdlib cimport malloc, free

cdef class DArray:
    def __cinit__(self):
        self.size = 0
        self.array = NULL
    def __init__(self, size):
        self.size = size
        self.array = <double*>malloc(size * sizeof(double))
    def __dealloc__(self):
        if self.array is not NULL:
            free(self.array)

