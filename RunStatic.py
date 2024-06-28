import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from RIDimensioningStatic import RIDimensioning
from ImbalanceNettingStatic import GurobiModel as ImbalanceNetting
from MinuteToQuarter import minute_to_quarter as ImbalanceSampling
from Capacity_total_FRR import FRRNIDimensioning
from Capacity_aFRR import aFRRNIDimensioning
import pickle as pkl
#import os

# begin with 3 months
"""
1. Read ATC from ODIN, choose daterange (compute both hours and minutes)
2. Run FRR_RI dimensioning -> save FRR_RI and ATC_postRI
3. Read stochastic and normal imbalances from scenario 1 (Done within imbalance netting
4. Run imbalance netting using imbalances and ATC_postRI -> Save netted imbalances + ATC_postnet
6. Run imbalance sampling -> save ATC, slow imbalance and fast imbalance with quarter-hourly resolution
7. Run FRR_NI dimensioning using ATC and slow imbalances -> save FRR_NI, save remaining ATC for potential analyses
8. Run aFRR_NI dimensionig using ATC and fast imbalances -> save aFRR_NI
9. Compute and save mFRR_NI as FRR_NI - aFRR_NI"""

class StaticDimensioning:

    def __init__(self, start_date='2019-01-01', num_days=10, save=False, epsilon=0.01):
        self.save = save
        self.areas = ('SE1', 'SE2', 'SE3', 'SE4', 'NO1', 'NO2', 'NO3', 'NO4', 'NO5', 'DK2', 'FI')
        self.data_path = 'C:\\Users\\hnordstr\\OneDrive - KTH\\box_files\\KTH\\Papers&Projects\\DynamicFRR\\Normal Imbalances\\Scenario1\\'
        self.result_path = f'C:\\Users\\hnordstr\\OneDrive - KTH\\box_files\\KTH\\Papers&Projects\\DynamicFRR\\Results\\Static\\'
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.num_days = num_days
        self.hour_time = [self.start_date + timedelta(hours=x) for x in range(24 * num_days)]
        self.minute_time = [self.start_date + timedelta(minutes=x) for x in range(24 * 60 * num_days)]
        self.atc_odin = pd.read_csv(f'{self.data_path}ATC_ODIN.csv', index_col=[0])
        self.atc_odin = self.atc_odin.loc[datetime.strftime(self.hour_time[0], '%Y-%m-%d %H:%M:%S+00:00'):
                                          datetime.strftime(self.hour_time[-1], '%Y-%m-%d %H:%M:%S+00:00')]
        self.epsilon = epsilon
        self.atc_odin.reset_index(drop=True, inplace=True)
        self.ac_index = self.atc_odin.columns.tolist()
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
        self.atc_odin = self.atc_odin.round(decimals=0)

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

    def RI_dimensioning(self):
        print('DIMENSIONING FRR FOR REFERENCE INCIDENTS')
        st = time.time()
        model = RIDimensioning(atc=self.atc_odin, num_RI=1, epsilon=self.epsilon, vertex_sets=self.VERTEXSETS)
        self.RI_results = model.run()
        et = time.time()
        print(f'RI dimensioning done in {et - st} seconds')

    def imbalance_netting(self, atc_pos=[], atc_neg=[]):
        print('NETTING IMBALANCES')
        st = time.time()
        if atc_pos.__len__() == 0:
            atc_pos = self.RI_results['ATC positive']
        for c in atc_pos.columns.tolist():
            atc_pos.loc[atc_pos[c] < 0, c] = 0
        if atc_neg.__len__() == 0:
            atc_neg = self.RI_results['ATC negative']
        for c in atc_neg.columns.tolist():
            atc_neg.loc[atc_neg[c] < 0, c] = 0
        self.netting_results = {}
        self.netting_results['Stochastic imbalances'], self.netting_results['Deterministic imbalances'], \
        self.netting_results['Netted imbalances'], self.netting_results['ATC positive'],\
        self.netting_results['ATC negative'], self.netting_results['Transmission'] = \
            ImbalanceNetting(atc_pos=atc_pos, atc_neg=atc_neg, time=self.hour_time).run()
        et = time.time()
        print(f'Imbalance netting done in {et - st} seconds')

    def imbalance_sampling(self, imbalances=[], atc_pos=[], atc_neg=[]):
        print('SAMPLING IMBALANCES')
        st = time.time()
        if atc_pos.__len__() == 0 and imbalances.__len__() == 0 and atc_neg.__len__() == 0:
            imbalances = self.netting_results['Netted imbalances']
            atc_pos = self.netting_results['ATC positive']
            atc_neg = self.netting_results['ATC negative']
        self.sampling_results = {}
        self.sampling_results['Slow imbalances'], self.sampling_results['Fast imbalances'], \
        self.sampling_results['ATC positive'], self.sampling_results['ATC negative'] = \
            ImbalanceSampling(imbalance=imbalances, atc_pos_in=atc_pos, atc_neg_in=atc_neg)
        et = time.time()
        print(f'Imbalance sampling done in {et - st} seconds')

    def aFRR_NI_dimensioning(self, imbalances=[], atc_pos=[], atc_neg=[]):
        print('DIMENSIONING AFRR FOR NORMAL IMBALANCES')
        st = time.time()
        if atc_pos.__len__() == 0 and atc_neg.__len__() == 0 and imbalances.__len__() == 0:
            imbalances = self.sampling_results['Fast imbalances']
            atc_pos = self.sampling_results['ATC positive']
            atc_neg = self.sampling_results['ATC negative']

        model = aFRRNIDimensioning(imbalances=imbalances, atc_pos=atc_pos, atc_neg=atc_neg, epsilon=self.epsilon, vertex_sets=self.VERTEXSETS)
        self.aFRR_NI_results = model.run()
        et = time.time()
        print(f'aFRR dimensioning done in {et - st} seconds')

    def total_NI_dimensioning(self, imbalances=[], atc_pos=[], atc_neg=[], capup=[], capdown=[]):
        print('DIMENSIONING FRR FOR NORMAL IMBALANCES')
        st = time.time()
        if atc_pos.__len__() == 0 and atc_neg.__len__() == 0 and imbalances.__len__() == 0:
            imbalances = self.sampling_results['Slow imbalances']
            atc_pos = self.sampling_results['ATC positive']
            atc_neg = self.sampling_results['ATC negative']
        if capup.__len__() == 0 and capdown.__len__() == 0:
            capup = self.aFRR_NI_results['Up capacity']
            capdown = self.aFRR_NI_results['Down capacity']

        model = FRRNIDimensioning(imbalances=imbalances, atc_pos=atc_pos, atc_neg=atc_neg, capup=capup, capdown=capdown,
                                  epsilon=self.epsilon, vertex_sets=self.VERTEXSETS)
        self.FRR_NI_results = model.run()
        et = time.time()
        print(f'Total FRR dimensioning done in {et - st} seconds')


    def run(self):
        st_time = time.time()
        self.setup_linked_vertex_sets()
        self.RI_dimensioning()
        self.imbalance_netting()
        self.imbalance_sampling()
        self.aFRR_NI_dimensioning()
        self.total_NI_dimensioning()
        self.mFRR_NI_results = {
            'Up capacity': self.FRR_NI_results['Up capacity'] - self.aFRR_NI_results['Up capacity'],
            'Down capacity': self.FRR_NI_results['Down capacity'] - self.aFRR_NI_results['Down capacity']
        }
        et_time = time.time()
        print(f'Ran entire process in {et_time - st_time} seconds')
        self.results = {
            'RI': self.RI_results,
            'Netting': self.netting_results,
            'Sampling': self.sampling_results,
            'FRR NI': self.FRR_NI_results,
            'aFRR NI': self.aFRR_NI_results,
            'mFRR NI': self.mFRR_NI_results,
            'Time': et_time - st_time
        }
        if self.save:
            with open(f'{self.result_path}Start_{datetime.strftime(self.start_date, "%Y-%m-%d")}_Days_{self.num_days}_Epsilon_{self.epsilon}.pickle', 'wb') as handle:
                pkl.dump(self.results, handle, protocol=pkl.HIGHEST_PROTOCOL)


m = StaticDimensioning(num_days=365, save=True, epsilon=0.05)
m.run()








