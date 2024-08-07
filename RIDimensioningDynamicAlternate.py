
# This is the same model as the Capacity_and_energy.py but we want to run it per hour. On this case, we import the ATC data from ODIN (Elis' model).
# Then, we use the data for the reference incident from FRR Dimesioning webinar but we need to make it random for one scenario out of 365 scenarios.

import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import random
import math
import time

class RIDimensioning:
    def __init__(self, atc, epsilon, vertex_sets):
        self.atc = atc
        self.num_RI = 22
        self.epsilon = epsilon
        self.vertex_sets = vertex_sets

    class MIP:
        def __init__(self, atc, num_RI, epsilon, vertex_sets):
            self.name = 'MIPModel'
            self.areas = ('SE1', 'SE2', 'SE3', 'SE4', 'NO1', 'NO2', 'NO3', 'NO4', 'NO5', 'DK2', 'FI')
            self.num_RI = num_RI
            self.ac_links = {
                'SE1->SE2': ('SE2', 'SE1', 'SE2->SE1'),
                'SE1->NO4': ('NO4', 'SE1', 'NO4->SE1'),
                'SE1->FI': ('FI', 'SE1', 'FI->SE1'),
                'SE2->NO4': ('NO4', 'SE2', 'NO4->SE2'),
                'SE2->NO3': ('NO3', 'SE2', 'NO3->SE2'),
                'SE2->SE3': ('SE3', 'SE2', 'SE3->SE2'),
                'SE3->NO1': ('NO1', 'SE3', 'NO1->SE3'),
                'SE3->SE4': ('SE4', 'SE3', 'SE4->SE3'),
                'SE4->DK2': ('DK2', 'SE4', 'DK2->SE4'),
                'NO1->NO2': ('NO2', 'NO1', 'NO2->NO1'),
                'NO1->NO3': ('NO3', 'NO1', 'NO3->NO1'),
                'NO1->NO5': ('NO5', 'NO1', 'NO5->NO1'),
                'NO2->NO5': ('NO5', 'NO2', 'NO5->NO2'),
                'NO3->NO5': ('NO5', 'NO3', 'NO5->NO3'),
                'NO3->NO4': ('NO4', 'NO3', 'NO4->NO3')
            }

            self.RI_up = {'SE1': 800,
                          'SE2': 600,
                          'SE3': 1450,
                          'SE4': 1000,
                          'NO1': 1450,
                          'NO2': 1400,
                          'NO3': 1000,
                          'NO4': 650,
                          'NO5': 700,
                          'DK2': 600,
                          'FI': 1300
                          }

            self.RI_down = {'SE1': 1100,
                            'SE2': 1000,
                            'SE3': 1350,
                            'SE4': 700,
                            'NO1': 1450,
                            'NO2': 1400,
                            'NO3': 600,
                            'NO4': 800,
                            'NO5': 1400,
                            'DK2': 600,
                            'FI': 800
                            }
            self.epsilon = epsilon
            self.atc_pos = pd.DataFrame(columns=self.ac_links.keys(), index=atc.index)
            self.atc_neg = pd.DataFrame(columns=self.ac_links.keys(), index=atc.index)
            for l in self.ac_links.keys():
                self.atc_pos[l] = atc[l]
                self.atc_neg[l] = atc[self.ac_links[l][2]]
            self.VERTEXSETS = vertex_sets

        def compute_h(self, vertex_set, imbalance, atc_pos, atc_neg, q):
            import_lines = []
            export_lines = []
            for a in vertex_set:
                for l in self.ac_links.keys():
                    if self.ac_links[l][0] == a and self.ac_links[l][1] not in vertex_set:
                        import_lines.append(l)
                    elif self.ac_links[l][1] == a and self.ac_links[l][0] not in vertex_set:
                        export_lines.append(l)
            h_pos = pd.DataFrame(columns=['Value'])
            h_neg = pd.DataFrame(columns=['Value'])
            h_pos['Value'] = [0 for i in range(imbalance.__len__())]
            h_neg['Value'] = [0 for i in range(imbalance.__len__())]
            for a in vertex_set:
                h_pos['Value'] -= imbalance[a]
                h_neg['Value'] += imbalance[a]
            for l in import_lines:
                h_pos['Value'] -= atc_pos[l]
                h_neg['Value'] -= atc_neg[l]
            for l in export_lines:
                h_pos['Value'] -= atc_neg[l]
                h_neg['Value'] -= atc_pos[l]
            h_pos = h_pos.sort_values(by=['Value'], ascending=False)
            h_neg = h_neg.sort_values(by=['Value'], ascending=False)
            sigma_pos = h_pos.index.tolist()[:q]
            sigma_neg = h_neg.index.tolist()[:q]
            h_pos = h_pos['Value'].tolist()[:q + 1]
            h_neg = h_neg['Value'].tolist()[:q + 1]
            return h_pos, h_neg, sigma_pos, sigma_neg

        def setup_problem(self):
            self.SET_ACLINKS = self.ac_links.keys()
            self.SET_AREAS = self.areas
            self.PARAM_EPSILON = self.epsilon
            self.SET_SCENARIOS = range(self.atc_pos.__len__() * self.num_RI)
            self.SET_VERTEXSETS = range(self.VERTEXSETS.__len__())
            self.PARAM_IMBALANCES_DIST = pd.DataFrame(columns=self.areas, index=self.SET_SCENARIOS)
            self.Q = math.floor(self.SET_SCENARIOS.__len__() * self.PARAM_EPSILON)
            self.SET_Q = list(range(self.Q))

            for hour in range(self.atc_pos.__len__()):
                for i in range(math.ceil(self.num_RI / 2)):
                    for a in self.areas:
                        if a == self.areas[i]:
                            self.PARAM_IMBALANCES_DIST[a][hour * self.num_RI + i] = - self.RI_up[a]
                        else:
                            self.PARAM_IMBALANCES_DIST[a][hour * self.num_RI + i] = 0
                for j in range(math.ceil(self.num_RI / 2)):
                    for a in self.areas:
                        if a == self.areas[j]:
                            self.PARAM_IMBALANCES_DIST[a][hour * self.num_RI + i + 1 + j] = self.RI_down[a]
                        else:
                            self.PARAM_IMBALANCES_DIST[a][hour * self.num_RI + i + 1 + j] = 0

            self.PARAM_ATC_POS = pd.DataFrame(columns=self.SET_ACLINKS, index=self.SET_SCENARIOS)
            self.PARAM_ATC_NEG = pd.DataFrame(columns=self.SET_ACLINKS, index=self.SET_SCENARIOS)
            for l in self.SET_ACLINKS:
                self.PARAM_ATC_POS[l] = [self.atc_pos[l][h] for h in self.atc_pos.index.tolist() for x in
                                         range(self.num_RI)]
                self.PARAM_ATC_NEG[l] = [self.atc_neg[l][h] for h in self.atc_neg.index.tolist() for x in
                                         range(self.num_RI)]

            self.PARAM_HPOS = {}
            self.PARAM_HNEG = {}
            self.SET_SIGMAPOS = {}
            self.SET_SIGMANEG = {}
            for i in range(self.VERTEXSETS.__len__()):
                self.PARAM_HPOS[i], self.PARAM_HNEG[i], self.SET_SIGMAPOS[i], self.SET_SIGMANEG[i] = \
                    self.compute_h(vertex_set=self.VERTEXSETS[i],
                                   imbalance=self.PARAM_IMBALANCES_DIST, atc_pos=self.PARAM_ATC_POS,
                                   atc_neg=self.PARAM_ATC_NEG, q=self.Q)
            self.gm = gp.Model(name='Model')

            self.VAR_RESERVECAPUP = self.gm.addVars(self.SET_AREAS, name='reservecapacityup', vtype=GRB.CONTINUOUS,
                                                    lb=0, ub=float('inf'))
            self.VAR_RESERVECAPDOWN = self.gm.addVars(self.SET_AREAS, name='reservecapacitydown', vtype=GRB.CONTINUOUS,
                                                      lb=0, ub=float('inf'))
            self.VAR_OMEGAPOS = self.gm.addVars(self.SET_VERTEXSETS, self.SET_Q, name='omegapos', vtype=GRB.BINARY,
                                                lb=0, ub=1)
            self.VAR_OMEGANEG = self.gm.addVars(self.SET_VERTEXSETS, self.SET_Q, name='omeganeg', vtype=GRB.BINARY,
                                                lb=0, ub=1)
            self.VAR_VIOLATION_POS = self.gm.addVars(self.SET_SCENARIOS, name='violationpos', vtype=GRB.BINARY,
                                                     lb=0, ub=1)
            self.VAR_VIOLATION_NEG = self.gm.addVars(self.SET_SCENARIOS, name='violationneg', vtype=GRB.BINARY,
                                                     lb=0, ub=1)

            self.setup_objective()
            self.setup_reserve_constraint_up()
            self.setup_reserve_constraint_down()
            self.setup_binary_up1()
            self.setup_binary_down1()
            self.setup_binary_up2()
            self.setup_binary_down2()
            self.setup_chance_up()
            self.setup_chance_down()
            self.gm.setParam('MIPGap', 0)
            self.gm.setParam('NumericFocus', 3)

        def setup_objective(self):
            self.obj = sum(self.VAR_RESERVECAPUP[a] + self.VAR_RESERVECAPDOWN[a] for a in self.SET_AREAS)
            self.gm.setObjective(self.obj, sense=GRB.MINIMIZE)

        def setup_reserve_constraint_up(self):
            self.CONSTR_RESERVE_UP = {}
            for s in self.SET_VERTEXSETS:
                left_hand = sum(self.VAR_RESERVECAPUP[a] for a in self.VERTEXSETS[s])
                left_hand += sum(
                    (self.PARAM_HPOS[s][i] - self.PARAM_HPOS[s][i + 1]) * self.VAR_OMEGAPOS[s, i] for i in self.SET_Q)
                right_hand = self.PARAM_HPOS[s][0]
                self.CONSTR_RESERVE_UP[s] = self.gm.addLConstr(
                    lhs=left_hand,
                    sense=GRB.GREATER_EQUAL,
                    rhs=right_hand,
                    name=f'RESERVEUP[{s}]'
                )

        def setup_reserve_constraint_down(self):
            self.CONSTR_RESERVE_DOWN = {}
            for s in self.SET_VERTEXSETS:
                left_hand = sum(self.VAR_RESERVECAPDOWN[a] for a in self.VERTEXSETS[s])
                left_hand += sum(
                    (self.PARAM_HNEG[s][i] - self.PARAM_HNEG[s][i + 1]) * self.VAR_OMEGANEG[s, i] for i in self.SET_Q)
                right_hand = self.PARAM_HNEG[s][0]
                self.CONSTR_RESERVE_DOWN[s] = self.gm.addLConstr(
                    lhs=left_hand,
                    sense=GRB.GREATER_EQUAL,
                    rhs=right_hand,
                    name=f'RESERVEDOWN[{s}]'
                )

        def setup_binary_up1(self):
            self.CONSTR_BINARY_UP1 = {}
            for s in self.SET_VERTEXSETS:
                for i in range(self.Q - 1):
                    left_hand = self.VAR_OMEGAPOS[s, i] - self.VAR_OMEGAPOS[s, i + 1]
                    right_hand = 0
                    self.CONSTR_BINARY_UP1[s, i] = self.gm.addLConstr(
                        lhs=left_hand,
                        sense=GRB.GREATER_EQUAL,
                        rhs=right_hand,
                        name=f'BINARYUP1[{s, i}]'
                    )

        def setup_binary_down1(self):
            self.CONSTR_BINARY_DOWN1 = {}
            for s in self.SET_VERTEXSETS:
                for i in range(self.Q - 1):
                    left_hand = self.VAR_OMEGANEG[s, i] - self.VAR_OMEGANEG[s, i + 1]
                    right_hand = 0
                    self.CONSTR_BINARY_DOWN1[s, i] = self.gm.addLConstr(
                        lhs=left_hand,
                        sense=GRB.GREATER_EQUAL,
                        rhs=right_hand,
                        name=f'BINARYDOWN1[{s, i}]'
                    )

        def setup_binary_up2(self):
            self.CONSTR_BINARY_UP2 = {}
            for s in self.SET_VERTEXSETS:
                for i in range(self.Q):
                    left_hand = self.VAR_VIOLATION_POS[self.SET_SIGMAPOS[s][i]] - self.VAR_OMEGAPOS[s, i]
                    right_hand = 0
                    self.CONSTR_BINARY_UP2[s, i] = self.gm.addLConstr(
                        lhs=left_hand,
                        sense=GRB.GREATER_EQUAL,
                        rhs=right_hand,
                        name=f'BINARYUP2[{s, i}]'
                    )

        def setup_binary_down2(self):
            self.CONSTR_BINARY_DOWN2 = {}
            for s in self.SET_VERTEXSETS:
                for i in range(self.Q):
                    left_hand = self.VAR_VIOLATION_NEG[self.SET_SIGMANEG[s][i]] - self.VAR_OMEGANEG[s, i]
                    right_hand = 0
                    self.CONSTR_BINARY_DOWN2[s, i] = self.gm.addLConstr(
                        lhs=left_hand,
                        sense=GRB.GREATER_EQUAL,
                        rhs=right_hand,
                        name=f'BINARYDOWN2[{s, i}]'
                    )

        def setup_chance_up(self):
            left_hand = sum(self.VAR_VIOLATION_POS[i] for i in self.SET_SCENARIOS)
            right_hand = self.Q
            self.CONSTR_CHANCE_UP = self.gm.addLConstr(
                lhs=left_hand,
                sense=GRB.LESS_EQUAL,
                rhs=right_hand,
                name=f'CHANCEUP'
            )

        def setup_chance_down(self):
            left_hand = sum(self.VAR_VIOLATION_NEG[i] for i in self.SET_SCENARIOS)
            right_hand = self.Q
            self.CONSTR_CHANCE_DOWN = self.gm.addLConstr(
                lhs=left_hand,
                sense=GRB.LESS_EQUAL,
                rhs=right_hand,
                name=f'CHANCEDOWN'
            )

    class LP:
        def __init__(self, atc_pos, atc_neg, imbalance, reserve_up, reserve_down, binary_pos, binary_neg):
            self.PARAM_ATCPOS = atc_pos
            self.PARAM_ATCNEG = atc_neg
            self.PARAM_IMBALANCE = imbalance
            self.PARAM_RESERVEUP = reserve_up
            self.PARAM_RESERVEDOWN = reserve_down
            self.PARAM_BINARYPOS = binary_pos
            self.PARAM_BINARYNEG = binary_neg
            self.ac_links = {
                'SE1->SE2': ('SE2', 'SE1', 'SE2->SE1'),
                'SE1->NO4': ('NO4', 'SE1', 'NO4->SE1'),
                'SE1->FI': ('FI', 'SE1', 'FI->SE1'),
                'SE2->NO4': ('NO4', 'SE2', 'NO4->SE2'),
                'SE2->NO3': ('NO3', 'SE2', 'NO3->SE2'),
                'SE2->SE3': ('SE3', 'SE2', 'SE3->SE2'),
                'SE3->NO1': ('NO1', 'SE3', 'NO1->SE3'),
                'SE3->SE4': ('SE4', 'SE3', 'SE4->SE3'),
                'SE4->DK2': ('DK2', 'SE4', 'DK2->SE4'),
                'NO1->NO2': ('NO2', 'NO1', 'NO2->NO1'),
                'NO1->NO3': ('NO3', 'NO1', 'NO3->NO1'),
                'NO1->NO5': ('NO5', 'NO1', 'NO5->NO1'),
                'NO2->NO5': ('NO5', 'NO2', 'NO5->NO2'),
                'NO3->NO5': ('NO5', 'NO3', 'NO5->NO3'),
                'NO3->NO4': ('NO4', 'NO3', 'NO4->NO3')
            }
            self.areas = ('SE1', 'SE2', 'SE3', 'SE4', 'NO1', 'NO2', 'NO3', 'NO4', 'NO5', 'DK2', 'FI')

        def setup_problem(self):
            self.gm = gp.Model(name='LPModel')
            self.SET_AREAS = self.areas
            self.SET_ACLINKS = self.ac_links.keys()
            self.SET_SCENARIOS = list(range(self.PARAM_IMBALANCE.__len__()))
            self.VAR_TRANSMISSIONPOS = self.gm.addVars(self.SET_ACLINKS, self.SET_SCENARIOS, name='transmissionpos',
                                                       vtype=GRB.CONTINUOUS, lb=0, ub=float('inf'))
            self.VAR_TRANSMISSIONNEG = self.gm.addVars(self.SET_ACLINKS, self.SET_SCENARIOS, name='transmissionneg',
                                                       vtype=GRB.CONTINUOUS, lb=0, ub=float('inf'))
            self.VAR_ACTIVATIONUP = self.gm.addVars(self.SET_AREAS, self.SET_SCENARIOS, name='activationup',
                                                    vtype=GRB.CONTINUOUS, lb=0, ub=float('inf'))
            self.VAR_ACTIVATIONDOWN = self.gm.addVars(self.SET_AREAS, self.SET_SCENARIOS, name='activationdown',
                                                      vtype=GRB.CONTINUOUS, lb=0, ub=float('inf'))
            self.VAR_UNSERVEDPOS = self.gm.addVars(self.SET_AREAS, self.SET_SCENARIOS, name='unservedup',
                                                   vtype=GRB.CONTINUOUS, lb=0, ub=float('inf'))
            self.VAR_UNSERVEDNEG = self.gm.addVars(self.SET_AREAS, self.SET_SCENARIOS, name='unserveddown',
                                                   vtype=GRB.CONTINUOUS, lb=0, ub=float('inf'))

            print('SETTING UP LP PROBLEM')
            self.setup_objective()
            self.setup_transmission_pos()
            self.setup_transmission_neg()
            self.setup_power_balance()
            self.setup_activation_up()
            self.setup_activation_down()
            #self.setup_unserved_pos()
            #self.setup_unserved_neg()
            #self.gm.setParam('FeasibilityTol', 10 ** (-3))

        def setup_objective(self):
            self.obj = sum(self.VAR_UNSERVEDPOS[a, i] + self.VAR_UNSERVEDNEG[a, i] for a in self.SET_AREAS for i in
                           self.SET_SCENARIOS)
            self.obj += 10 ** (-3) * sum(
                self.VAR_TRANSMISSIONPOS[l, i] + self.VAR_TRANSMISSIONNEG[l, i] for l in self.SET_ACLINKS for i in
                self.SET_SCENARIOS)
            self.gm.setObjective(self.obj, sense=GRB.MINIMIZE)

        def setup_transmission_pos(self):
            self.CONSTR_TRANSMISSIONPOS = {}
            for l in self.SET_ACLINKS:
                for i in self.SET_SCENARIOS:
                    left_hand = self.VAR_TRANSMISSIONPOS[l, i]
                    right_hand = self.PARAM_ATCPOS[l][i]
                    self.CONSTR_TRANSMISSIONPOS[l, i] = self.gm.addLConstr(
                        lhs=left_hand,
                        sense=GRB.LESS_EQUAL,
                        rhs=right_hand,
                        name=f'TRANSMISSIONPOS[{l, i}]'
                    )

        def setup_transmission_neg(self):
            self.CONSTR_TRANSMISSIONNEG = {}
            for l in self.SET_ACLINKS:
                for i in self.SET_SCENARIOS:
                    left_hand = self.VAR_TRANSMISSIONNEG[l, i]
                    right_hand = self.PARAM_ATCNEG[l][i]
                    self.CONSTR_TRANSMISSIONNEG[l, i] = self.gm.addLConstr(
                        lhs=left_hand,
                        sense=GRB.LESS_EQUAL,
                        rhs=right_hand,
                        name=f'TRANSMISSIONPOS[{l, i}]'
                    )

        def setup_activation_up(self):
            self.CONSTR_ACTIVATIONUP = {}
            for a in self.SET_AREAS:
                for i in self.SET_SCENARIOS:
                    left_hand = self.VAR_ACTIVATIONUP[a, i]
                    right_hand = self.PARAM_RESERVEUP[a]
                    self.CONSTR_ACTIVATIONUP[a, i] = self.gm.addLConstr(
                        lhs=left_hand,
                        sense=GRB.LESS_EQUAL,
                        rhs=right_hand,
                        name=f'ACTIVATIONUP[{a, i}]'
                    )

        def setup_activation_down(self):
            self.CONSTR_ACTIVATIONDOWN = {}
            for a in self.SET_AREAS:
                for i in self.SET_SCENARIOS:
                    left_hand = self.VAR_ACTIVATIONDOWN[a, i]
                    right_hand = self.PARAM_RESERVEDOWN[a]
                    self.CONSTR_ACTIVATIONDOWN[a, i] = self.gm.addLConstr(
                        lhs=left_hand,
                        sense=GRB.LESS_EQUAL,
                        rhs=right_hand,
                        name=f'ACTIVATIONDOWN[{a, i}]'
                    )

        def setup_unserved_pos(self):
            self.CONSTR_UNSERVEDPOS = {}
            for a in self.SET_AREAS:
                for i in self.SET_SCENARIOS:
                    left_hand = self.VAR_UNSERVEDPOS[a, i]
                    right_hand = self.PARAM_BINARYPOS[i] * 10 ** 4
                    self.CONSTR_UNSERVEDPOS[a, i] = self.gm.addLConstr(
                        lhs=left_hand,
                        sense=GRB.LESS_EQUAL,
                        rhs=right_hand,
                        name=f'UNSERVEDPOS[{a, i}]'
                    )

        def setup_unserved_neg(self):
            self.CONSTR_UNSERVEDNEG = {}
            for a in self.SET_AREAS:
                for i in self.SET_SCENARIOS:
                    left_hand = self.VAR_UNSERVEDNEG[a, i]
                    right_hand = self.PARAM_BINARYNEG[i] * 10 ** 4
                    self.CONSTR_UNSERVEDNEG[a, i] = self.gm.addLConstr(
                        lhs=left_hand,
                        sense=GRB.LESS_EQUAL,
                        rhs=right_hand,
                        name=f'UNSERVEDNEG[{a, i}]'
                    )

        def setup_power_balance(self):
            self.CONSTR_POWERBALANCE = {}
            for a in self.SET_AREAS:
                imp_lines = []
                exp_lines = []
                for l in self.ac_links:
                    if self.ac_links[l][0] == a:
                        imp_lines.append(l)
                    elif self.ac_links[l][1] == a:
                        exp_lines.append(l)
                for i in self.SET_SCENARIOS:
                    left_hand = self.PARAM_IMBALANCE[a][i] + self.VAR_ACTIVATIONUP[a, i] - self.VAR_ACTIVATIONDOWN[
                        a, i] + \
                                self.VAR_UNSERVEDPOS[a, i] - self.VAR_UNSERVEDNEG[a, i]
                    right_hand = sum(
                        self.VAR_TRANSMISSIONPOS[l, i] - self.VAR_TRANSMISSIONNEG[l, i] for l in exp_lines) - \
                                 sum(self.VAR_TRANSMISSIONPOS[l, i] - self.VAR_TRANSMISSIONNEG[l, i] for l in
                                     imp_lines)
                    self.CONSTR_POWERBALANCE[a, i] = self.gm.addLConstr(
                        lhs=left_hand,
                        sense=GRB.EQUAL,
                        rhs=right_hand,
                        name=f'POWERBALANCE[{a, i}]'
                    )

    def run(self):
        m = self.MIP(atc=self.atc, num_RI=self.num_RI, epsilon=self.epsilon, vertex_sets=self.vertex_sets)
        st_tot = time.time()
        m.setup_problem()
        m.gm.optimize()
        et_tot = time.time()
        print(f'SOLVED FIRST PROBLEM IN {round(et_tot - st_tot, 0)} SECONDS')
        reserve_up = {}
        reserve_down = {}
        for a in m.SET_AREAS:
            reserve_up[a] = m.VAR_RESERVECAPUP[a].X
            reserve_down[a] = m.VAR_RESERVECAPDOWN[a].X
        binary_pos = [m.VAR_VIOLATION_POS[i].X for i in m.SET_SCENARIOS]
        binary_neg = [m.VAR_VIOLATION_NEG[i].X for i in m.SET_SCENARIOS]
        st_tot2 = time.time()
        m2 = self.LP(atc_pos=m.PARAM_ATC_POS, atc_neg=m.PARAM_ATC_NEG, imbalance=m.PARAM_IMBALANCES_DIST,
                reserve_up=reserve_up,
                reserve_down=reserve_down, binary_pos=binary_pos, binary_neg=binary_neg)
        m2.setup_problem()
        m2.gm.optimize()
        et_tot2 = time.time()
        print(f'SOLVED SECOND PROBLEM IN {round(et_tot2 - st_tot2, 0)} SECONDS')

        # for a in m.SET_AREAS:
        #     print(f'PRE UPWARD CAPACITY {a}: {round(m.VAR_RESERVECAPUP[a].X, 1)} MW')
        #     print(f'POST UPWARD CAPACITY {a}: {round(m2.VAR_RESERVECAPUP[a].X, 1)} MW')
        #     print(f'PRE DOWNWARD CAPACITY {a}: {round(m.VAR_RESERVECAPDOWN[a].X, 1)} MW')
        #     print(f'POST DOWNWARD CAPACITY {a}: {round(m2.VAR_RESERVECAPDOWN[a].X, 1)} MW')

        #print('\n')
        #print(f'PRE TOTAL UPWARD CAPACITY: {round(sum(m.VAR_RESERVECAPUP[a].X for a in m.SET_AREAS), 1)} MW')
        print(f'TOTAL UPWARD CAPACITY: {round(sum(m.VAR_RESERVECAPUP[a].X for a in m.SET_AREAS), 1)} MW')
        #print(f'PRE TOTAL DOWNWARD CAPACITY: {round(sum(m.VAR_RESERVECAPDOWN[a].X for a in m.SET_AREAS), 1)} MW')
        print(f'TOTAL DOWNWARD CAPACITY: {round(sum(m.VAR_RESERVECAPDOWN[a].X for a in m.SET_AREAS), 1)} MW')
        print(f'UPWARD RELIABILITY: {round(100 - 100 * sum(m.VAR_VIOLATION_POS[i].X for i in m.SET_SCENARIOS) / m.SET_SCENARIOS.__len__(), 2)} %')
        print(f'DOWNWARD RELIABILITY: {round(100 - 100 * sum(m.VAR_VIOLATION_NEG[i].X for i in m.SET_SCENARIOS) / m.SET_SCENARIOS.__len__(), 2)} %')

        print(f'TOTAL TIME: {round(et_tot2 - st_tot, 0)} SECONDS')
        self.results = {
            'Up activation': pd.DataFrame(columns=m2.SET_AREAS, index=list(range(self.atc.__len__()))),
            'Down activation': pd.DataFrame(columns=m2.SET_AREAS, index=list(range(self.atc.__len__()))),
            'Unserved up': pd.DataFrame(columns=m2.SET_AREAS, index=list(range(self.atc.__len__()))),
            'Unserved down': pd.DataFrame(columns=m2.SET_AREAS, index=list(range(self.atc.__len__()))),
            'Up capacity': pd.DataFrame(columns=m2.SET_AREAS, index=[0]),
            'Down capacity': pd.DataFrame(columns=m2.SET_AREAS, index=[0]),
            'Transmission': pd.DataFrame(columns=m2.SET_ACLINKS, index=list(range(self.atc.__len__()))),
            'ATC positive': pd.DataFrame(columns=m2.SET_ACLINKS, index=list(range(self.atc.__len__()))),
            'ATC negative': pd.DataFrame(columns=m2.SET_ACLINKS, index=list(range(self.atc.__len__()))),
        }
        for a in m2.SET_AREAS:
            self.results['Up capacity'][a][0] = m.VAR_RESERVECAPUP[a].X
            self.results['Down capacity'][a][0] = m.VAR_RESERVECAPDOWN[a].X

        ## worst_case identifier
        ### Worst case identification, find the RI-scenario with largest difference between ATC in directions
        flow_tot = [sum(abs(m2.VAR_TRANSMISSIONPOS[l,t].X - m2.VAR_TRANSMISSIONNEG[l,t].X) for l in m2.SET_ACLINKS) for t in m2.SET_SCENARIOS]
        flow_tot = pd.Series(flow_tot)
        worst_case_idxs = []
        for hour in range(self.atc.__len__()):
            worst_case_idxs.append(flow_tot[hour * self.num_RI: (hour + 1) * self.num_RI - 1].idxmax())

        for a in m2.SET_AREAS:
            self.results['Up activation'][a] = [m2.VAR_ACTIVATIONUP[a, w].X for w in worst_case_idxs]
            self.results['Down activation'][a] = [m2.VAR_ACTIVATIONDOWN[a, w].X for w in worst_case_idxs]
            self.results['Unserved up'][a] = [m2.VAR_UNSERVEDPOS[a, w].X for w in worst_case_idxs]
            self.results['Unserved down'][a] = [m2.VAR_UNSERVEDNEG[a, w].X for w in worst_case_idxs]
        for l in m2.SET_ACLINKS:
            self.results['Transmission'][l] = [m2.VAR_TRANSMISSIONPOS[l, w].X - m2.VAR_TRANSMISSIONNEG[l, w].X
                                               for w in worst_case_idxs]
        for l in m2.SET_ACLINKS:
            self.results['ATC positive'][l] = m.atc_pos[l] - self.results['Transmission'][l]
            self.results['ATC negative'][l] = m.atc_neg[l] + self.results['Transmission'][l]
        return self.results

