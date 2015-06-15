# encoding: utf-8

cdef extern from "../libcrf/sentence.h":
    ctypedef struct C_Sentence:
        int length
        int** singles   # single observations
        int* snum       # number of singles obs.
        int** pairs     # pair observations
        int* pnum       # number of pair obs.

cdef class Sentence:
    cdef C_Sentence sent
