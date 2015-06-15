#ifndef _MODEL_H_
#define _MODEL_H_

typedef struct {
	int pn;	// number of parameters
	int* features;
	double* values;

	int xn;
	int yn;
	int dummy_id;
} C_Model;

#endif
