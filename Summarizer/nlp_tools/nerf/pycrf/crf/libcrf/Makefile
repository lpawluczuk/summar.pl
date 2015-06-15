all: connsbuf.o qsort.o utils.o real.o
	ar rcs libfastcrf.a connsbuf.o qsort.o utils.o real.o

connsbuf.o: connsbuf.c
	gcc -fPIC -g -c -Wall connsbuf.c

qsort.o: qsort.c
	gcc -fPIC -g -c -Wall qsort.c

utils.o: utils.c
	gcc -fPIC -g -c -Wall utils.c

real.o: real.c
	gcc -fPIC -g -c -Wall real.c

clear:
	rm *.o *.a
