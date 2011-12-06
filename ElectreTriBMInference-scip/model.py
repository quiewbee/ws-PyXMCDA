from zibopt import scip
from itertools import product

class leroy_linear_problem():

    def __init__(self, a, c, pt, af, cat):
        self.a = a
        self.c = c
        self.pt = pt
        self.af = af
        self.cat = cat

        self.ncrit = len(self.c)
        self.nalts = len(self.a)
        print("ncrit %d; nalts %d" % (self.ncrit, self.nalts))

        self.solver = scip.solver()
        self._init_variables()
        self._add_variables_constraints()
        self._add_constraints()

    def _init_variables(self):
        # Lambda
        self.v_lbda = self.solver.variable(vartype=scip.CONTINUOUS,
                                           lower=0.5, upper=1)

        # csup and cinf
        self.v_csup = dict((i.id,
                           dict((j.id, {}) for j in self.c))
                           for i in self.a)
        self.v_cinf = dict((i.id,
                           dict((j.id, {}) for j in self.c))
                           for i in self.a)

        for i, j in product(self.a, self.c):
            self.v_csup[i.id][j.id] = self.solver.variable(scip.CONTINUOUS)
            self.v_cinf[i.id][j.id] = self.solver.variable(scip.CONTINUOUS)

        # weights
        self.v_w = dict((j.id, {}) for j in self.c)
        for j in self.c:
            self.v_w[j.id] = self.solver.variable(scip.CONTINUOUS)

        # gamma
        self.v_g = dict((i.id, {}) for i in self.a)
        for i in self.a:
            self.v_g[i.id] = self.solver.variable(scip.BINARY)

        # dsup and dinf
        self.v_dsup = dict((i.id,
                           dict((j.id, {}) for j in self.c))
                           for i in self.a)
        self.v_dinf = dict((i.id,
                           dict((j.id, {}) for j in self.c))
                           for i in self.a)
        for i, j in product(self.a, self.c):
            self.v_dsup[i.id][j.id] = self.solver.variable(scip.BINARY)
            self.v_dinf[i.id][j.id] = self.solver.variable(scip.BINARY)

        # gb (profiles evaluations)
        self.v_gb = dict((i,
                         dict((j.id, {}) for j in self.c))
                         for i in range(0, len(self.cat)))
        for i, j in product(range(0, len(self.cat)), self.c):
            self.v_gb[i, j.id] = self.solver.variable(scip.CONTINUOUS)

    def _add_variables_constraints(self):
        pass

    def _add_constraints(self):
        pass

    def solve(self):
        pass
