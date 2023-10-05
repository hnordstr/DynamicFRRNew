import gurobipy as gp
from gurobipy import GRB
import subprocess
import pandas as pd
import random
import math
import numpy as np
import csv
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import pickle as pkl
import time

### Read ATC data
with open('ATC.pickle', 'rb') as handle:
    atc_in = pkl.load(handle)
date = datetime.strptime('2019-12-29', '%Y-%m-%d')  #
num_scenarios = 15
num_RI = 22
dates = []
for n in range(1, num_scenarios + 1):
    dates.append(date - timedelta(days=n))
hours = []
for d in dates:
    hours.extend([d + timedelta(hours=x) for x in range(24)])
hours.sort()
hours_str = [datetime.strftime(h, '%Y-%m-%d %H:%M:%S+00:00') for h in hours]
atc = atc_in[atc_in.index.isin(hours_str)]


class MIP:
    """This is the class Optimization model that will be assigned all functions needed to solve our problem,
    a class is an object with multiple attributes and functions. When referencing any attributes/functions
    within the class, they must be referenced with self"""

    def __init__(self, atc, num_RI, epsilon):
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

        self.RI = (('SE1', 'up', 800),
                   ('SE2', 'up', 600),
                   ('SE3', 'up', 1450),
                   ('SE4', 'up', 1000),
                   ('NO1', 'up', 1450),
                   ('NO2', 'up', 1400),
                   ('NO3', 'up', 1000),
                   ('NO4', 'up', 650),
                   ('NO5', 'up', 700),
                   ('DK2', 'up', 600),
                   ('FI', 'up', 1300),
                   ('SE1', 'down', -1100),
                   ('SE2', 'down', -1000),
                   ('SE3', 'down', -1350),
                   ('SE4', 'down', -700),
                   ('NO1', 'down', -1450),
                   ('NO2', 'down', -1400),
                   ('NO3', 'down', -600),
                   ('NO4', 'down', -800),
                   ('NO5', 'down', -1400),
                   ('DK2', 'down', -600),
                   ('FI', 'down', -800)
                   )
        self.epsilon = epsilon

        #self.gm = gp.Model()
        self.atc_pos = pd.DataFrame(columns=self.ac_links.keys(), index=atc.index)
        self.atc_neg = pd.DataFrame(columns=self.ac_links.keys(), index=atc.index)
        for l in self.ac_links.keys():
            self.atc_pos[l] = atc[l]
            self.atc_neg[l] = atc[self.ac_links[l][2]]

    def setup_linked_vertex_sets(self):
        V_SEL = ['SE1']
        E_SEL = []
        self.VERTEXSETS = [['SE1']]
        E_LIST = list(self.ac_links.keys())
        while E_SEL != E_LIST:
            for l in E_LIST:
                if l not in E_SEL:
                    if self.ac_links[l][0] in V_SEL or self.ac_links[l][1] in V_SEL:
                        E_PICK = l
                        E_SEL.append(E_PICK)
                        break
                    else:
                        pass
                else:
                    pass
            if self.ac_links[E_PICK][0] in V_SEL and self.ac_links[E_PICK][1] in V_SEL:
                W_V = []
                W_W = []
                for n in self.VERTEXSETS:
                    if self.ac_links[E_PICK][0] in n:
                        W_V.append(n)
                    if self.ac_links[E_PICK][1] in n:
                        W_W.append(n)
                for S1 in W_V:
                    for S2 in W_W:
                        lst = []
                        lst.extend(S1)
                        for n in S2:
                            if n not in lst:
                                lst.append(n)
                                lst = sorted(lst)
                        if lst not in self.VERTEXSETS:
                            self.VERTEXSETS.append(sorted(lst))
            else:
                if self.ac_links[E_PICK][0] in V_SEL:
                    v = self.ac_links[E_PICK][0]
                    w = self.ac_links[E_PICK][1]
                elif self.ac_links[E_PICK][1] in V_SEL:
                    v = self.ac_links[E_PICK][1]
                    w = self.ac_links[E_PICK][0]
                self.VERTEXSETS.append([w])
                V_SEL.append(w)
                W_V = []
                for n in self.VERTEXSETS:
                    if v in n:
                        W_V.append(n)
                for S in W_V:
                    lst = []
                    lst.extend(S)
                    lst.append(w)
                    lst = sorted(lst)
                    if lst not in self.VERTEXSETS:
                        self.VERTEXSETS.append(sorted(lst))

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
        h_pos = h_pos['Value'].tolist()[:q+1]
        h_neg = h_neg['Value'].tolist()[:q+1]
        return h_pos, h_neg, sigma_pos, sigma_neg

    def setup_problem(self):
        print('SETTING UP VERTEX SETS')
        self.setup_linked_vertex_sets()
        self.SET_ACLINKS = self.ac_links.keys()
        self.SET_AREAS = self.areas
        self.PARAM_EPSILON = self.epsilon
        self.SET_SCENARIOS = range(self.atc_pos.__len__() * self.num_RI)
        self.SET_SCENARIOS_imb = range(len(self.RI))
        self.SET_VERTEXSETS = range(self.VERTEXSETS.__len__())
        self.PARAM_IMBALANCES_DIST = pd.DataFrame(columns=self.areas, index=self.SET_SCENARIOS)
        self.Q = math.floor(self.SET_SCENARIOS.__len__() * self.PARAM_EPSILON)
        self.SET_Q = list(range(self.Q))

        ### Generate random matrix with RI
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
            self.PARAM_ATC_POS[l] = [self.atc_pos[l][h] for h in self.atc_pos.index.tolist() for x in range(self.num_RI)]
            self.PARAM_ATC_NEG[l] = [self.atc_neg[l][h] for h in self.atc_neg.index.tolist() for x in range(self.num_RI)]

        print('COMPUTING H-VALUES')
        st = time.time()
        self.PARAM_HPOS = {}
        self.PARAM_HNEG = {}
        self.SET_SIGMAPOS = {}
        self.SET_SIGMANEG = {}
        for i in range(self.VERTEXSETS.__len__()):
            self.PARAM_HPOS[i], self.PARAM_HNEG[i], self.SET_SIGMAPOS[i], self.SET_SIGMANEG[i] = \
                self.compute_h(vertex_set=self.VERTEXSETS[i],
                            imbalance=self.PARAM_IMBALANCES_DIST, atc_pos=self.PARAM_ATC_POS,
                                                                    atc_neg=self.PARAM_ATC_NEG, q=self.Q)
        et = time.time()
        print(f'COMPUTED H-VALUES IN {round(et-st, 0)} SECONDS')


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
        print('SETTING UP PROBLEM')
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

    def setup_objective(self):
        self.obj = sum(self.VAR_RESERVECAPUP[a] + self.VAR_RESERVECAPDOWN[a] for a in self.SET_AREAS)
        self.gm.setObjective(self.obj, sense=GRB.MINIMIZE)

    def setup_reserve_constraint_up(self):
        self.CONSTR_RESERVE_UP = {}
        for s in self.SET_VERTEXSETS:
            left_hand = sum(self.VAR_RESERVECAPUP[a] for a in self.VERTEXSETS[s])
            left_hand += sum((self.PARAM_HPOS[s][i] - self.PARAM_HPOS[s][i + 1]) * self.VAR_OMEGAPOS[s,i] for i in self.SET_Q)
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
            left_hand += sum((self.PARAM_HNEG[s][i] - self.PARAM_HNEG[s][i + 1]) * self.VAR_OMEGANEG[s,i] for i in self.SET_Q)
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
                left_hand = self.VAR_OMEGAPOS[s,i] - self.VAR_OMEGAPOS[s,i+1]
                right_hand = 0
                self.CONSTR_BINARY_UP1[s,i] = self.gm.addLConstr(
                    lhs=left_hand,
                    sense=GRB.GREATER_EQUAL,
                    rhs=right_hand,
                    name=f'BINARYUP1[{s,i}]'
                )

    def setup_binary_down1(self):
        self.CONSTR_BINARY_DOWN1 = {}
        for s in self.SET_VERTEXSETS:
            for i in range(self.Q - 1):
                left_hand = self.VAR_OMEGANEG[s,i] - self.VAR_OMEGANEG[s,i+1]
                right_hand = 0
                self.CONSTR_BINARY_DOWN1[s,i] = self.gm.addLConstr(
                    lhs=left_hand,
                    sense=GRB.GREATER_EQUAL,
                    rhs=right_hand,
                    name=f'BINARYDOWN1[{s,i}]'
                )

    def setup_binary_up2(self):
        self.CONSTR_BINARY_UP2 = {}
        for s in self.SET_VERTEXSETS:
            for i in range(self.Q):
                left_hand = self.VAR_VIOLATION_POS[self.SET_SIGMAPOS[s][i]] - self.VAR_OMEGAPOS[s,i]
                right_hand = 0
                self.CONSTR_BINARY_UP2[s,i] = self.gm.addLConstr(
                    lhs=left_hand,
                    sense=GRB.GREATER_EQUAL,
                    rhs=right_hand,
                    name=f'BINARYUP2[{s,i}]'
                )

    def setup_binary_down2(self):
        self.CONSTR_BINARY_DOWN2 = {}
        for s in self.SET_VERTEXSETS:
            for i in range(self.Q):
                left_hand = self.VAR_VIOLATION_NEG[self.SET_SIGMANEG[s][i]] - self.VAR_OMEGANEG[s,i]
                right_hand = 0
                self.CONSTR_BINARY_DOWN2[s,i] = self.gm.addLConstr(
                    lhs=left_hand,
                    sense=GRB.GREATER_EQUAL,
                    rhs=right_hand,
                    name=f'BINARYDOWN2[{s,i}]'
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
        self.PARAM_RESERVEUPTOT = reserve_up
        self.PARAM_RESERVEDOWNTOT = reserve_down
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

        self.VAR_RESERVECAPUP = self.gm.addVars(self.SET_AREAS, name='reservecapacityup', vtype=GRB.CONTINUOUS,
                                                  lb=0, ub=float('inf'))
        self.VAR_RESERVECAPDOWN = self.gm.addVars(self.SET_AREAS, name='reservecapacitydown', vtype=GRB.CONTINUOUS,
                                                  lb=0, ub=float('inf'))
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
        self.setup_unserved_pos()
        self.setup_unserved_neg()
        self.setup_reserve_up()
        self.setup_reserve_down()

    def setup_objective(self):
        self.obj = sum(self.VAR_UNSERVEDPOS[a,i] + self.VAR_UNSERVEDNEG[a,i] for a in self.SET_AREAS for i in self.SET_SCENARIOS)
        self.obj += 10**(-3) * sum(self.VAR_TRANSMISSIONPOS[l,i] + self.VAR_TRANSMISSIONNEG[l,i] for l in self.SET_ACLINKS for i in self.SET_SCENARIOS)
        self.gm.setObjective(self.obj, sense=GRB.MINIMIZE)

    def setup_transmission_pos(self):
        self.CONSTR_TRANSMISSIONPOS = {}
        for l in self.SET_ACLINKS:
            for i in self.SET_SCENARIOS:
                left_hand = self.VAR_TRANSMISSIONPOS[l,i]
                right_hand = self.PARAM_ATCPOS[l][i]
                self.CONSTR_TRANSMISSIONPOS[l,i] = self.gm.addLConstr(
                    lhs=left_hand,
                    sense=GRB.LESS_EQUAL,
                    rhs=right_hand,
                    name=f'TRANSMISSIONPOS[{l,i}]'
                )

    def setup_transmission_neg(self):
        self.CONSTR_TRANSMISSIONNEG = {}
        for l in self.SET_ACLINKS:
            for i in self.SET_SCENARIOS:
                left_hand = self.VAR_TRANSMISSIONNEG[l,i]
                right_hand = self.PARAM_ATCNEG[l][i]
                self.CONSTR_TRANSMISSIONNEG[l,i] = self.gm.addLConstr(
                    lhs=left_hand,
                    sense=GRB.LESS_EQUAL,
                    rhs=right_hand,
                    name=f'TRANSMISSIONPOS[{l,i}]'
                )

    def setup_activation_up(self):
        self.CONSTR_ACTIVATIONUP = {}
        for a in self.SET_AREAS:
            for i in self.SET_SCENARIOS:
                left_hand = self.VAR_ACTIVATIONUP[a,i]
                right_hand = self.VAR_RESERVECAPUP[a]
                self.CONSTR_ACTIVATIONUP[a,i] = self.gm.addLConstr(
                    lhs=left_hand,
                    sense=GRB.LESS_EQUAL,
                    rhs=right_hand,
                    name=f'ACTIVATIONUP[{a,i}]'
                )

    def setup_activation_down(self):
        self.CONSTR_ACTIVATIONDOWN = {}
        for a in self.SET_AREAS:
            for i in self.SET_SCENARIOS:
                left_hand = self.VAR_ACTIVATIONDOWN[a,i]
                right_hand = self.VAR_RESERVECAPDOWN[a]
                self.CONSTR_ACTIVATIONDOWN[a,i] = self.gm.addLConstr(
                    lhs=left_hand,
                    sense=GRB.LESS_EQUAL,
                    rhs=right_hand,
                    name=f'ACTIVATIONDOWN[{a,i}]'
                )

    def setup_unserved_pos(self):
        self.CONSTR_UNSERVEDPOS = {}
        for a in self.SET_AREAS:
            for i in self.SET_SCENARIOS:
                left_hand = self.VAR_UNSERVEDPOS[a,i]
                right_hand = self.PARAM_BINARYPOS[i] * 10**4
                self.CONSTR_UNSERVEDPOS[a,i] = self.gm.addLConstr(
                    lhs=left_hand,
                    sense=GRB.LESS_EQUAL,
                    rhs=right_hand,
                    name=f'UNSERVEDPOS[{a,i}]'
                )

    def setup_unserved_neg(self):
        self.CONSTR_UNSERVEDNEG = {}
        for a in self.SET_AREAS:
            for i in self.SET_SCENARIOS:
                left_hand = self.VAR_UNSERVEDNEG[a,i]
                right_hand = self.PARAM_BINARYNEG[i] * 10**4
                self.CONSTR_UNSERVEDNEG[a,i] = self.gm.addLConstr(
                    lhs=left_hand,
                    sense=GRB.LESS_EQUAL,
                    rhs=right_hand,
                    name=f'UNSERVEDNEG[{a,i}]'
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
                left_hand = self.PARAM_IMBALANCE[a][i] + self.VAR_ACTIVATIONUP[a,i] - self.VAR_ACTIVATIONDOWN[a,i] + \
                            self.VAR_UNSERVEDPOS[a,i] - self.VAR_UNSERVEDNEG[a,i]
                right_hand = sum(self.VAR_TRANSMISSIONPOS[l,i] - self.VAR_TRANSMISSIONNEG[l,i] for l in exp_lines) - \
                             sum(self.VAR_TRANSMISSIONPOS[l,i] - self.VAR_TRANSMISSIONNEG[l,i] for l in imp_lines)
                self.CONSTR_POWERBALANCE[a,i] = self.gm.addLConstr(
                    lhs=left_hand,
                    sense=GRB.EQUAL,
                    rhs=right_hand,
                    name=f'POWERBALANCE[{a,i}]'
                )

    def setup_reserve_up(self):
        left_hand = sum(self.VAR_RESERVECAPUP[a] for a in self.SET_AREAS)
        right_hand = self.PARAM_RESERVEUPTOT
        self.CONSTR_RESERVEUP = self.gm.addLConstr(
            lhs=left_hand,
            sense=GRB.LESS_EQUAL,
            rhs=right_hand,
            name=f'RESERVEUP'
        )

    def setup_reserve_down(self):
        left_hand = sum(self.VAR_RESERVECAPDOWN[a] for a in self.SET_AREAS)
        right_hand = self.PARAM_RESERVEDOWNTOT
        self.CONSTR_RESERVEDOWN = self.gm.addLConstr(
            lhs=left_hand,
            sense=GRB.LESS_EQUAL,
            rhs=right_hand,
            name=f'RESERVEDOWN'
        )

m = MIP(atc=atc, num_RI=num_RI,epsilon=0.01)
st_tot = time.time()
m.setup_problem()
print('SOLVING OPTIMIZATION PROBLEM')
st_solve = time.time()
m.gm.optimize()
et_tot = time.time()
print(f'SOLVED FIRST PROBLEM IN {round(et_tot - st_tot, 0)} SECONDS')
print(f'UPWARD RELIABILITY: {round(100 - 100 * sum(m.VAR_VIOLATION_POS[i].X for i in m.SET_SCENARIOS) / m.SET_SCENARIOS.__len__(), 2)} %')
print(f'DOWNWARD RELIABILITY: {round(100 - 100 * sum(m.VAR_VIOLATION_NEG[i].X for i in m.SET_SCENARIOS) / m.SET_SCENARIOS.__len__(), 2)} %')
reserve_up = sum(m.VAR_RESERVECAPUP[a].X for a in m.SET_AREAS)
reserve_down = sum(m.VAR_RESERVECAPDOWN[a].X for a in m.SET_AREAS)
binary_pos = [m.VAR_VIOLATION_POS[i].X for i in m.SET_SCENARIOS]
binary_neg = [m.VAR_VIOLATION_NEG[i].X for i in m.SET_SCENARIOS]


st_tot2 = time.time()
m2 = LP(atc_pos=m.PARAM_ATC_POS, atc_neg=m.PARAM_ATC_NEG, imbalance=m.PARAM_IMBALANCES_DIST, reserve_up=reserve_up,
        reserve_down=reserve_down, binary_pos=binary_pos, binary_neg=binary_neg)
m2.setup_problem()
m2.gm.optimize()
et_tot2 = time.time()
print(f'SOLVED SECOND PROBLEM IN {round(et_tot2 - st_tot2, 0)} SECONDS')

for a in m.SET_AREAS:
    print(f'PRE UPWARD CAPACITY {a}: {round(m.VAR_RESERVECAPUP[a].X, 1)} MW')
    print(f'POST UPWARD CAPACITY {a}: {round(m2.VAR_RESERVECAPUP[a].X,1)} MW')
    print(f'PRE DOWNWARD CAPACITY {a}: {round(m.VAR_RESERVECAPDOWN[a].X,1)} MW')
    print(f'POST DOWNWARD CAPACITY {a}: {round(m2.VAR_RESERVECAPDOWN[a].X,1)} MW')

print('\n')
print(f'PRE TOTAL UPWARD CAPACITY: {round(sum(m.VAR_RESERVECAPUP[a].X for a in m.SET_AREAS) ,1)} MW')
print(f'POST TOTAL UPWARD CAPACITY: {round(sum(m2.VAR_RESERVECAPUP[a].X for a in m.SET_AREAS) ,1)} MW')
print(f'PRE TOTAL DOWNWARD CAPACITY: {round(sum(m.VAR_RESERVECAPDOWN[a].X for a in m.SET_AREAS) ,1)} MW')
print(f'POST TOTAL DOWNWARD CAPACITY: {round(sum(m2.VAR_RESERVECAPDOWN[a].X for a in m.SET_AREAS) ,1)} MW')

print(f'TOTAL TIME: {round(et_tot2 - st_tot, 0)} SECONDS')

