# encoding: utf-8

cdef extern from "connsbuf.h":
    ctypedef struct C_ConnsBuf:
        pass
    C_ConnsBuf* newConnsBuf(int yn, int obstype_num)
    void freeConnsBuf(C_ConnsBuf* connsBuf)

cdef class ConnsBuf:
    cdef C_ConnsBuf* cbuf
