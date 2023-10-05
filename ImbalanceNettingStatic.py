import gurobipy as gp
from gurobipy import GRB
from gurobipy import *
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

"""Takes hourly post-RI ATC (indexed 0-N) and extends to minute resolution
Reads stochastic + deterministic imbalances
Needs to be fed time index of atc
Example run: imbalance, atc = GurobiModel(atc=df_atc, time=time_idx_list).run()
"""
class GurobiModel:

    def __init__(self, atc_pos, atc_neg, time, name=''):
        #with gp.Env(empty=True) as env:
        #    env.setParam('OutputFlag', 0)
        #    env.start()
        #    self.gm = gp.Model(name, env=env)
        self.name = name
        self.path = f'C:\\Users\\hnordstr\\OneDrive - KTH\\box_files\\KTH\\Papers&Projects\\DynamicFRR\\Normal Imbalances\\Scenario1\\' #Minute normal imbalances
        self.areas = ('SE1', 'SE2', 'SE3', 'SE4', 'NO1', 'NO2', 'NO3', 'NO4', 'NO5', 'DK2', 'FI')
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


        self.ac_indx = self.ac_links.keys()
        self.time = time
        self.atc_pos = atc_pos
        self.atc_neg = atc_neg

        print('READING INPUT FILES')
        ###IMBALANCES###
        self.stochastic = pd.read_csv(f'{self.path}stochastic_prenet.csv', index_col=[0])
        self.deterministic = pd.read_csv(f'{self.path}deterministic_prenet.csv', index_col=[0])
        ###PARAMETERS###
        self.set_time = list(range(self.time.__len__() * 60))
        self.param_STOCHASTIC_IMBALANCE = pd.DataFrame(columns=self.areas, index=self.set_time)
        self.param_DETERMINISTIC_IMBALANCE = pd.DataFrame(columns=self.areas, index=self.set_time)
        self.param_ATC_POS = pd.DataFrame(columns=self.ac_indx, index=self.set_time)
        self.param_ATC_NEG = pd.DataFrame(columns=self.ac_indx, index=self.set_time)

        for l in self.ac_indx:
            self.param_ATC_POS[l] = [self.atc_pos[l][i] for i in range(self.atc_pos.__len__()) for x in
                                     range(60)]
            self.param_ATC_NEG[l] = [self.atc_neg[l][i] for i in range(self.atc_neg.__len__()) for x in
                                     range(60)]
        for a in self.areas:
            sto_list = []
            det_list = []
            for t in self.time:
                sto_list.extend(self.stochastic[a][datetime.strftime(t, '%Y-%m-%d %H:%M:%S+00:00'):
                                                   datetime.strftime(t + timedelta(minutes=59),
                                                                     '%Y-%m-%d %H:%M:%S+00:00')].values)
                det_list.extend(self.deterministic[a][datetime.strftime(t, '%Y-%m-%d %H:%M:%S+00:00'):
                                                      datetime.strftime(t + timedelta(minutes=59),
                                                                        '%Y-%m-%d %H:%M:%S+00:00')].values)
            self.param_STOCHASTIC_IMBALANCE[a] = sto_list
            self.param_DETERMINISTIC_IMBALANCE[a] = det_list

    def setup_problem(self, time_set):
        self.gm = gp.Model('name')

        print('SETTING UP VARIABLES')
        ###SETS###
        self.set_TIME = time_set #Fl
        self.set_INTERVALS = time_set[:-1]
        self.set_AREAS = self.areas
        self.set_ACLINES = self.ac_links
        self.set_ACINDX = self.ac_indx
        self.set_IMPORT_LINES = {}
        self.set_EXPORT_LINES = {}
        for a in self.set_AREAS:
            self.set_IMPORT_LINES[a] = [l for l in self.ac_links.keys() if self.ac_links[l][0] == a]
            self.set_EXPORT_LINES[a] = [l for l in self.ac_links.keys() if self.ac_links[l][1] == a]

        ###VARIABLES###
        self.var_AC_POS = self.gm.addVars(self.set_ACINDX, self.set_TIME, name='AC', vtype=GRB.CONTINUOUS, lb=0, ub=float('inf'))
        self.var_AC_NEG = self.gm.addVars(self.set_ACINDX, self.set_TIME, name='AC', vtype=GRB.CONTINUOUS, lb=0, ub=float('inf'))
        self.var_IMBALANCE_POS = self.gm.addVars(self.set_AREAS, self.set_TIME, name='BALUP', vtype=GRB.CONTINUOUS, lb=0, ub=float('inf'))
        self.var_IMBALANCE_NEG = self.gm.addVars(self.set_AREAS, self.set_TIME, name='BALDOWN', vtype=GRB.CONTINUOUS, lb=0, ub=float('inf'))
        self.var_IMBDIFF_POS = self.gm.addVars(self.set_AREAS, self.set_INTERVALS, name='IMBDIFFPOS', vtype=GRB.CONTINUOUS,
                                                 lb=0, ub=float('inf'))
        self.var_IMBDIFF_NEG = self.gm.addVars(self.set_AREAS, self.set_INTERVALS, name='IMBDIFFNEG', vtype=GRB.CONTINUOUS,
                                                 lb=0, ub=float('inf'))


        ###OPTIMIZATION PROBLEM###
        self.setup_objective()
        self.setup_transmission_constr_pos()
        self.setup_transmission_constr_neg()
        self.setup_imbdiffpos()
        self.setup_imbdiffneg()
        self.setup_balance_constr()
        self.gm.update()

    def setup_objective(self):
        print('SETTING UP OBJECTIVE FUNCTION')
        obj = sum(self.var_IMBALANCE_POS[a,t] + self.var_IMBALANCE_NEG[a,t] for a in self.set_AREAS for t in self.set_TIME)
        obj += 10**(-5) * sum(self.var_AC_POS[l,t] + self.var_AC_NEG[l,t] for l in self.set_ACINDX
                              for t in self.set_TIME)
        obj += 10**(-8) * sum(self.var_IMBDIFF_POS[a,t] + self.var_IMBDIFF_NEG[a,t] for a in self.set_AREAS
                              for t in self.set_INTERVALS)
        self.gm.setObjective(obj, sense=GRB.MINIMIZE)

    def setup_transmission_constr_pos(self):
        print('SETTING UP TRANSMISSION CONSTRAINTS')
        self.constr_ACMAXPOS = {}
        for l in self.set_ACINDX:
            for t in self.set_TIME:
                left_hand = self.var_AC_POS[l,t]
                right_hand = self.param_ATC_POS[l][t]
                self.constr_ACMAXPOS[l,t] = self.gm.addLConstr(
                    lhs = left_hand,
                    sense = GRB.LESS_EQUAL,
                    rhs = right_hand,
                    name = f'ACMAXPOS[{l,t}]'
                )

    def setup_transmission_constr_neg(self):
        self.constr_ACMAXNEG = {}
        for l in self.set_ACINDX:
            for t in self.set_TIME:
                left_hand = self.var_AC_NEG[l,t]
                right_hand = self.param_ATC_NEG[l][t]
                self.constr_ACMAXNEG[l,t] = self.gm.addLConstr(
                    lhs = left_hand,
                    sense = GRB.LESS_EQUAL,
                    rhs = right_hand,
                    name = f'ACMAXNEG[{l,t}]'
                )

    def setup_imbdiffpos(self):
        print('SETTING UP IMBALANCE DIFF CONSTRAINT 1')
        self.constr_IMBDIFFPOS = {}
        for a in self.set_AREAS:
            for i in self.set_INTERVALS:
                left_hand = (self.var_IMBALANCE_POS[a, i + 1] - self.var_IMBALANCE_NEG[a, i + 1]) - \
                (self.var_IMBALANCE_POS[a, i] - self.var_IMBALANCE_NEG[a, i])
                right_hand = self.var_IMBDIFF_POS[a, i]
                self.constr_IMBDIFFPOS[a, i] = self.gm.addLConstr(
                    lhs = left_hand,
                    sense = GRB.LESS_EQUAL,
                    rhs = right_hand,
                    name = f'IMBDIFFPOS[{a, i}]'
                )

    def setup_imbdiffneg(self):
        print('SETTING UP IMBALANCE DIFF CONSTRAINT 2')
        self.constr_IMBDIFFNEG = {}
        for a in self.set_AREAS:
            for i in self.set_INTERVALS:
                left_hand = (self.var_IMBALANCE_POS[a, i] - self.var_IMBALANCE_NEG[a, i]) - \
                (self.var_IMBALANCE_POS[a, i] - self.var_IMBALANCE_NEG[a, i])
                right_hand = self.var_IMBDIFF_NEG[a, i]
                self.constr_IMBDIFFNEG[a, i] = self.gm.addLConstr(
                    lhs = left_hand,
                    sense = GRB.LESS_EQUAL,
                    rhs = right_hand,
                    name = f'IMBDIFFNEG[{a, i}]'
                )

    def setup_balance_constr(self):
        print('SETTING UP BALANCE CONSTRAINTS')
        self.constr_balance = {}
        for a in self.set_AREAS:
            for t in self.set_TIME:
                left_hand = self.param_STOCHASTIC_IMBALANCE[a][t] + self.param_DETERMINISTIC_IMBALANCE[a][t] \
                            + self.var_IMBALANCE_NEG[a,t] - self.var_IMBALANCE_POS[a,t]
                right_hand = 0
                for l in self.set_IMPORT_LINES[a]:
                    left_hand = left_hand + self.var_AC_POS[l, t] - self.var_AC_NEG[l, t]
                for l in self.set_EXPORT_LINES[a]:
                    left_hand = left_hand - self.var_AC_POS[l, t] + self.var_AC_NEG[l, t]
                self.constr_balance[a, t] = self.gm.addLConstr(
                    lhs = left_hand,
                    sense = GRB.EQUAL,
                    rhs = right_hand,
                    name = f'BALANCE[{a, t}]'
                )

    def run(self):
        self.ac = pd.DataFrame(index=self.set_time, columns=self.ac_indx)
        self.atc_pos = pd.DataFrame(index=self.set_time, columns=self.ac_indx)
        self.atc_neg = pd.DataFrame(index=self.set_time, columns=self.ac_indx)
        self.imbalance = pd.DataFrame(index=self.set_time, columns=self.areas)
        period_length = 30 * 60 * 24
        nperiods = np.ceil(self.param_ATC_POS.__len__() / period_length)
        periods = list(range(int(nperiods)))
        imb_list = {}
        ac_list = {}
        for a in self.areas:
            imb_list[a] = []
        for l in self.ac_indx:
            ac_list[l] = []
        for p in periods:
            if p == nperiods - 1:
                idx_range = list(range(p * period_length, self.param_ATC_POS.__len__()))
            else:
                idx_range = list(range(p * period_length, (p + 1) * period_length))
            print(f'SETTING UP IMBALANCE NETTING OPTIMIZATION PERIOD {p + 1}')
            self.setup_problem(time_set=idx_range)
            print(f'SOLVING OPTIMIZATION PROBLEM PERIOD {p + 1}')
            self.gm.optimize()
            for a in self.areas:
                imb_list[a].extend([self.var_IMBALANCE_POS[a, t].X - self.var_IMBALANCE_NEG[a, t].X
                                    for t in idx_range])
            for l in self.ac_indx:
                ac_list[l].extend([self.var_AC_POS[l, t].X - self.var_AC_NEG[l, t].X for t in idx_range])
        for a in self.areas:
            self.imbalance[a] = imb_list[a]
        for l in self.ac_indx:
            self.ac[l] = ac_list[l]
        for l in self.ac_indx:
            self.atc_pos[l] = self.param_ATC_POS[l] - self.ac[l]
            self.atc_neg[l] = self.param_ATC_NEG[l] + self.ac[l]

        return self.param_STOCHASTIC_IMBALANCE, self.param_DETERMINISTIC_IMBALANCE, self.imbalance, self.atc_pos, self.atc_neg, self.ac