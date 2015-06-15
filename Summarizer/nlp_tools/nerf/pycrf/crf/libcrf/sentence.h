#ifndef _SENTENCE_H_
#define _SENTENCE_H_

typedef struct {
	int length;
	int** singles;
	int* snum;
	int** pairs;
	int* pnum;
} C_Sentence;

#endif
