import pickle as pkl
import json

import numpy as np
import plotly.express as px
import pandas as pd
import geojson_rewind
import geopandas as gpd
import plotly
import geopandas
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime, timedelta


"""
Each day/month/season/year constains a dictionary with keys:
'RI': RI input and results in dict with keys; Up/Down activation, Penalty up/down, Up/down capacity, Transmission value, ATC,
'Netting': Netting input and results in dict with keys; Stochastic/Deterministic/Netted imbalances, ATC, Transmission,
'Sampling': Sampling results in dict with keys; Slow/Fast imbalances, ATC,
'FRR NI': Total FRR results in dict with keys; Up/Down activation, Penalty up/down, Up/down capacity, Transmission value, ATC,,
'aFRR NI': aFRR results in dict with keys; Up/Down activation, Penalty up/down, Up/down capacity, Transmission value, ATC,,
'mFRR NI': mFRR results in dict with keys; Up/Down capacity,
'Time': Simulation time as float


File naming convention:
(x) = variable x
Static: result_path\\Static\\Start_(YYYY-mm-dd)_Days_(ndays).pickle
Dynamic pre-DA: result_path\\DynamicPreDA\\Day_(YYYY-mm-dd)_Scenarios_(nscenarios)_RIs_(nRIs).pickle
Dynamic post-DA: result_path\\DynamicPostDA
"""
areas = ('SE1', 'SE2', 'SE3', 'SE4', 'NO1', 'NO2', 'NO3', 'NO4', 'NO5', 'DK2', 'FI')
result_path ='C:\\Users\hnordstr\\OneDrive - KTH\\box_files\\KTH\\Papers&Projects\\DynamicFRR\\Results'


def print_static():
    stat_dict = {}
    with open(f'{result_path}\\Static\\Start_2019-01-01_Days_365_Epsilon_0.01.pickle','rb') as handle:
        static = pkl.load(handle)
        stat_up = static['RI']['Up capacity'].sum(axis=1)[0] + static['FRR NI']['Up capacity'].sum(axis=1)[0]
        stat_down = static['RI']['Down capacity'].sum(axis=1)[0] + static['FRR NI']['Down capacity'].sum(axis=1)[0]
        print(stat_up)
        print(stat_down)

def read_dynamic():
    results = pd.DataFrame(columns=['RI', 'aFRR', 'mFRR'], index=['Up', 'Down'])
    date_range = []
    d = datetime.strptime('2019-01-01', '%Y-%m-%d')
    for day in range(15):
        date_range.append(datetime.strftime(d + timedelta(days=day), '%Y-%m-%d'))
    result_dict = {}
    i = 0
    for d in date_range:
        with open(f'{result_path}\\DynamicPreDA\\Day_{d}_Scenarios_20_ATC_0.pickle', 'rb') as handle:
            result_dict[i] = pkl.load(handle)
        i += 1
    results['RI']['Up'] = sum(
        [sum(result_dict[i]['RI'][f'Up capacity'][a][0] for i in range(15) for a in areas)]) / 15
    results['RI']['Down'] = sum(
        [sum(result_dict[i]['RI'][f'Down capacity'][a][0] for i in range(15) for a in areas)]) / 15
    results['aFRR']['Up'] = sum(
        [sum(result_dict[i]['aFRR NI'][f'Up capacity'][a][0] for i in range(15) for a in areas)]) / 15
    results['aFRR']['Down'] = sum(
        [sum(result_dict[i]['aFRR NI'][f'Down capacity'][a][0] for i in range(15) for a in areas)]) / 15
    results['mFRR']['Up'] = sum(
        [sum(result_dict[i]['mFRR NI'][f'Up capacity'][a][0] for i in range(15) for a in areas)]) / 15
    results['mFRR']['Down'] = sum(
        [sum(result_dict[i]['mFRR NI'][f'Down capacity'][a][0] for i in range(15) for a in areas)]) / 15
    print(results)

def read_per_control_area_static():
    #Read static
    no_zones = ['NO1', 'NO2', 'NO3', 'NO4', 'NO5']
    se_zones = ['SE1', 'SE2', 'SE3', 'SE4']
    results = pd.DataFrame(columns=['RI', 'aFRR', 'mFRR'], index=['SE', 'NO', 'DK', 'FI', 'Total'])
    with open(f'{result_path}\\Static\\Start_2019-01-01_Days_365_Epsilon_0.05.pickle','rb') as handle:
       static = pkl.load(handle)

    results['RI']['FI'] = static['RI']['Up capacity']['FI'][0]
    results['aFRR']['FI'] = static['aFRR NI']['Up capacity']['FI'][0]
    results['mFRR']['FI'] = static['mFRR NI']['Up capacity']['FI'][0]
    results['RI']['DK'] = static['RI']['Up capacity']['DK2'][0]
    results['aFRR']['DK'] = static['aFRR NI']['Up capacity']['DK2'][0]
    results['mFRR']['DK'] = static['mFRR NI']['Up capacity']['DK2'][0]

    ri = 0
    afrr = 0
    mfrr = 0
    for a in no_zones:
        ri += static['RI']['Up capacity'][a][0]
        afrr += static['aFRR NI']['Up capacity'][a][0]
        mfrr += static['mFRR NI']['Up capacity'][a][0]

    results['RI']['NO'] = ri
    results['aFRR']['NO'] = afrr
    results['mFRR']['NO'] = mfrr

    ri = 0
    afrr = 0
    mfrr = 0
    for a in se_zones:
        ri += static['RI']['Up capacity'][a][0]
        afrr += static['aFRR NI']['Up capacity'][a][0]
        mfrr += static['mFRR NI']['Up capacity'][a][0]

    results['RI']['SE'] = ri
    results['aFRR']['SE'] = afrr
    results['mFRR']['SE'] = mfrr

    results['RI']['Total'] = results['RI'].sum()
    results['aFRR']['Total'] = results['aFRR'].sum()
    results['mFRR']['Total'] = results['mFRR'].sum()

    print(results)

def read_per_control_area_dynamic(direction='Up'):
    #Read static
    no_zones = ['NO1', 'NO2', 'NO3', 'NO4', 'NO5']
    se_zones = ['SE1', 'SE2', 'SE3', 'SE4']
    results = pd.DataFrame(columns=['RI', 'aFRR', 'mFRR'], index=['SE', 'NO', 'DK', 'FI', 'Total'])
    date_range = []
    d = datetime.strptime('2019-01-01', '%Y-%m-%d')
    for day in range(15):
        date_range.append(datetime.strftime(d + timedelta(days=day), '%Y-%m-%d'))
    result_dict = {}
    i = 0
    for d in date_range:
        with open(f'{result_path}\\DynamicPreDA\\Day_{d}_Scenarios_20.pickle','rb') as handle:
            result_dict[i] = pkl.load(handle)
        i += 1

    results['RI']['FI'] = sum([result_dict[i]['RI'][f'{direction} capacity']['FI'][0] for i in range(15)]) / 15
    results['aFRR']['FI'] = sum([result_dict[i]['aFRR NI'][f'{direction} capacity']['FI'][0] for i in range(15)]) / 15
    results['mFRR']['FI'] = sum([result_dict[i]['mFRR NI'][f'{direction} capacity']['FI'][0] for i in range(15)]) / 15
    results['RI']['DK'] = sum([result_dict[i]['RI'][f'{direction} capacity']['DK2'][0] for i in range(15)]) / 15
    results['aFRR']['DK'] = sum([result_dict[i]['aFRR NI'][f'{direction} capacity']['DK2'][0] for i in range(15)]) / 15
    results['mFRR']['DK'] = sum([result_dict[i]['mFRR NI'][f'{direction} capacity']['DK2'][0] for i in range(15)]) / 15

    results['RI']['NO'] = sum([sum(result_dict[i]['RI'][f'{direction} capacity'][a][0] for i in range(15) for a in no_zones)]) / 15
    results['aFRR']['NO'] = sum([sum(result_dict[i]['aFRR NI'][f'{direction} capacity'][a][0] for i in range(15) for a in no_zones)]) / 15
    results['mFRR']['NO'] = sum([sum(result_dict[i]['mFRR NI'][f'{direction} capacity'][a][0] for i in range(15) for a in no_zones)]) / 15
    results['RI']['SE'] = sum([sum(result_dict[i]['RI'][f'{direction} capacity'][a][0] for i in range(15) for a in se_zones)]) / 15
    results['aFRR']['SE'] = sum([sum(result_dict[i]['aFRR NI'][f'{direction} capacity'][a][0] for i in range(15) for a in se_zones)]) / 15
    results['mFRR']['SE'] = sum([sum(result_dict[i]['mFRR NI'][f'{direction} capacity'][a][0] for i in range(15) for a in se_zones)]) / 15
    results['RI']['Total'] = results['RI'].sum()
    results['aFRR']['Total'] = results['aFRR'].sum()
    results['mFRR']['Total'] = results['mFRR'].sum()
    print(results)

#read_per_control_area_dynamic(direction='Up')

def read_to_csv(version):
    start = datetime.strptime('2019-01-01', '%Y-%m-%d')
    dates = [start + timedelta(days=d) for d in range(365)]

    post_da_up = []
    post_da_down = []
    labels = []
    post_da = pd.DataFrame(columns=['Date', 'Uptot', 'Downtot'])
    if version == 'PostDA':
        file_path = f'{result_path}\\DynamicPostDA\\'
    elif version == 'PreDA':
        file_path = f'{result_path}\\DynamicPreDA\\'

    i = 0
    for d in dates:
        with open(f'{file_path}Day_{datetime.strftime(d, "%Y-%m-%d")}_Scenarios_20.pickle',
                  'rb') as handle:
            results = pkl.load(handle)
        up = 0
        down = 0
        for a in areas:
            up += results['RI']['Up capacity'][a][0] + \
                                  results['FRR NI']['Up capacity'][a][0]
            down += results['RI']['Down capacity'][a][0] + \
                                  results['FRR NI']['Down capacity'][a][0]
        post_da_up.append(up)
        post_da_down.append(down)
        labels.append(i)
        i += 1
    post_da['Date'] = labels
    post_da['Uptot'] = post_da_up
    post_da['Downtot'] = post_da_down
    post_da = post_da.set_index('Date')
    print(post_da['Uptot'].mean())
    print(post_da['Downtot'].mean())
    # if version == 'PostDA':
    #     post_da.to_csv('post_da.csv')
    # elif version == 'PreDA':
    #     post_da.to_csv('pre_da.csv')



#
def choropleth_static():
    stat_up = pd.DataFrame(columns=['Reserves', 'id'] )
    stat_down = pd.DataFrame(columns=['Reserves', 'id'])
    with open(f'{result_path}\\Static\\Start_2019-01-01_Days_365_Epsilon_0.01.pickle','rb') as handle:
       static = pkl.load(handle)
    #
    stat_up['Reserves'] = [static['RI']['Up capacity'][a][0] + static['FRR NI']['Up capacity'][a][0] for a in areas]
    stat_down['Reserves'] = [static['RI']['Down capacity'][a][0] + static['FRR NI']['Down capacity'][a][0] for a in areas]

    stat_up['id'] = [a for a in areas]
    stat_down['id'] = [a for a in areas]


    ## plot per area
    maps_in = gpd.read_file('C:\\Users\\hnordstr\\OneDrive - KTH\\box_files\KTH\\Papers&Projects\\DynamicFRR\\nordic.geojson')
    maps_in = json.loads(maps_in.to_json())
    maps = geojson_rewind.rewind(maps_in, rfc7946=False)


    for f in maps['features']:
       f['id'] = f['properties']['name']
    print(maps)
    print(stat_down)

    fig = px.choropleth(stat_down,
                       locations='id',
                       geojson=maps,
                       featureidkey='id',
                       color='Reserves',
                       hover_name='id',
                       color_continuous_scale=px.colors.sequential.Viridis,
                       range_color=[0, 2000],
                       scope='europe')
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.update_layout(coloraxis_colorbar=dict(
       ticks="outside", ticksuffix=" MW",
       dtick=400, len=0.8, thickness=50, y=0.53,x=0.67,
       title=dict(text='FRR', font=dict(size=60))
    ))
    fig.update_coloraxes(colorbar_tickfont_size=60)
    fig.show()


def choropleth_preda():
    # Choropleth plot pre-DA
    start = datetime.strptime('2019-01-01', '%Y-%m-%d')
    dates = [start + timedelta(days=d) for d in range(365)]

    pre_da_up = pd.DataFrame(columns=areas, index=list(range(365)))
    pre_da_down = pd.DataFrame(columns=areas, index=list(range(365)))

    i = 0
    for d in dates:
        with open(f'{result_path}\\DynamicPreDA\\Day_{datetime.strftime(d, "%Y-%m-%d")}_Scenarios_20.pickle',
                  'rb') as handle:
            results = pkl.load(handle)
            for a in areas:
                pre_da_up[a][i] = results['RI']['Up capacity'][a][0] + \
                                      results['FRR NI']['Up capacity'][a][0]
                pre_da_down[a][i] = results['RI']['Down capacity'][a][0] + \
                                      results['FRR NI']['Down capacity'][a][0]
        i += 1

    preda_up = pd.DataFrame(columns=['Reserves', 'id'])
    preda_down = pd.DataFrame(columns=['Reserves', 'id'])

    preda_up['Reserves'] = [pre_da_up[a].mean() for a in areas]
    preda_down['Reserves'] = [pre_da_down[a].mean() for a in areas]
    preda_up['id'] = [a for a in areas]
    preda_down['id'] = [a for a in areas]
    ## plot per area
    maps_in = gpd.read_file('C:\\Users\\hnordstr\\OneDrive - KTH\\box_files\KTH\\Papers&Projects\\DynamicFRR\\nordic.geojson')
    maps_in = json.loads(maps_in.to_json())
    maps = geojson_rewind.rewind(maps_in, rfc7946=False)

    for f in maps['features']:
        f['id'] = f['properties']['name']
    print(preda_up)
    print(preda_down)

    fig = px.choropleth(preda_down,
                        locations='id',
                        geojson=maps,
                        featureidkey='id',
                        color='Reserves',
                        hover_name='id',
                        color_continuous_scale=px.colors.sequential.Viridis,
                        range_color=[0, 2000],
                        scope='europe')
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.update_layout(coloraxis_colorbar=dict(
        ticks="outside", ticksuffix=" MW",
        dtick=200, len=0.8, thickness=50, y=0.53,x=0.67,
        title=dict(text='FRR', font=dict(size=30))
    ))
    fig.update_coloraxes(colorbar_tickfont_size=30)

    fig.show()


def choropleth_postda():
    # Choropleth plot post-DA
    start = datetime.strptime('2019-01-01', '%Y-%m-%d')
    dates = [start + timedelta(days=d) for d in range(365)]

    post_da_up = pd.DataFrame(columns=areas, index=list(range(365)))
    post_da_down = pd.DataFrame(columns=areas, index=list(range(365)))

    i = 0
    for d in dates:
        with open(f'{result_path}\\DynamicPostDA\\Day_{datetime.strftime(d, "%Y-%m-%d")}_Scenarios_20.pickle',
                  'rb') as handle:
            results = pkl.load(handle)
            for a in areas:
                post_da_up[a][i] = results['RI']['Up capacity'][a][0] + \
                                      results['FRR NI']['Up capacity'][a][0]
                post_da_down[a][i] = results['RI']['Down capacity'][a][0] + \
                                      results['FRR NI']['Down capacity'][a][0]
        i += 1

    postda_up = pd.DataFrame(columns=['Reserves', 'id'])
    postda_down = pd.DataFrame(columns=['Reserves', 'id'])

    postda_up['Reserves'] = [post_da_up[a].mean() for a in areas]
    postda_down['Reserves'] = [post_da_down[a].mean() for a in areas]
    postda_up['id'] = [a for a in areas]
    postda_down['id'] = [a for a in areas]
    ## plot per area
    maps_in = gpd.read_file('C:\\Users\\hnordstr\\OneDrive - KTH\\box_files\KTH\\Papers&Projects\\DynamicFRR\\nordic.geojson')
    maps_in = json.loads(maps_in.to_json())
    maps = geojson_rewind.rewind(maps_in, rfc7946=False)

    for f in maps['features']:
        f['id'] = f['properties']['name']

    print(postda_up)
    print(postda_down)

    fig = px.choropleth(postda_down,
                        locations='id',
                        geojson=maps,
                        featureidkey='id',
                        color='Reserves',
                        hover_name='id',
                        color_continuous_scale=px.colors.sequential.Viridis,
                        range_color=[0, 2000],
                        scope='europe')
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.update_layout(coloraxis_colorbar=dict(
        ticks="outside", ticksuffix=" MW",
        dtick=200, len=0.8, thickness=50, y=0.53,x=0.67,
        title=dict(text='FRR', font=dict(size=30))
    ))
    fig.update_coloraxes(colorbar_tickfont_size=30)

    fig.show()

def reliability_plot():
    start = datetime.strptime('2019-01-01', '%Y-%m-%d')
    dates = [start + timedelta(days=d) for d in range(365)]
    rel_up = pd.DataFrame(columns=['Static 1%', 'Static 3%', 'Static 5%', 'Dynamic Pre-DA', 'Interval', 'Duration', 'Percentage'])
    rel_down = pd.DataFrame(columns=['Static 1%', 'Static 3%', 'Static 5%', 'Dynamic Pre-DA', 'Interval', 'Duration', 'Percentage'])
    # rel_up['Date'] = [i for i in range(365)]
    # rel_down['Date'] = [i for i in range(365)]
    with open(f'{result_path}\\Static\\Start_2019-01-01_Days_365_Epsilon_0.01.pickle','rb') as handle:
       static = pkl.load(handle)
    period_range = int(static['FRR NI']['Unserved up'].__len__() /365)
    up_list = []
    down_list = []
    for d in range(365):
        up_list.append(100 - 100 * np.count_nonzero(
            static['FRR NI']['Unserved up'][d * period_range: (d+1) * period_range].sum(axis=1)) / period_range)
        down_list.append(100 - 100 * np.count_nonzero(
            static['FRR NI']['Unserved down'][d * period_range: (d + 1) * period_range].sum(axis=1)) / period_range)
    up_list_sorted = up_list
    up_list_sorted.sort(reverse=True)
    down_list_sorted = down_list
    down_list_sorted.sort(reverse=True)
    rel_up['Static 1%'] = up_list_sorted
    rel_down['Static 1%'] = down_list_sorted

    with open(f'{result_path}\\Static\\Start_2019-01-01_Days_365_Epsilon_0.03.pickle','rb') as handle:
       static = pkl.load(handle)
    period_range = int(static['FRR NI']['Unserved up'].__len__() /365)
    up_list = []
    down_list = []
    for d in range(365):
        up_list.append(100 - 100 * np.count_nonzero(
            static['FRR NI']['Unserved up'][d * period_range: (d+1) * period_range].sum(axis=1)) / period_range)
        down_list.append(100 - 100 * np.count_nonzero(
            static['FRR NI']['Unserved down'][d * period_range: (d + 1) * period_range].sum(axis=1)) / period_range)
    up_list_sorted = up_list
    up_list_sorted.sort(reverse=True)
    down_list_sorted = down_list
    down_list_sorted.sort(reverse=True)
    rel_up['Static 3%'] = up_list_sorted
    rel_down['Static 3%'] = down_list_sorted

    with open(f'{result_path}\\Static\\Start_2019-01-01_Days_365_Epsilon_0.05.pickle','rb') as handle:
       static = pkl.load(handle)
    period_range = int(static['FRR NI']['Unserved up'].__len__() /365)
    up_list = []
    down_list = []
    for d in range(365):
        up_list.append(100 - 100 * np.count_nonzero(
            static['FRR NI']['Unserved up'][d * period_range: (d+1) * period_range].sum(axis=1)) / period_range)
        down_list.append(100 - 100 * np.count_nonzero(
            static['FRR NI']['Unserved down'][d * period_range: (d + 1) * period_range].sum(axis=1)) / period_range)
    up_list_sorted = up_list
    up_list_sorted.sort(reverse=True)
    down_list_sorted = down_list
    down_list_sorted.sort(reverse=True)
    rel_up['Static 5%'] = up_list_sorted
    rel_down['Static 5%'] = down_list_sorted

    up_list = []
    down_list = []
    for d in dates:
        with open(f'{result_path}\\DynamicPreDA\\Day_{datetime.strftime(d, "%Y-%m-%d")}_Scenarios_20.pickle',
                  'rb') as handle:
            results = pkl.load(handle)
        up_list.append(100 - 100 * np.count_nonzero(
            results['FRR NI']['Unserved up'].sum(axis=1)) / results['FRR NI']['Unserved up'].__len__())
        down_list.append(100 - 100 * np.count_nonzero(
            results['FRR NI']['Unserved down'].sum(axis=1)) / results['FRR NI']['Unserved down'].__len__())
    up_list_sorted = up_list
    up_list_sorted.sort(reverse=True)
    down_list_sorted = down_list
    down_list_sorted.sort(reverse=True)
    rel_up['Dynamic Pre-DA'] = up_list_sorted
    rel_down['Dynamic Pre-DA'] = down_list_sorted
    rel_up['Interval'] = [1 for i in range(up_list_sorted.__len__())]
    rel_up['Duration'] = rel_up['Interval'].cumsum()
    rel_up['Percentage'] = rel_up['Duration'] * 100 / up_list_sorted.__len__()
    rel_down['Interval'] = [1 for i in range(up_list_sorted.__len__())]
    rel_down['Duration'] = rel_down['Interval'].cumsum()
    rel_down['Percentage'] = rel_down['Duration'] * 100 / up_list_sorted.__len__()
    # up_list = []
    # down_list = []
    # for d in dates:
    #     with open(f'{result_path}\\DynamicPostDA\\Day_{datetime.strftime(d, "%Y-%m-%d")}_Scenarios_20.pickle',
    #               'rb') as handle:
    #         results = pkl.load(handle)
    #     up_list.append(100 - 100 * np.count_nonzero(
    #         results['FRR NI']['Unserved up'].sum(axis=1)) / results['FRR NI']['Unserved up'].__len__())
    #     down_list.append(100 - 100 * np.count_nonzero(
    #         results['FRR NI']['Unserved down'].sum(axis=1)) / results['FRR NI']['Unserved down'].__len__())
    # rel_up['Dynamic Post-DA'] = up_list
    # rel_down['Dynamic Post-DA'] = down_list
    plt.rcParams.update({'font.size': 20})

    plt.plot(rel_up['Percentage'].tolist(), rel_up['Static 1%'].tolist(), label='Static up', linewidth=5)
    plt.plot(rel_down['Percentage'].tolist(), rel_down['Static 1%'].tolist(), label='Static down', linewidth=5, linestyle='--')
    # plt.plot(rel_up['Percentage'].tolist(), rel_up['Static 3%'].tolist(), label='Static 3%', linewidth=3)
    # plt.plot(rel_up['Percentage'].tolist(), rel_up['Static 5%'].tolist(), label='Static 5%', linewidth=3)
    plt.plot(rel_up['Percentage'].tolist(), rel_up['Dynamic Pre-DA'].tolist(), label='Dynamic Pre-DA/Post-DA up/down', linewidth=5)
    #plt.plot(rel_up['Dynamic Post-DA'].tolist(), label='Dynamic Post-DA', linestyle=(0, (5, 10)), linewidth=3)
    plt.grid()
    plt.legend()
    plt.xlabel('Share of time [%]')
    plt.ylabel('Reliability [%]')
    plt.tight_layout()
    fig = plt.gcf()
    fig.set_figwidth(16)
    plt.xlim(0, 100)
    plt.ylim(80,101)
    save=True
    if save:
        fig.savefig(
            f'C:\\Users\\hnordstr\\OneDrive - KTH\\box_files\\KTH\\Papers&Projects\\DynamicFRR\\ReliabilityPlot.pdf',
            dpi=fig.dpi, pad_inches=0, bbox_inches='tight')
    plt.show()

def atc_plot():
    ac_links = {
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
    atc_cap = pd.DataFrame(columns=['FI import', 'FI export', 'NO2 import', 'NO2 export'])
    with open(f'ATC.pickle','rb') as handle:
       atcs = pkl.load(handle)
    for a in ['NO2', 'FI']:
        imp_lines = []
        exp_lines = []
        for l in ac_links.keys():
            if ac_links[l][0] == a:
                imp_lines.append(l)
                exp_lines.append(ac_links[l][2])
        atc_cap[f'{a} import'] = atcs[imp_lines].sum(axis=1)
        atc_cap[f'{a} export'] = atcs[exp_lines].sum(axis=1)

    for c in atc_cap.columns.tolist():
        plt.plot(atc_cap[c].tolist(), label=c)
    plt.legend()
    plt.grid()
    plt.show()

def read_reliability_csv():
    data = pd.read_csv('reliability.csv')
    print(data['Reliability up'].mean())
    print(data['Reliability down'].mean())
    plt.plot(data['Reliability down'])
    plt.grid()
    plt.show()
    ## TESTA ATT KÖRA MED ATC:N FRÅN RI ISTÄLLET

def compare_allocation():
    #ONLY FRR and aFRR
    start = datetime.strptime('2019-01-01', '%Y-%m-%d')
    dates = [datetime.strftime(start + timedelta(days=d),'%Y-%m-%d') for d in range(31)]
    unserved_up_list1 = []
    unserved_down_list1 = []
    transmission_list1 = []
    unserved_up_list2 = []
    unserved_down_list2 = []
    transmission_list2 = []

    for d in dates:
        with open(f'{result_path}\\DynamicPreDA\\Day_{d}_Scenarios_20.pickle',
                  'rb') as handle:
            result1 = pkl.load(handle)
        with open(f'{result_path}\\DynamicPreDA\\Day_{d}_Scenarios_20_Alternate.pickle',
                  'rb') as handle2:
            result2 = pkl.load(handle2)
        unserved_up1 = result1['aFRR NI']['Unserved up'].sum(axis=1).sum()
        unserved_down1 = result1['aFRR NI']['Unserved down'].sum(axis=1).sum()
        transmission1 = result1['aFRR NI']['Transmission'].abs().sum(axis=1).sum()
        unserved_up2 = result2['aFRR NI']['Unserved up'].sum(axis=1).sum()
        unserved_down2 = result2['aFRR NI']['Unserved down'].sum(axis=1).sum()
        transmission2 = result2['aFRR NI']['Transmission'].abs().sum(axis=1).sum()
        unserved_up_list1.append(unserved_up1)
        unserved_down_list1.append(unserved_down1)
        transmission_list1.append(transmission1)
        unserved_up_list2.append(unserved_up2)
        unserved_down_list2.append(unserved_down2)
        transmission_list2.append(transmission2)

    print(f'Unserved up energy with re-allocation: {round(1000 * np.mean(unserved_up_list1) / (24 * 12 * 20 * 12), 2)} kWh')
    print(f'Unserved down energy with re-allocation: {round(1000 * np.mean(unserved_down_list1) / (24 * 12 * 20 * 12), 2)} kWh')
    print(f'Transmission with re-allocation: {round(1000 * np.mean(transmission_list1) / (24 * 12 * 20 * 12), 2)} kWh')

    print(f'Unserved up energy without re-allocation: {round(1000 * np.mean(unserved_up_list2) / (24 * 12 * 20 * 12), 2)} kWh')
    print(f'Unserved down energy without re-allocation: {round(1000 * np.mean(unserved_down_list2) / (24 * 12 * 20 * 12), 2)} kWh')
    print(f'Transmission without re-allocation: {round(1000 * np.mean(transmission_list2) / (24 * 12 * 20 * 12), 2)} kWh')

def write_time():
    with open(f'{result_path}\\Static\\Start_2019-01-01_Days_365_Epsilon_0.05.pickle','rb') as handle:
        static = pkl.load(handle)
    print(f'Static time: {round(static["Time"]/60, 2)} minutes')
    pre_da_time = 0
    post_da_time = 0
    start = datetime.strptime('2019-01-01', '%Y-%m-%d')
    dates = [datetime.strftime(start + timedelta(days=d),'%Y-%m-%d') for d in range(365)]
    for d in dates:
        with open(f'{result_path}\\DynamicPreDA\\Day_{d}_Scenarios_20.pickle',
                  'rb') as handle:
            preda = pkl.load(handle)
        with open(f'{result_path}\\DynamicPostDA\\Day_{d}_Scenarios_20.pickle',
                  'rb') as handle:
            postda = pkl.load(handle)
        pre_da_time += preda['Time']
        post_da_time += postda['Time']
    print(f'Pre-DA time: {round(pre_da_time/(60), 2)} minutes')
    print(f'Post-DA time: {round(post_da_time / (60), 2)} minutes')

def plot_vs_wind():
    results = pd.DataFrame(columns=['Up', 'Down'])
    date_range = []
    d = datetime.strptime('2019-01-01', '%Y-%m-%d')
    for day in range(365):
        date_range.append(datetime.strftime(d + timedelta(days=day), '%Y-%m-%d'))
    result_dict = {}
    i = 0
    for d in date_range:
        result_dict[i] = pd.read_pickle(f'{result_path}\\DynamicPostDA\\Day_{d}_Scenarios_20.pickle')
        i += 1
    up_list = [result_dict[i]['aFRR NI']['Up capacity'].sum(axis=1)[0] + result_dict[i]['mFRR NI']['Up capacity'].sum(axis=1)[0] for i in range(result_dict.keys().__len__())]
    down_list = [
        result_dict[i]['aFRR NI']['Down capacity'].sum(axis=1)[0] + result_dict[i]['mFRR NI']['Down capacity'].sum(axis=1)[
            0] for i in range(result_dict.keys().__len__())]
    # up_list = [result_dict[i]['aFRR NI']['Up capacity']['SE3'][0] + result_dict[i]['mFRR NI']['Up capacity']['SE3'][0] for i in range(result_dict.keys().__len__())]
    # down_list = [
    #     result_dict[i]['aFRR NI']['Down capacity']['SE3'][0] + result_dict[i]['mFRR NI']['Down capacity']['SE3'][
    #         0] for i in range(result_dict.keys().__len__())]
    results['Up'] = up_list
    results['Down'] = down_list

    odin_dict = {}
    odin_path = 'C:\\Users\\hnordstr\\OneDrive - KTH\\box_files\\KTH\\Papers&Projects\\FRRDimensioning\\odin_2020_weather2016\\'
    areas = ('SE1', 'SE2', 'SE3', 'SE4', 'NO1', 'NO2', 'NO3', 'NO4', 'NO5', 'DK2', 'FI')
    # areas = ['SE3']
    wind_sum = pd.DataFrame(columns=['Wind'])
    wind_sum['Wind'] = [0 for n in range(365 * 24)]
    for a in areas:
        odin_dict[a] = pd.read_csv(f'{odin_path}{a}.csv')
        #print(odin_dict[a].keys())
        wind_sum['Wind'] = wind_sum['Wind'] + odin_dict[a]['Wind'][:8760] * 1000
    wind_list = [wind_sum['Wind'][n*24: (n+1)*24].sum() / 1000 for n in range(365)]

    static = pd.read_pickle(f'{result_path}\\Static\\Start_2019-01-01_Days_365_Epsilon_0.01.pickle')
    stat_up = static['aFRR NI']['Up capacity'].sum(axis=1)[0] + static['mFRR NI']['Up capacity'].sum(axis=1)[0]
    stat_down = static['aFRR NI']['Down capacity'].sum(axis=1)[0] + static['mFRR NI']['Down capacity'].sum(axis=1)[0]

    stat_up_list = [stat_up for n in range(1000)]
    stat_down_list = [stat_down for n in range(1000)]


    plt.rcParams.update({'font.size': 16})
    # fig, axs = plt.subplots(nrows=1, sharex=True)
    b, a = np.polyfit(wind_list, results['Up'].tolist(), deg=1)
    xse1 = np.linspace(0.75* min(wind_list), 1.05 * max(wind_list), num = 1000)
    # axs[0].plot(xse1, a + b * xse1, color='black', linewidth=2, label='Fitted function for dynamic pre-DA')
    # axs[0].plot(xse1, stat_up_list, color='black', linewidth=2, linestyle='--', label='Fitted function for static')
    # axs[0].scatter(wind_list, results['Up'].tolist(), label='Up', alpha=0.5, color='blue')
    # axs[0].set_xlim(0.75*min(wind_list), 1.05 * max(wind_list))
    # axs[1].set_xlabel('Daily wind generation forecast [MWh]')
    # axs[0].set_ylabel('FRR-NI capacity [MW]')
    # axs[0].legend()
    # axs[0].grid()

    plt.plot(xse1, a + b * xse1, color='black', linewidth=3, label='Fitted function for dynamic pre-DA')
    plt.plot(xse1, stat_up_list, color='black', linewidth=3, linestyle='--', label='Fitted function for static')
    plt.scatter(wind_list, results['Up'].tolist(), label='Reserve need vs wind forecast', s= 60, alpha=0.5, color='blue')
    plt.xlim(0.75*min(wind_list), 1.05 * max(wind_list))
    plt.xlabel('Daily wind generation forecast [GWh]')
    plt.ylabel('FRR-NI capacity [MW]')
    plt.legend()
    plt.grid()

    # b, a = np.polyfit(wind_list, results['Down'].tolist(), deg=1)
    # xse1 = np.linspace(0.75* min(wind_list), 1.05 * max(wind_list), num = 1000)
    # axs[1].plot(xse1, a + b * xse1, color='black', linewidth=2, label='Fitted function for dynamic pre-DA')
    # axs[1].plot(xse1, stat_down_list, color='black', linewidth=2, linestyle='--', label='Fitted function for static')
    # axs[1].scatter(wind_list, results['Down'].tolist(), label='Down', alpha=0.5, color='orange')
    # axs[1].set_xlim(0.75*min(wind_list), 1.05 * max(wind_list))
    # axs[1].set_ylabel('FRR-NI capacity [MW]')
    # axs[1].legend()
    # axs[1].grid()
    plt.tight_layout()
    fig = plt.gcf()
    fig.set_figwidth(10)
    save=True
    if save:
        fig.savefig(
            f'C:\\Users\\hnordstr\\OneDrive - KTH\\box_files\\KTH\\Papers&Projects\\DynamicFRR\\WindPlot.pdf',
            dpi=fig.dpi, pad_inches=0, bbox_inches='tight')
    plt.show()

def plot_vs_demand():
    results = pd.DataFrame(columns=['Up', 'Down'])
    date_range = []
    d = datetime.strptime('2019-01-01', '%Y-%m-%d')
    for day in range(365):
        date_range.append(datetime.strftime(d + timedelta(days=day), '%Y-%m-%d'))
    result_dict = {}
    i = 0
    for d in date_range:
        result_dict[i] = pd.read_pickle(f'{result_path}\\DynamicPostDA\\Day_{d}_Scenarios_20.pickle')
        i += 1
    up_list = [result_dict[i]['aFRR NI']['Up capacity'].sum(axis=1)[0] + result_dict[i]['mFRR NI']['Up capacity'].sum(axis=1)[0] for i in range(result_dict.keys().__len__())]
    down_list = [
        result_dict[i]['aFRR NI']['Down capacity'].sum(axis=1)[0] + result_dict[i]['mFRR NI']['Down capacity'].sum(axis=1)[
            0] for i in range(result_dict.keys().__len__())]
    # up_list = [result_dict[i]['aFRR NI']['Up capacity']['SE3'][0] + result_dict[i]['mFRR NI']['Up capacity']['SE3'][0] for i in range(result_dict.keys().__len__())]
    # down_list = [
    #     result_dict[i]['aFRR NI']['Down capacity']['SE3'][0] + result_dict[i]['mFRR NI']['Down capacity']['SE3'][
    #         0] for i in range(result_dict.keys().__len__())]
    results['Up'] = up_list
    results['Down'] = down_list

    odin_dict = {}
    odin_path = 'C:\\Users\\hnordstr\\OneDrive - KTH\\box_files\\KTH\\Papers&Projects\\FRRDimensioning\\odin_2020_weather2016\\'
    areas = ('SE1', 'SE2', 'SE3', 'SE4', 'NO1', 'NO2', 'NO3', 'NO4', 'NO5', 'DK2', 'FI')
    # areas = ['SE3']
    demand_sum = pd.DataFrame(columns=['Demand'])
    demand_sum['Demand'] = [0 for n in range(365 * 24)]
    for a in areas:
        odin_dict[a] = pd.read_csv(f'{odin_path}{a}.csv')
        #print(odin_dict[a].keys())
        demand_sum['Demand'] = demand_sum['Demand'] + odin_dict[a]['Demand'][:8760] * 1000
    demand_list = [demand_sum['Demand'][n*24: (n+1)*24].sum() for n in range(365)]

    # fig,ax1 = plt.subplots()
    # ax2 = ax1.twinx()
    # ax1.set_xlabel('Date')
    # ax1.set_ylabel('Reserve capacity [MW]')
    # ax2.set_ylabel('Wind forecast [MW]')
    # lns3 = ax2.plot(wind_list, label='Wind', color='black', linestyle='--')
    # lns1 = ax1.plot(results['Up'].tolist(), label='Up reserves')
    # lns2 = ax1.plot(results['Down'].tolist(), label='Down reserves')
    # lns= lns1 + lns2 + lns3
    # labs = [l.get_label() for l in lns]
    # ax1.legend(lns, labs)
    plt.rcParams.update({'font.size': 12})
    fig, axs = plt.subplots(nrows=2, sharex=True)
    b, a = np.polyfit(demand_list, results['Up'].tolist(), deg=1)
    xse1 = np.linspace(0.98* min(demand_list), 1.02 * max(demand_list), num = 1000)
    axs[0].plot(xse1, a + b * xse1, color='black', linewidth=2)
    axs[0].scatter(demand_list, results['Up'].tolist(), label='Up', alpha=0.5, color='blue')
    axs[0].set_xlim(0.98*min(demand_list), 1.02 * max(demand_list))
    axs[1].set_xlabel('Demand forecast [MWh]')
    axs[0].set_ylabel('FRR-NI capacity [MW]')
    axs[0].legend()
    axs[0].grid()

    b, a = np.polyfit(demand_list, results['Down'].tolist(), deg=1)
    xse1 = np.linspace(0.98* min(demand_list), 1.02 * max(demand_list), num = 1000)
    axs[1].plot(xse1, a + b * xse1, color='black', linewidth=2)
    axs[1].scatter(demand_list, results['Down'].tolist(), label='Down', alpha=0.5, color='orange')
    axs[1].set_xlim(0.98*min(demand_list), 1.02 * max(demand_list))
    #axs[1].set_xlabel('Wind generation forecast [MWh]')
    axs[1].set_ylabel('FRR-NI capacity [MW]')
    axs[1].legend()
    axs[1].grid()
    plt.tight_layout()
    save=True
    if save:
        fig.savefig(
            f'C:\\Users\\hnordstr\\OneDrive - KTH\\box_files\\KTH\\Papers&Projects\\DynamicFRR\\DemandPlot.pdf',
            dpi=fig.dpi, pad_inches=0, bbox_inches='tight')
    plt.show()

plot_vs_wind()