import gurobipy as gp
from gurobipy import GRB
from gurobipy import *
import pandas as pd
from datetime import datetime, timedelta



"""Takes hourly post-RI ATC (indexed 0-N) and extends to minute resolution
Reads stochastic + deterministic imbalances
Needs to be date in format year-month-date + number of scenarios
Example run: imbalance, atc = GurobiModel(date='2019-01-01', scenarios=20, atc=df_atc).run()
"""
class GurobiModel:

    def __init__(self, date, scenarios, atc_pos, atc_neg, name=''):
        #with gp.Env(empty=True) as env:
        #    env.setParam('OutputFlag', 0)
        #    env.start()
        #    self.gm = gp.Model(name, env=env)
        self.gm = gp.Model(name)
        self.date = datetime.strptime(date, '%Y-%m-%d')
        self.name = name
        self.path = f'C:\\Users\\hnordstr\\OneDrive - KTH\\box_files\\KTH\\Papers&Projects\\DynamicFRR\\Normal Imbalances\\Scenario'
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

        self.atc_pos = atc_pos
        self.atc_neg = atc_neg
        self.num_scenarios = scenarios

    def setup_problem(self):
        print('READING INPUT FILES')
        ###IMBALANCES###
        self.stochastic = {}
        for i in range(1, self.num_scenarios + 1):
            stoch_in = pd.read_csv(f'{self.path}{i}\\stochastic_prenet.csv', index_col=[0])
            self.stochastic[i] = pd.DataFrame(columns=self.areas)
            for a in self.areas:
                self.stochastic[i][a] = stoch_in[a][datetime.strftime(self.date, '%Y-%m-%d %H:%M:%S+00:00'):
                     datetime.strftime(self.date + timedelta(minutes=59 + 23 * 60), '%Y-%m-%d %H:%M:%S+00:00')].tolist()
        self.deterministic = pd.read_csv(f'{self.path}1\\deterministic_prenet.csv', index_col=[0])


        print('SETTING UP VARIABLES')
        ###SETS###
        self.set_TIME = list(range(self.num_scenarios * 24 * 60))
        self.set_INTERVALS = list(range(self.num_scenarios * 24 * 60 - 1))
        self.set_AREAS = self.areas
        self.set_ACLINES = self.ac_links
        self.set_ACINDX = self.ac_indx
        self.set_IMPORT_LINES = {}
        self.set_EXPORT_LINES = {}
        for a in self.set_AREAS:
            self.set_IMPORT_LINES[a] = [l for l in self.ac_links.keys() if self.ac_links[l][0] == a]
            self.set_EXPORT_LINES[a] = [l for l in self.ac_links.keys() if self.ac_links[l][1] == a]

        ###PARAMETERS###
        self.param_STOCHASTIC_IMBALANCE = pd.DataFrame(columns=self.areas, index=self.set_TIME)
        self.param_DETERMINISTIC_IMBALANCE = pd.DataFrame(columns=self.areas, index=self.set_TIME)
        self.param_ATC_POS = pd.DataFrame(columns=self.set_ACINDX, index=self.set_TIME)
        self.param_ATC_NEG = pd.DataFrame(columns=self.set_ACINDX, index=self.set_TIME)

        for l in self.set_ACINDX:
            self.param_ATC_POS[l] = [self.atc_pos[l][i] for n in range(self.num_scenarios) for i in
                                     range(self.atc_pos.__len__()) for x in range(60)]
            self.param_ATC_NEG[l] = [self.atc_neg[l][i] for n in range(self.num_scenarios) for i in
                                     range(self.atc_neg.__len__()) for x in range(60)]
        for a in self.areas:
            sto_list = []
            det_list = []
            for n in range(1, self.num_scenarios + 1):
                sto_list.extend(self.stochastic[n][a].tolist())
                det_list.extend(self.deterministic[a][datetime.strftime(self.date, '%Y-%m-%d %H:%M:%S+00:00'):
                    datetime.strftime(self.date + timedelta(minutes=59 + 23*60), '%Y-%m-%d %H:%M:%S+00:00')].values)
            self.param_STOCHASTIC_IMBALANCE[a] = sto_list
            self.param_DETERMINISTIC_IMBALANCE[a] = det_list


        ###VARIABLES###
        self.var_AC_POS = self.gm.addVars(self.set_ACINDX, self.set_TIME, name='ACPOS', vtype=GRB.CONTINUOUS, lb=0,
                                          ub=float('inf'))
        self.var_AC_NEG = self.gm.addVars(self.set_ACINDX, self.set_TIME, name='ACNEG', vtype=GRB.CONTINUOUS, lb=0,
                                          ub=float('inf'))
        self.var_IMBALANCE_POS = self.gm.addVars(self.set_AREAS, self.set_TIME, name='BALUP', vtype=GRB.CONTINUOUS,
                                                 lb=0, ub=float('inf'))
        self.var_IMBALANCE_NEG = self.gm.addVars(self.set_AREAS, self.set_TIME, name='BALDOWN', vtype=GRB.CONTINUOUS,
                                                 lb=0, ub=float('inf'))
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
        obj = sum(self.var_IMBALANCE_POS[a,t] + self.var_IMBALANCE_NEG[a,t] for a in self.set_AREAS
                  for t in self.set_TIME)
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

    def setup_balance_constr(self):
        print('SETTING UP BALANCE CONSTRAINTS')
        self.constr_balance = {}
        for a in self.set_AREAS:
            for t in self.set_TIME:
                left_hand = self.param_STOCHASTIC_IMBALANCE[a][t] + self.param_DETERMINISTIC_IMBALANCE[a][t] \
                            + self.var_IMBALANCE_NEG[a,t] - self.var_IMBALANCE_POS[a,t]
                right_hand = 0
                for l in self.set_IMPORT_LINES[a]:
                    left_hand = left_hand + (self.var_AC_POS[l, t] - self.var_AC_NEG[l, t])
                for l in self.set_EXPORT_LINES[a]:
                    left_hand = left_hand - (self.var_AC_POS[l, t] - self.var_AC_NEG[l, t])
                self.constr_balance[a, t] = self.gm.addLConstr(
                    lhs = left_hand,
                    sense = GRB.EQUAL,
                    rhs = right_hand,
                    name = f'BALANCE[{a, t}]'
                )

    def run(self):
        self.setup_problem()
        print('SOLVING OPTIMIZATION PROBLEM')
        self.gm.optimize()
        self.ac = pd.DataFrame(index=self.set_TIME, columns=self.set_ACINDX)
        self.atc_pos = pd.DataFrame(index=self.set_TIME, columns=self.set_ACINDX)
        self.atc_neg = pd.DataFrame(index=self.set_TIME, columns=self.set_ACINDX)
        self.imbalance_pos = pd.DataFrame(index=self.set_TIME, columns=self.set_AREAS)
        self.imbalance_neg = pd.DataFrame(index=self.set_TIME, columns=self.set_AREAS)
        self.imbalance = pd.DataFrame(index=self.set_TIME, columns=self.set_AREAS)
        print('POST-PROCESSING OF DATA')
        for l in self.set_ACINDX:
            AC_list = []
            for t in self.set_TIME:
                AC_list.append(self.var_AC_POS[l,t].X - self.var_AC_NEG[l,t].X)
            self.ac[l] = AC_list
        for a in self.set_AREAS:
            imbpos_list = []
            imbneg_list = []
            for t in self.set_TIME:
                imbpos_list.append(self.var_IMBALANCE_POS[a,t].X)
                imbneg_list.append(self.var_IMBALANCE_NEG[a,t].X)
            self.imbalance_pos[a] = imbpos_list
            self.imbalance_neg[a] = imbneg_list
            self.imbalance[a] = self.imbalance_pos[a] - self.imbalance_neg[a]
        for l in self.set_ACINDX:
            self.atc_pos[l] = self.param_ATC_POS[l] - self.ac[l]
            self.atc_neg[l] = self.param_ATC_NEG[l] + self.ac[l]
        return self.param_STOCHASTIC_IMBALANCE, self.param_DETERMINISTIC_IMBALANCE, self.imbalance, self.atc_pos, self.atc_neg, self.ac