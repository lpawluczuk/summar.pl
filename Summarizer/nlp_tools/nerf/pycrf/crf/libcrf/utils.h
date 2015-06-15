#ifndef _UTILS_H_
#define _UTILS_H_

#include "connsbuf.h"
#include "sentence.h"

double logZ(C_Sentence* sent, C_Model* model, C_Conns* conns, C_ConnsBuf* connsbuf, double* B);
void tag_sent(C_Sentence* sent, C_Model* model, C_Conns* conns, C_ConnsBuf* connsbuf, int* labels);

#endif
