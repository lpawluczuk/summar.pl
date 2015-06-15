#include <math.h>
#include <stdio.h>
// #include <stdlib.h>

#undef NDEBUG
#include <assert.h>

#include "model.h"
#include "sentence.h"
#include "connsbuf.h"
#include "real.h"
#include "qsort.h"

//TODO: double -> real !
//sort from highest to lowest values
int compareDownReal(void *arg, const void *v1, const void *v2)
{
	double *prevCol = (double *)arg;
	int e1 = *(const int *)v1;
	int e2 = *(const int *)v2;
	double a = prevCol[e1];
	double b = prevCol[e2];
	if(a > b)
		return -1;
	else if(b > a)
		return 1;
	return 0;
}

int compareUpReal(void *arg, const void *v1, const void *v2)
{
	double *prevCol = (double *)arg;
	int e1 = *(const int *)v1;
	int e2 = *(const int *)v2;
	double a = prevCol[e1];
	double b = prevCol[e2];
	if(a < b)
		return -1;
	else if(b < a)
		return 1;
	return 0;
}

void sortUpReal(int *order, double *val, int len) {
	// prevCol = val;
	_quicksort((void*)order, len, sizeof(int), compareUpReal, val);
}

// int *intValue;
int compareUpInt(void *arg, const void *v1, const void *v2)
{
	int *intValue = (int *)arg;
	int e1 = *(const int *)v1;
	int e2 = *(const int *)v2;
	int a = intValue[e1];
	int b = intValue[e2];
	if(a < b)
		return -1;
	else if(b < a)
		return 1;
	return 0;
}

void sortUpInt(int *order, int *val, int len) {
	// intValue = val;
	_quicksort((void*)order, len, sizeof(int), compareUpInt, val);
}

//TODO: dodac lepsze komentarze !
//UWAGA ! Zalozenie - parametru sa juz zlogarytmowane !
real getLnFi(int *paramId, int parNum, double *params)
{
	double fi = 0.;

	int j;
	for(j = 0 ; j < parNum ; ++j)
		fi += params[paramId[j]];	//UWAGA ! Zalozenie - parametru sa juz zlogarytmowane !

	// assert( isfinite(fi) );
	assert( !isinf(fi) );
	return realFromLog(fi);
}

//UWAGA ! Zalozenie - parametru sa juz zlogarytmowane !
real logPsi(int y, double *params, C_ConnsBuf *connsBuf)
{
	C_SimpleConns *simpleConns = connsBuf->simpleConns;
	return getLnFi(simpleConns->paramId[y], simpleConns->paramsNumber[y], params);
}

real logFi(int y, double *params, C_CompoundConns *compoundConns, real *Y, int *position, real *partSum, int *sortedLabels, int ysize)
{
	real res = realZero();

	int *prevLabels = compoundConns->prevLabels[y];
	int *paramsNumber = compoundConns->paramsNumber[y];
	int **paramId = compoundConns->paramId[y];
	int prevNum = compoundConns->prevNumber[y];

	int k;
	for(k = 0 ; k < prevNum ; ++k)
		sortedLabels[k] = prevLabels[k];

	sortUpInt(sortedLabels, position, prevNum);

	int lastPos = -1;
	for(k = 0 ; k < prevNum ; ++k) {
		int py = sortedLabels[k];
		int pos = position[py];

		res = realAdd(res, realSub(partSum[pos], partSum[lastPos+1]));
		lastPos = pos;
	}
	res = realAdd(res, realSub(partSum[ysize], partSum[lastPos+1]));

	for(k = 0 ; k < prevNum ; ++k) {
		int py = prevLabels[k];
		real realLogFi = getLnFi(paramId[k], paramsNumber[k], params);
		res = realAdd(res, realMult(Y[py], realLogFi));
	}

	return res;
}

real logDummyFi(int y, double *params, C_ConnsBuf *connsBuf, int dummy_id)
{
	C_CompoundConns *compoundConns = connsBuf->compoundConns;

	int *prevLabels = compoundConns->prevLabels[y];
	int *paramsNumber = compoundConns->paramsNumber[y];
	int **paramId = compoundConns->paramId[y];
	int prevNum = compoundConns->prevNumber[y];

	real res = realOne();

	int k;
	for(k = 0 ; k < prevNum ; ++k) {
		int py = prevLabels[k];

		if(py != dummy_id)
			continue;

		res = realMult(res, getLnFi(paramId[k], paramsNumber[k], params));
	}

	return res;
}

void getPositions(int *position, int *order, int len)
{
	int i;
	for(i = 0 ; i < len ; ++i)
		position[order[i]] = i;
}

void countPartSum(real *partSum, int *order, real *Y, int Y_size)
{
	int i;
	partSum[0] = realZero();
	for(i = 0 ; i < Y_size ; ++i)
		partSum[i+1] = realAdd(partSum[i], Y[order[i]]);
}

int checkUp(int *order, real *Y, int ysize)
{
	int i;
	for(i = 1 ; i < ysize ; ++i)
		if(Y[order[i]] < Y[order[i-1]])
			return 0;
	return 1;
}

double countLogAlpha(real *alpha, C_Sentence* sent, C_Model* model, C_Conns* conns, C_ConnsBuf *connsBuf)
{
	int i, y;

	int yn = model->yn;
	real *pY = alpha;
	real *Y = pY + yn;

	for(y = 0 ; y < yn ; ++y)
		pY[y] = realOne();

	// fillConnsBuf(connsBuf, conns, sent->words[0], sent->wsizes[0]);
	fillConnsBuf(connsBuf, conns, sent, 0);

	for(y = 0 ; y < yn ; ++y)
		Y[y] = realOne();

	for(y = 0 ; y < yn ; ++y)
		Y[y] = realMult(Y[y], logPsi(y, model->values, connsBuf));

	for(y = 0 ; y < yn ; ++y)
		Y[y] = realMult(Y[y], logDummyFi(y, model->values, connsBuf, model->dummy_id));

	clearConnsBuf(connsBuf);

	pY = Y;
	Y += yn;

	//for sorting Y values from previous column.
	int *order = malloc(yn * sizeof(int));
	for(y = 0 ; y < yn ; ++y)
		order[y] = y;

	//for sorting connection labels.
	int *sortedLabels = malloc(yn * sizeof(int));

	//for labels positions (regarding order).
	int *position = malloc(yn * sizeof(int));

	//for part sums of order table.
	real *partSum = malloc((yn + 1) * sizeof(real));
	
	for(i = 1 ; i < sent->length ; ++i) {
		// fillConnsBuf(connsBuf, conns, sent->words[i], sent->wsizes[i]);
		fillConnsBuf(connsBuf, conns, sent, i);

		// order -- porzadek na etykietach, wzgledem rosnacych wartosci pY.
		sortUpReal(order, pY, yn);
		//assert( checkUp(order, pY, yn) );
		getPositions(position, order, yn);
		countPartSum(partSum, order, pY, yn);

		for(y = 0 ; y < yn ; ++y)
			Y[y] = logFi(y, model->values, connsBuf->compoundConns, pY, position, partSum, sortedLabels, yn);

		for(y = 0 ; y < yn ; ++y)
			Y[y] = realMult(Y[y], logPsi(y, model->values, connsBuf));

		clearConnsBuf(connsBuf);

		pY = Y;
		Y += yn;
	}

	real sum = realZero();
	for(y = 0 ; y < yn ; ++y)
		sum = realAdd(sum, pY[y]);

	free(partSum);
	free(position);
	free(sortedLabels);
	free(order);

	return realLog(sum);
}

double countLogBeta(real *beta, C_Sentence* sent, C_Model* model, C_Conns* conns, C_ConnsBuf *connsBuf)
{
	int i, y;
	int yn = model->yn;

	real *psiVal = malloc(yn * sizeof(real));

	real *next_Y = beta + sent->length * yn;
	real *Y = next_Y - yn;

	//for sorting Y values from previous column.
	int *order = malloc(yn * sizeof(int));
	for(y = 0 ; y < yn ; ++y)
		order[y] = y;

	//for sorting connection labels.
	int *sortedLabels = malloc(yn * sizeof(int));

	//for labels positions (regarding order).
	int *position = malloc(yn * sizeof(int));

	//for part sums of order table.
	real *partSum = malloc((yn + 1) * sizeof(real));
	
	for(y = 0 ; y < yn ; ++y)
		next_Y[y] = realOne();

	for(i = sent->length - 1 ; i >= 0 ; --i) {
		// fillConnsBuf(connsBuf, conns, sent->words[i], sent->wsizes[i]);
		fillConnsBuf(connsBuf, conns, sent, i);

		for(y = 0 ; y < yn ; ++y) {
			psiVal[y] = logPsi(y, model->values, connsBuf);
			psiVal[y] = realMult(psiVal[y], next_Y[y]);
		}

		sortUpReal(order, psiVal, yn);
		//assert( checkUp(order, psiVal, yn) );
		getPositions(position, order, yn);
		countPartSum(partSum, order, psiVal, yn);

		for(y = 0 ; y < yn ; ++y)
			Y[y] = logFi(y, model->values, connsBuf->revCompoundConns, psiVal, position, partSum, sortedLabels, yn);

		clearConnsBuf(connsBuf);

		next_Y = Y;
		Y -= yn;
	}

	free(partSum);
	free(position);
	free(sortedLabels);
	free(order);

	free(psiVal);

	return realLog(next_Y[model->dummy_id]);
}

void countArgMax(double **maxTab, int **argMax, C_Sentence* sent, C_Model* model, C_Conns* conns, C_ConnsBuf *connsBuf)
{
	int i, k, l, y;
	double prevMax, max;
	int yn = model->yn;

	char** seenPair = malloc(yn * sizeof(char*));
	for(y = 0 ; y < yn ; ++y)
		seenPair[y] = calloc(yn, sizeof(char));

	int *prevOrder = malloc(yn * sizeof(int));

	for(y = 0 ; y < yn ; ++y)
		maxTab[0][y] = -HUGE_VAL;
	maxTab[0][model->dummy_id] = 0.0;

	for(i = 1 ; i < sent->length+1 ; ++i) {
		//sort values from previous column
		for(y = 0 ; y < yn ; ++y)
			prevOrder[y] = y;
		// prevCol = maxTab[i-1];
		_quicksort((void*)prevOrder, yn, sizeof(int), compareDownReal, maxTab[i-1]);
		//sortDown(...) ?
		
		// fillConnsBuf(connsBuf, conns, sent->words[i-1], sent->wsizes[i-1]);
		fillConnsBuf(connsBuf, conns, sent, i - 1);

		//get information about the seen pairs
		C_CompoundConns *compoundConns = connsBuf->compoundConns;
		for(y = 0 ; y < yn ; ++y) {
			int *prevLabels = compoundConns->prevLabels[y];
			int prevNum = compoundConns->prevNumber[y];

			for(k = 0 ; k < prevNum ; ++k) {
				int py = prevLabels[k];
				seenPair[py][y] = 1;
			}
		}

		//count default value for every row in column i,
		for(k = 0 ; k < yn ; ++k) {
			maxTab[i][k] = -HUGE_VAL;

			for(l = 0 ; l < yn ; ++l) {
				int arg = prevOrder[l];
				if(!seenPair[arg][k]) {
					maxTab[i][k] = maxTab[i-1][arg];	// maxTab[i-1][k] + ln(1.0)
					argMax[i][k] = arg;
					break;
				}
			}
		}

		//count maximum taking on account seen pairs (y1, y2)
		for(y = 0 ; y < yn ; ++y) {
			int *prevLabels = compoundConns->prevLabels[y];
			int prevNum = compoundConns->prevNumber[y];
			int *paramsNumber = compoundConns->paramsNumber[y];
			int **paramId = compoundConns->paramId[y];

			for(k = 0 ; k < prevNum ; ++k) {
				int py = prevLabels[k];
				real realLogFi = getLnFi(paramId[k], paramsNumber[k], model->values);
				double logFi = realLog(realLogFi);

				prevMax = maxTab[i-1][py];
				max = maxTab[i][y];
				if(logFi + prevMax > max) {
					maxTab[i][y] = logFi + prevMax;
					argMax[i][y] = py;
				}
			}
		}

		//erase information about the seen pairs
		for(y = 0 ; y < yn ; ++y) {
			int *prevLabels = compoundConns->prevLabels[y];
			int prevNum = compoundConns->prevNumber[y];

			for(k = 0 ; k < prevNum ; ++k) {
				int py = prevLabels[k];
				seenPair[py][y] = 0;
			}
		}

		//change maxTab value with respect to
		//features f(y, x). Additionally, exclude
		//dummy_id row
		for(k = 0 ; k < yn ; ++k) {
			if(k == model->dummy_id) {
				maxTab[i][k] = -HUGE_VAL;
				continue;
			}

			maxTab[i][k] += realLog(logPsi(k, model->values, connsBuf));
		}

		//clear connection buffer
		clearConnsBuf(connsBuf);
	}

	free(prevOrder);

	for(i = 0 ; i < yn ; ++i)
		free(seenPair[i]);
	free(seenPair);
}

void tag_sent(C_Sentence* sent, C_Model* model, C_Conns* conns, C_ConnsBuf* connsBuf, int* labels)
{
	int yn = model->yn;
	double *maxTabMem = (double *) malloc((sent->length+1)*yn*sizeof(double));
	if(maxTabMem == NULL) return;
	double **maxTab = (double **) malloc((sent->length+1) * sizeof(double*));
	if(maxTab == NULL) return;

	int *argMaxMem = (int *) malloc((sent->length+1)*yn*sizeof(int));
	if(argMaxMem == NULL) return;
	int **argMax = (int **) malloc((sent->length+1) * sizeof(int*));
	if(argMax == NULL) return;

	int i, j;
	for(i = 0 ; i < sent->length+1 ; ++i) {
		maxTab[i] = &maxTabMem[i*yn];
		argMax[i] = &argMaxMem[i*yn];
	}

	countArgMax(maxTab, argMax, sent, model, conns, connsBuf);

	int arg = 0;
	for(j = 1 ; j < yn ; ++j)
		if(maxTab[sent->length][j] > maxTab[sent->length][arg])
			arg = j;

	labels[sent->length - 1] = arg;
	for(i = sent->length ; i >= 2 ; --i) {
		arg = argMax[i][arg];
		labels[i - 2] = arg;
	}

	free(argMax);
	free(argMaxMem);
	free(maxTab);
	free(maxTabMem);
}

void fillB(double* B, real* alpha, real* beta, C_Sentence* sent, C_Model* model, C_Conns* conns, C_ConnsBuf* connsBuf, double logZx)
{
	int i, j, k, y;
	int yn = model->yn;
	for(i = 0 ; i < sent->length ; ++i) {
		// fillConnsBuf(connsBuf, conns, sent->words[i], sent->wsizes[i]);
		fillConnsBuf(connsBuf, conns, sent, i);

		C_CompoundConns* compoundConns = connsBuf->compoundConns;
		for(y = 0 ; y < yn ; ++y) {
			int *prevLabels = compoundConns->prevLabels[y];
			int prevNum = compoundConns->prevNumber[y];
			int *paramsNumber = compoundConns->paramsNumber[y];
			int **paramId = compoundConns->paramId[y];

			double lnPsi = logPsi(y, model->values, connsBuf);

			for(k = 0 ; k < prevNum ; ++k) {
				int py = prevLabels[k];
				int parNum = paramsNumber[k];
				int *parId = paramId[k];

				real realLogFi = getLnFi(parId, parNum, model->values);
				double lnFi = realLog(realLogFi);

				double _alpha = realLog(alpha[i*yn + py]);
				double _beta = realLog(beta[(i+1)*yn + y]);
				double a = exp(_alpha + lnFi + lnPsi + _beta - logZx);
	
				for(j = 0 ; j < parNum ; ++j) {
					int par_id = parId[j];
					B[par_id] += a;
				}
			}
		}

		C_SimpleConns *simpleConns = connsBuf->simpleConns;
		for(y = 0 ; y < yn ; ++y) {
			int parNum = simpleConns->paramsNumber[y];
			int *parId = simpleConns->paramId[y];

			double _alpha = realLog(alpha[(i+1)*yn + y]);
			double _beta = realLog(beta[(i+1)*yn + y]);
			double a = exp(_alpha + _beta - logZx);

			for(j = 0 ; j < parNum ; ++j) {
				int par_id = parId[j];
				B[par_id] += a;
			}
		}

		clearConnsBuf(connsBuf);
	}

}

double logZ(C_Sentence* sent, C_Model* model, C_Conns* conns, C_ConnsBuf* connsBuf, double* B)
{
	real *alpha = (real *) malloc((sent->length+1) * model->yn * sizeof(real));
	real *beta = (real *) malloc((sent->length+1) * model->yn * sizeof(real));

	if(alpha == NULL || beta == NULL)
		return -1.0;

	// TODO: When not counting gradient (B == NULL), there is no reason to call countLogBeta.
	double logZx = countLogAlpha(alpha, sent, model, conns, connsBuf);
	double logZx2 = countLogBeta(beta, sent, model, conns, connsBuf);

	if(fabs(logZx-logZx2) > 1.0e-5) {
		printf("logZx - logZx2 = %e\n", logZx - logZx2);
		printf("logZx = %e, logZx2 = %e\n", logZx, logZx2);
	}

        if(B != NULL)
		fillB(B, alpha, beta, sent, model, conns, connsBuf, logZx);

	free(beta);
	free(alpha);

	return logZx;
}
