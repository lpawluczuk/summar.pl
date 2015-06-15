#ifndef _CONNSBUF_H_
#define _CONNSBUF_H_

#include "conns.h"
#include "sentence.h"

typedef struct {
	int *paramsNumber;
	int **paramId;
} C_SimpleConns;

typedef struct {
	int *prevNumber;
	int **prevLabels;
	int **paramsNumber;
	int **connsMap;
	int ***paramId;
} C_CompoundConns;

typedef struct {
	C_SimpleConns *simpleConns;
	C_CompoundConns *compoundConns;
	C_CompoundConns *revCompoundConns;
	int yn;
} C_ConnsBuf;

void fillConnsBuf(C_ConnsBuf* connsBuf, C_Conns* conns, C_Sentence* sent, int wid);
void clearConnsBuf(C_ConnsBuf* connsBuf);

C_ConnsBuf* newConnsBuf(int yn, int obstype_num);
void freeConnsBuf(C_ConnsBuf* connsBuffer);

#endif
