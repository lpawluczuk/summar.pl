# encoding: utf-8

cdef class DArray:
    cdef int size
    cdef double* array
