# encoding: utf-8

from libc.stdlib cimport malloc, free

from crf.array cimport DArray
from crf.model cimport Model
from crf.data.connsbuf cimport ConnsBuf
from crf.data.auxdata cimport AuxData
from crf.data.sentence cimport Sentence

cdef extern from "sentence.h":
    ctypedef struct C_Sentence:
        pass

cdef extern from "model.h":
    ctypedef struct C_Model:
        int pn
        int* features
        double* values
        int xn
        int yn
        int dummy_id

cdef extern from "conns.h":
    ctypedef struct C_Conns:
        pass

cdef extern from "connsbuf.h":
    ctypedef struct C_ConnsBuf:
        pass

cdef extern from "utils.h":
    double logZ(C_Sentence* sent, C_Model* model, C_Conns* conns,
            C_ConnsBuf* connsbuf, double* B) nogil

def count_z_stats(batch, Model model, ConnsBuf connsbuf):
    cdef double logz
    cdef Sentence sent
    z_stats = []
    for sent, _ in batch:
        with nogil:
            logz = logZ(&sent.sent, &model.model, &model.conns.conns,
                    connsbuf.cbuf, NULL)
        z_stats.append(logz)
    return z_stats

def add_expected_numbers(Sentence sent, DArray numbers_wrapper, Model model,
        ConnsBuf connsbuf):
    """Add expected numbers of features in the sentence."""
    cdef int k
    cdef double* numbers = numbers_wrapper.array
    cdef C_Model* _model = &model.model
    cdef double logz
    with nogil:
        logz = logZ(&sent.sent, _model, &model.conns.conns,
                connsbuf.cbuf, numbers)
    return logz

def expected_numbers(batch, DArray numbers_wrapper, Model model,
        ConnsBuf connsbuf):
    """Count expected numbers of features in the batch of sentences."""
    cdef int k
    cdef double* numbers = numbers_wrapper.array
    cdef C_Model* _model = &model.model
    with nogil:
        for k from 0 <= k < _model.pn:
            numbers[k] = 0.0
    cdef Sentence sent
    cdef double logz
    z_stats = []
    for sent, _ in batch:
        with nogil:
            logz = logZ(&sent.sent, _model, &model.conns.conns,
                    connsbuf.cbuf, numbers)
        z_stats.append(logz)
    return z_stats

def count_gradient(batch, DArray gradient_wrapper, Model model, 
        AuxData auxdata, ConnsBuf connsbuf, double i_var2, double coef):
    """
    :param coef:
        Shoudl be equall to |batch size| / |data size|.
    """
    cdef int fn, i
    cdef double val
    expected_numbers(batch, gradient_wrapper, model, auxdata, connsbuf)
    cdef double* gradient = gradient_wrapper.array
    cdef C_Model* _model = &model.model
    # ANOTHER VERSION: auxdata = AuxData(batch, model)
    with nogil:
        for i from 0 <= i < _model.pn:
            val = _model.values[i]
            fn = auxdata.fnum[i]
            # gradient[i] = gradient[i] - fn + val*i_var2*coef
            gradient[i] = gradient[i] - (fn + val*i_var2)*coef

#def count_gradient(batch, GradientWrapper gradient_wrapper, Model model,
#        AuxData auxdata, ConnsBuf connsbuf, double i_var2,
#        double coef, count_cll=True, verbose=False):
#    """
#    :param coef:
#        Shoudl be equall to |batch size| / |data size|.
#    """
#    cdef int k
#    cdef double* gradient = gradient_wrapper.gradient
#    cdef C_Model* _model = &model.model
#
#    with nogil:
#        for k from 0 <= k < _model.pn:
#            gradient[k] = 0.0
#        
#    # OTHER VERSION:
#    # auxdata = AuxData(batch, model)
#
#    cdef Sentence sent
#    cdef double logz
#    z_stats = []
#    for sent, _ in batch:
#        with nogil:
#            logz = logZ(&sent.sent, _model, &model.conns.conns,
#                    connsbuf.cbuf, gradient)
#        z_stats.append(logz)
#
#    cdef int fn
#    cdef double val
#    with nogil:
#        for i from 0 <= i < _model.pn:
#            val = _model.values[i]
#            fn = auxdata.fnum[i]
#            # gradient[i] = gradient[i] - fn + val*i_var2*coef
#            gradient[i] = gradient[i] - (fn + val*i_var2)*coef
#
#    cllval = 0.0
#    if count_cll:
#        cllval = model.cll(batch, z_stats, coef, i_var2)
#        if verbose:
#            print "Conditional Log Likelihood:", cllval
#    return cllval
