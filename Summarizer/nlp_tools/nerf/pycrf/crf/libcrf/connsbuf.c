#include <stdlib.h>
#include <assert.h>

#include "connsbuf.h"

#ifndef NULL
#define NULL (void *)0
#endif

void addSimpleC(C_SimpleConns *simpleConns, int y, int par_id)
{
	int num = simpleConns->paramsNumber[y];
	simpleConns->paramId[y][num] = par_id;
	++simpleConns->paramsNumber[y];
}

void addCompoundC(C_CompoundConns *compoundConns, int py, int y, int par_id)
{
	int i = compoundConns->connsMap[y][py] - 1;
	if(i == -1) {
		i = compoundConns->prevNumber[y];
		compoundConns->prevLabels[y][i] = py;
		compoundConns->paramsNumber[y][i] = 0;

		++compoundConns->prevNumber[y];
		compoundConns->connsMap[y][py] = i + 1;
	}

	int num = compoundConns->paramsNumber[y][i];
	compoundConns->paramId[y][i][num] = par_id;
	++compoundConns->paramsNumber[y][i];
}

/*void addC(int *conn, int cn, C_ConnsBuf *connsBuf)
{
	C_SimpleConns *simpleConns = connsBuf->simpleConns;
	C_CompoundConns *compoundConns = connsBuf->compoundConns;
	C_CompoundConns *revCompoundConns = connsBuf->revCompoundConns;

	int k;
        for (k = 0; k < 3 * cn; k += 3) {
		int y1 = conn[k];
		int y2 = conn[k + 1];
		int par_id = conn[k + 2];

		if(y1 == -1)
			addSimpleC(simpleConns, y2, par_id);
		else {
			addCompoundC(compoundConns, y1, y2, par_id);
			addCompoundC(revCompoundConns, y2, y1, par_id);
		}
	}
}*/

void fillSimpleConns(int *conn, int cn, C_ConnsBuf *connsBuf)
{
	C_SimpleConns *simpleConns = connsBuf->simpleConns;

	int k;
        for (k = 0; k < 3 * cn; k += 3) {
		int y1 = conn[k];
		int y2 = conn[k + 1];
		int par_id = conn[k + 2];	// parameter/feature id

		assert(y1 == -1);
		addSimpleC(simpleConns, y2, par_id);
	}
}

void fillCompoundConns(int *conn, int cn, C_ConnsBuf *connsBuf)
{
	C_CompoundConns *compoundConns = connsBuf->compoundConns;
	C_CompoundConns *revCompoundConns = connsBuf->revCompoundConns;

	int k;
        for (k = 0; k < 3 * cn; k += 3) {
		int y1 = conn[k];
		int y2 = conn[k + 1];
		int par_id = conn[k + 2];

		assert(y1 != -1);
		addCompoundC(compoundConns, y1, y2, par_id);
		addCompoundC(revCompoundConns, y2, y1, par_id);
	}
}

void fillConnsBuf(C_ConnsBuf* connsBuf, C_Conns* conns, C_Sentence* sent, int wid)
{
	int k;
	for(k = 0 ; k < sent->snum[wid] ; ++k) {
		int x = sent->singles[wid][k]; 
		if(x < conns->xn)
			// addC(conns->conns[x], conns->csizes[x], connsBuf);
			fillSimpleConns(conns->conns[x], conns->csizes[x], connsBuf);
	}

	for(k = 0 ; k < sent->pnum[wid] ; ++k) {
		int x = sent->pairs[wid][k]; 
		if(x < conns->xn)
			// addC(conns->conns[x], conns->csizes[x], connsBuf);
			fillCompoundConns(conns->conns[x], conns->csizes[x], connsBuf);
	}
}

/*void fillConnsBuf(C_ConnsBuf* connsBuf, C_Conns* conns, int *word, int wn)
{
	int k;
	for(k = 0; k < wn; ++k) {
		int x = word[k]; 
		if(x < conns->xn)
			addC(conns->conns[x], conns->csizes[x], connsBuf);
	}
}*/

//obstype_num - liczba typow obserwacji
C_SimpleConns* initSimpleConns(int yn, int obstype_num)
{
	C_SimpleConns *simpleConns = (C_SimpleConns*)malloc(sizeof(C_SimpleConns));
	if(simpleConns == NULL)
		return NULL;

	//Musi byc wyzerowane !
	simpleConns->paramsNumber = (int*)calloc(yn, sizeof(int));
	if(simpleConns->paramsNumber == NULL)
		return NULL;

	simpleConns->paramId = (int**)malloc(yn * sizeof(int*));
	if(simpleConns->paramId == NULL)
		return NULL;

	int i;
	for(i = 0 ; i < yn ; ++i) {
		simpleConns->paramId[i] = malloc(obstype_num * sizeof(int));
		if(simpleConns->paramId[i] == NULL)
			return NULL;
	}
	
	return simpleConns;
}

C_CompoundConns* initCompoundConns(int yn, int obstype_num)
{
	C_CompoundConns *compoundConns = (C_CompoundConns*)malloc(sizeof(C_CompoundConns));
	if(compoundConns == NULL)
		return NULL;

	compoundConns->prevNumber = (int*)calloc(yn, sizeof(int));
	if(compoundConns->prevNumber == NULL)
		return NULL;

	compoundConns->prevLabels = (int**)malloc(yn * sizeof(int*));
	if(compoundConns->prevLabels == NULL)
		return NULL;

	compoundConns->paramsNumber = (int**)malloc(yn * sizeof(int*));
	if(compoundConns->paramsNumber == NULL)
		return NULL;

	compoundConns->connsMap = (int**)malloc(yn * sizeof(int*));
	if(compoundConns->connsMap == NULL)
		return NULL;

	int i, j;
	for(i = 0 ; i < yn ; ++i) {
		compoundConns->prevLabels[i] = malloc(yn * sizeof(int));
		if(compoundConns->prevLabels[i] == NULL)
			return NULL;
		compoundConns->paramsNumber[i] = malloc(yn * sizeof(int));
		if(compoundConns->paramsNumber[i] == NULL)
			return NULL;
		//connsMap musi byc wyzerowana !
		compoundConns->connsMap[i] = calloc(yn, sizeof(int));
		if(compoundConns->connsMap[i] == NULL)
			return NULL;
	}
	
	compoundConns->paramId = malloc(yn * sizeof(int**));
	if(compoundConns->paramId == NULL)
		return NULL;

	for(i = 0 ; i < yn ; ++i) {
		compoundConns->paramId[i] = malloc(yn * sizeof(int*));
		if(compoundConns->paramId[i] == NULL)
			return NULL;

		for(j = 0 ; j < yn ; ++j) {
			compoundConns->paramId[i][j] = malloc(obstype_num * sizeof(int));
			if(compoundConns->paramId[i][j] == NULL)
				return NULL;
		}
	}
	
	return compoundConns;
}


C_ConnsBuf *newConnsBuf(int yn, int obstype_num)
{
	C_ConnsBuf *connsBuffer = (C_ConnsBuf *)malloc(sizeof(C_ConnsBuf));
	if(connsBuffer == NULL)
		return NULL;

	connsBuffer->yn = yn;

	connsBuffer->simpleConns = initSimpleConns(yn, obstype_num);
	if(connsBuffer->simpleConns == NULL)
		return NULL;

	connsBuffer->compoundConns = initCompoundConns(yn, obstype_num);
	if(connsBuffer->compoundConns == NULL)
		return NULL;

	connsBuffer->revCompoundConns = initCompoundConns(yn, obstype_num);
	if(connsBuffer->revCompoundConns == NULL)
		return NULL;

	return connsBuffer;
}

void freeSimpleConns(C_SimpleConns *simpleConns, int yn)
{
	free(simpleConns->paramsNumber);

	int i;
	for(i = 0 ; i < yn ; ++i)
		free(simpleConns->paramId[i]);
	free(simpleConns->paramId);

	free(simpleConns);
}

void freeCompoundConns(C_CompoundConns *compoundConns, int yn)
{
	free(compoundConns->prevNumber);

	int i, j;
	for(i = 0 ; i < yn ; ++i) {
		free(compoundConns->prevLabels[i]);
		free(compoundConns->paramsNumber[i]);
		free(compoundConns->connsMap[i]);
	}
	free(compoundConns->prevLabels);
	free(compoundConns->paramsNumber);
	free(compoundConns->connsMap);

	for(i = 0 ; i < yn ; ++i) {
		for(j = 0 ; j < yn ; ++j)
			free(compoundConns->paramId[i][j]);
		free(compoundConns->paramId[i]);
	}
	free(compoundConns->paramId);

	free(compoundConns);
}

void freeConnsBuf(C_ConnsBuf* connsBuffer)
{
	int yn = connsBuffer->yn;
	freeSimpleConns(connsBuffer->simpleConns, yn);
	freeCompoundConns(connsBuffer->compoundConns, yn);
	freeCompoundConns(connsBuffer->revCompoundConns, yn);
	free(connsBuffer);
}

void clearSimpleConns(C_SimpleConns* simpleConns, int yn)
{
	int i;
	for(i = 0 ; i < yn ; ++i)
		simpleConns->paramsNumber[i] = 0;
}

void clearCompoundConns(C_CompoundConns* compoundConns, int yn)
{
	int y, k;
	for(y = 0 ; y < yn ; ++y) {
		int prevNum = compoundConns->prevNumber[y];

		for(k = 0 ; k < prevNum ; ++k) {
			int py = compoundConns->prevLabels[y][k];
			compoundConns->connsMap[y][py] = 0;
		}

		compoundConns->prevNumber[y] = 0;
	}
}

void clearConnsBuf(C_ConnsBuf *connsBuf)
{
	int yn = connsBuf->yn;
	clearSimpleConns(connsBuf->simpleConns, yn);
	clearCompoundConns(connsBuf->compoundConns, yn);
	clearCompoundConns(connsBuf->revCompoundConns, yn);
}
