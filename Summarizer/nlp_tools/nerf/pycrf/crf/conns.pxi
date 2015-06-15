# encoding: utf-8

cdef class Conns:

    def __cinit__(self):
        self.conns.xn = 0
        self.conns.conns = NULL
        self.conns.csizes = NULL 

    def _dealloc(self):
        if self.conns.csizes is not NULL:
            free(self.conns.csizes)
        if self.conns.conns is not NULL:
            for i in range(self.conns.xn):
                if self.conns.conns[i] is not NULL:
                    free(self.conns.conns[i])
            free(self.conns.conns)

    def __dealloc__(self):
        self._dealloc()

    def __init__(self, Model model):
        self._dealloc()
        self.conns.xn = model.xn

        conns = defaultdict(list)
        for i, (feature, _) in enumerate(model):
            (py, y, x) = feature
            conns[x].append((py, y, i))
        # conns = sorted(conns.items())
        # assert len(conns) == self.conns.xn

        self.conns.csizes = <int*>malloc(self.conns.xn * sizeof(int))
        if self.conns.csizes is NULL:
            raise MemoryError
        self.conns.conns = <int**>malloc(self.conns.xn * sizeof(int*))
        if self.conns.conns is NULL:
            raise MemoryError
        for x in range(self.conns.xn):
            self.conns.conns[x] = NULL

        for x in range(self.conns.xn):
            xconns = conns.get(x, [])
            self.conns.csizes[x] = len(xconns)
            self.conns.conns[x] = <int*>malloc(
                    max(1, len(xconns)) * 3 * sizeof(int))
            if self.conns.conns[x] is NULL:
                raise MemoryError
            for k, (py, y, par_id) in enumerate(xconns):
                self.conns.conns[x][k*3] = py
                self.conns.conns[x][k*3 + 1] = y
                self.conns.conns[x][k*3 + 2] = par_id

    def __getitem__(self, x):
        if x < 0 or x >= self.conns.xn:
            raise IndexError
        return [(
            self.conns.conns[x][k*3],
            self.conns.conns[x][k*3 + 1],
            self.conns.conns[x][k*3 + 2])
            for k in range(self.conns.csizes[x])]
