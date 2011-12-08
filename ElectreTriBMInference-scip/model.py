from zibopt import scip
from itertools import product

class leroy_linear_problem():

    def __init__(self, a, c, pt, af, cat, epsilon=0.1):
        self.a = a
        self.c = c
        self.pt = pt
        self.af = af
        self.cat = cat
        self.epsilon = epsilon

        self.ncrit = len(self.c)
        self.nalts = len(self.a)
        print("ncrit %d; nalts %d" % (self.ncrit, self.nalts))

#        for aa in self.af:
#            print(cat(aa.category_id).rank)

        self.solver = scip.solver(quiet=False)
        self._init_variables()
        self._add_constraints()

    def _init_variables(self):
        self.v_lbda = self.solver.variable(scip.CONTINUOUS,
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
            self.v_w[j.id] = self.solver.variable(scip.CONTINUOUS,
                                                  upper=1)

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
        for i, j in product(range(0, len(self.cat)+1), self.c):
            self.v_gb[i, j.id] = self.solver.variable(scip.CONTINUOUS)

    def _add_constraints(self):
        for i in self.a:
            self.solver += sum(self.v_cinf[i.id][j.id] for j in self.c) \
                                >= self.v_lbda - 2 * (1-self.v_g[i.id])
            self.solver += sum(self.v_csup[i.id][j.id] for j in self.c) \
                                + self.epsilon \
                                <= self.v_lbda + 2 * (1-self.v_g[i.id])

        for i, j in product(self.a, self.c):
            self.solver += self.v_cinf[i.id][j.id] <= self.v_w[j.id] 
            self.solver += self.v_csup[i.id][j.id] <= self.v_w[j.id] 
            self.solver += self.v_cinf[i.id][j.id] \
                            <= self.v_dinf[i.id][j.id]
            self.solver += self.v_csup[i.id][j.id] \
                            <= self.v_dsup[i.id][j.id]
            self.solver += self.v_cinf[i.id][j.id] \
                            >= self.v_dinf[i.id][j.id] - 1 + self.v_w[j.id]
            self.solver += self.v_csup[i.id][j.id] \
                            >= self.v_dsup[i.id][j.id] - 1 + self.v_w[j.id]

        for i, j in product(self.af, self.c):
            i_cat_rank = int(self.cat(i.category_id).rank)
            self.solver += self.v_dinf[i.alternative_id][j.id] \
                            >= self.pt(i.alternative_id, j.id) \
                                - self.v_gb[i_cat_rank-1, j.id] \
                                + self.epsilon
            self.solver += self.v_dsup[i.alternative_id][j.id] \
                            >= self.pt(i.alternative_id, j.id) \
                                - self.v_gb[i_cat_rank, j.id] \
                                + self.epsilon
            self.solver += self.v_dinf[i.alternative_id][j.id] \
                            <= self.pt(i.alternative_id, j.id) \
                                - self.v_gb[i_cat_rank-1, j.id] \
                                + 1
            self.solver += self.v_dinf[i.alternative_id][j.id] \
                            <= self.pt(i.alternative_id, j.id) \
                                - self.v_gb[i_cat_rank, j.id] \
                                + 1

        for i, j in product(range(1, len(self.cat)), self.c):
            self.solver += self.v_gb[i, j.id] <= self.v_gb[i+1, j.id]

#        for j in self.c:
#            self.solver += self.v_gb[0, j.id] == self.epsilon

        self.solver += sum(self.v_w[j.id] for j in self.c) == 1 

    def solve(self):
        self.solver.maximize(objective=sum(self.v_g[i.id] for i in self.a))
