#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#undef NDEBUG
#include <assert.h>

#include "real.h"

#ifndef INFINITY
#define INFINITY HUGE_VAL
#endif

inline void realPrint(real r)
{
	printf("%e\n", r);
}

real realOne(void)
{
	return 0.0;
}

real realZero(void)
{
	return -INFINITY;
	realPrint(exp(-INFINITY));
}

inline real realFromLog(double l)
{
	return l;
}

//TODO: zmienic na initRealModule
void initExpTab(void)
{
	;
}

#define isZero(r) ((r) == -INFINITY)

real realAdd(real r1, real r2)
{
	//wystarczy jedna liczba niezerowa (!= -INFINITY)
	//zeby ponizszy kod wykonal sie poprawnie.
	if(isZero(r1))
		return r2;

	real res;
	if(r1 > r2)
		res = r1 + log1p(exp(r2 - r1));
	else
		res = r2 + log1p(exp(r1 - r2));

	assert( !isnan(res) );
	return res;
}

//zalozenie: r1 >= r2
real realSub(real r1, real r2)
{
	if(isZero(r2))
		return r1;

	real res;
	if(r1 > r2)
		res = r1 + log1p(-exp(r2 - r1));
	else
		res = r2 + log1p(-exp(r1 - r2));

	if(isnan(res))
		printf("r1 = %e, r2 = %e\n", r1, r2);
	assert( !isnan(res) );
	return res;
}

inline real realMult(real r1, real r2)
{
	return r1 + r2;
}

inline double realLog(real r)
{
	return r;
}

