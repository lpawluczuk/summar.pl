# encoding: utf-8

cdef class AuxData:
    cdef int size
    cdef int dummy_id
    cdef int* fnum  # numbers of feautres in dataset
