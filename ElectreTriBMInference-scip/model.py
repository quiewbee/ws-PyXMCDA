from zibopt import scip
from itertools import product

class leroy_linear_problem():

    def __init__(self, a, c, pt, af, cat, epsilon=0.0000001):
        self.a = a
        self.c = c
        self.pt = pt
        self.af = af
        self.cat = cat

        self.solver = scip.solver(quiet=False)

        self.epsilon = self.solver.variable(scip.CONTINUOUS)
        self.solver += self.epsilon - epsilon == 0

        self._init_variables()
        self._add_constraints()

    def _init_variables(self):
        self.v_lbda = self.solver.variable(scip.CONTINUOUS,
                                           lower=0.5, upper=1)

        # csup and cinf
        self.v_csup = dict((i.id, {}) for i in self.a)
        self.v_cinf = dict((i.id, {}) for i in self.a)
        for i, j in product(self.a, self.c):
            self.v_csup[i.id][j.id] = self.solver.variable(scip.CONTINUOUS)
            self.v_cinf[i.id][j.id] = self.solver.variable(scip.CONTINUOUS)

        # weights
        self.v_w = dict((j.id, {}) for j in self.c)
        for j in self.c:
            self.v_w[j.id] = self.solver.variable(scip.CONTINUOUS,
                                                  upper=1)

        # gamma
        self.v_g = {}
        for i in self.a:
            self.v_g[i.id] = self.solver.variable(scip.BINARY)

        # dsup and dinf
        self.v_dsup = dict((i.id, {}) for i in self.a)
        self.v_dinf = dict((i.id, {}) for i in self.a)
        for i, j in product(self.a, self.c):
            self.v_dsup[i.id][j.id] = self.solver.variable(scip.BINARY)
            self.v_dinf[i.id][j.id] = self.solver.variable(scip.BINARY)

        # gb (profiles evaluations)
        self.v_gb = dict((i, {}) for i in range(0, len(self.cat)+1))
        for i, j in product(range(0, len(self.cat)+1), self.c):
            self.v_gb[i][j.id] = self.solver.variable(scip.CONTINUOUS)

    def _add_constraints(self):
        for i in self.a:
            self.solver += sum(self.v_cinf[i.id][j.id] for j in self.c) \
                                - self.v_lbda - 2*self.v_g[i.id] >= -2
            self.solver += sum(self.v_csup[i.id][j.id] for j in self.c) \
                                - self.v_lbda + 2*self.v_g[i.id] \
                                + self.epsilon <= 2

        for i, j in product(self.a, self.c):
            self.solver += self.v_cinf[i.id][j.id] - self.v_w[j.id] <= 0 
            self.solver += self.v_csup[i.id][j.id] - self.v_w[j.id] <= 0
            self.solver += self.v_cinf[i.id][j.id] \
                            - self.v_dinf[i.id][j.id] <= 0
            self.solver += self.v_csup[i.id][j.id] \
                            - self.v_dsup[i.id][j.id] <= 0
            self.solver += self.v_cinf[i.id][j.id] \
                            - self.v_dinf[i.id][j.id] - self.v_w[j.id] >= -1
            self.solver += self.v_csup[i.id][j.id] \
                            - self.v_dsup[i.id][j.id] - self.v_w[j.id] >= -1

        for i, j in product(self.af, self.c):
            i_cat_rank = len(self.cat)+1-int(self.cat(i.category_id).rank)
            self.solver += self.v_dinf[i.alternative_id][j.id] \
                                + self.v_gb[i_cat_rank-1][j.id] \
                                - self.epsilon \
                                >= self.pt(i.alternative_id, j.id)
            self.solver += self.v_dsup[i.alternative_id][j.id] \
                                + self.v_gb[i_cat_rank][j.id] \
                                - self.epsilon \
                                >= self.pt(i.alternative_id, j.id)
            self.solver += self.v_dinf[i.alternative_id][j.id] \
                                + self.v_gb[i_cat_rank-1][j.id] \
                                <= (1 + self.pt(i.alternative_id, j.id))
            self.solver += self.v_dinf[i.alternative_id][j.id] \
                                + self.v_gb[i_cat_rank][j.id] \
                                <= (1 + self.pt(i.alternative_id, j.id))

        for i, j in product(range(0, len(self.cat)), self.c):
            self.solver += self.v_gb[i][j.id]-self.v_gb[i+1][j.id] <= 0

        self.solver += sum(self.v_w[j.id] for j in self.c) -1 == 0

    def solve(self):
        obj = sum(self.v_g[i.id] for i in self.a)
        solution = self.solver.maximize(objective=obj)

        print('z  =', solution.objective)

        compat = {}
        for i in self.a:
            compat[i.id] = solution[self.v_g[i.id]]
        print('compat', compat)

        w = {}
        for i in self.c:
            w[i.id] = solution[self.v_w[i.id]]
        print('weights', w)

        print('lambda', solution[self.v_lbda])

        for i in range(0, len(self.cat)+1):
            perfs = {}
            for j in self.c:
                perfs[j.id] = solution[self.v_gb[i][j.id]]
            print(i, perfs)
