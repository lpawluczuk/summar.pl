#ifndef _REAL_H_
#define _REAL_H_

typedef double real;

void realPrint(real r);

real realOne(void);
real realZero(void);
real realFromLog(double l);

void initExpTab(void);

real realAdd(real r1, real r2);
real realSub(real r1, real r2);		//zalozenie: r1 >= r2
real realMult(real r1, real r2);
double realLog(real r);

#endif
