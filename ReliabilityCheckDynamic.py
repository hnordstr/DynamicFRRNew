import numpy as np
import pickle as pkl
from datetime import timedelta, datetime
import gurobipy as gp
import pandas as pd
from gurobipy import *
from gurobipy import GRB

class ReliabilityCheck:

    def __init__(self, date,num):
        self.date = date
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
        self.result_path = 'C:\\Users\hnordstr\\OneDrive - KTH\\box_files\\KTH\\Papers&Projects\\DynamicFRR\\Results'
        with open(f'{self.result_path}\\DynamicPreDA\\Day_{self.date}_Scenarios_20.pickle','rb') as handle:
            data_in = pkl.load(handle)
        self.PARAM_RESERVECAPUP = data_in['FRR NI']['Up capacity']
        self.PARAM_RESERVECAPDOWN = data_in['FRR NI']['Down capacity']
        self.PARAM_IMBALANCE = data_in['Sampling']['Slow imbalances']
        self.PARAM_ATCPOS = data_in['Sampling']['ATC positive']
        self.PARAM_ATCNEG = data_in['Sampling']['ATC negative']
        self.UNSERVEDUP = data_in['FRR NI']['Unserved up'].sum(axis=1).sum()
        self.UNSERVEDDOWN = data_in['FRR NI']['Unserved down'].sum(axis=1).sum()
        self.TRANSMISSION = data_in['FRR NI']['Transmission'].abs().sum(axis=1).sum()


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

        self.setup_objective()
        self.setup_transmission_pos()
        self.setup_transmission_neg()
        self.setup_power_balance()
        self.setup_activation_up()
        self.setup_activation_down()
        #self.gm.setParam('FeasibilityTol', 10 ** (-4))

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
                right_hand = self.PARAM_RESERVECAPUP[a][0]
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
                right_hand = self.PARAM_RESERVECAPDOWN[a][0]
                self.CONSTR_ACTIVATIONDOWN[a, i] = self.gm.addLConstr(
                    lhs=left_hand,
                    sense=GRB.LESS_EQUAL,
                    rhs=right_hand,
                    name=f'ACTIVATIONDOWN[{a, i}]'
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


date_range = []
d = datetime.strptime('2019-01-03', '%Y-%m-%d')
rel_up_list = []
rel_down_list = []
for day in range(1):
    date_range.append(datetime.strftime(d + timedelta(days=day), '%Y-%m-%d'))

i=0
for d in date_range:
    m = ReliabilityCheck(date=d, num=i)
    m.setup_problem()
    m.gm.optimize()
    results = {
        'Unserved up': pd.DataFrame(columns=m.SET_AREAS, index=m.SET_SCENARIOS),
        'Unserved down': pd.DataFrame(columns=m.SET_AREAS, index=m.SET_SCENARIOS),
        'Transmission': pd.DataFrame(columns=m.SET_ACLINKS, index=m.SET_SCENARIOS),
    }
    for a in m.SET_AREAS:
        results['Unserved up'][a] = [m.VAR_UNSERVEDPOS[a, w].X for w in m.SET_SCENARIOS]
        results['Unserved down'][a] = [m.VAR_UNSERVEDNEG[a, w].X for w in m.SET_SCENARIOS]
    for l in m.SET_ACLINKS:
        results['Transmission'][l] = [m.VAR_TRANSMISSIONPOS[l, w].X - m.VAR_TRANSMISSIONNEG[l, w].X
                                           for w in m.SET_SCENARIOS]

    print(f'Share upwards unserved energy: {round(100 * m.UNSERVEDUP / results["Unserved up"].sum(axis=1).sum(),3)} %')
    print(f'Share upwards unserved energy: {round(100 * m.UNSERVEDDOWN / results["Unserved down"].sum(axis=1).sum(),3)} %')
    print(f'Share transmission: {round(100 * m.TRANSMISSION / results["Transmission"].abs().sum(axis=1).sum(), 3)} %')
    # viol_up = 0
    # viol_down = 0
    # for w in m.SET_SCENARIOS:
    #     if sum(m.VAR_UNSERVEDPOS[a,w].X for a in m.SET_AREAS) > 0:
    #         viol_up += 1
    #     if sum(m.VAR_UNSERVEDNEG[a,w].X for a in m.SET_AREAS) > 0:
    #         viol_down += 1
    # rel_up = 100 - 100 * viol_up / m.SET_SCENARIOS.__len__()
    # rel_down = 100 - 100 * viol_down / m.SET_SCENARIOS.__len__()
    # print(d)
    # print(f'Up reliability {round(rel_up,3)}%')
    # print(f'Down reliability {round(rel_down,3)}%')
    # rel_up_list.append(rel_up)
    # rel_down_list.append(rel_down)
    # i+=1
# df = pd.DataFrame(columns=['Reliability up', 'Reliability down'])
# df['Reliability up'] = rel_up_list
# df['Reliability down'] = rel_down_list
# # df.to_csv('reliability.csv')
# print(df)
