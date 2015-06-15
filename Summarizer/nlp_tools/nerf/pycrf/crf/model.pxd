# encoding: utf-8

# cdef extern from "libcrf/connsbuf.h":
cdef extern from "connsbuf.h":
    ctypedef struct C_Conns:
        int** conns
        int* csizes
        int xn

cdef class Conns:
    cdef C_Conns conns

# cdef extern from "libcrf/model.h":
cdef extern from "model.h":
    ctypedef struct C_Model:
        int pn
        int* features
        double* values
        int xn
        int yn
        int dummy_id

cdef class Model:
    cdef C_Model model
    cdef object fmap
    cdef Conns conns
