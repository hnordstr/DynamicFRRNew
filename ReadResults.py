import pickle as pkl
import json
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
# with open(f'{result_path}\\DynamicPreDA\\Day_2019-03-01_Scenarios_15_RIs_22_WC_ATC_0.pickle','rb') as handle:
#     data = pkl.load(handle)
#
# print(f"RI capacity: {float(data['RI']['Up capacity'].sum(axis=1))}")
# print(f"aFRR capacity: {float(data['aFRR NI']['Up capacity'].sum(axis=1))}")
# print(f"mFRR capacity: {float(data['mFRR NI']['Up capacity'].sum(axis=1))}")



# scenario_dict = {}
# for i in [10, 15]:
#     for n in [10,20]:
#         with open(f'{result_path}\\DynamicPreDA\\Day_2019-10-01_Scenarios_{i}_RIs_10.pickle','rb') as handle:
#             scenario_dict[i] = pkl.load(handle)
#             print(f'Scenarios: {i}, RIs: {n}')
#             print(scenario_dict[i]['RI']['Up capacity'].sum(axis=1)[0])
#             print(scenario_dict[i]['FRR NI']['Up capacity'].sum(axis=1)[0])

# stat_dict = {}
# with open(f'{result_path}\\Static\\Start_2019-01-01_Days_365.pickle','rb') as handle:
#     static = pkl.load(handle)
#     imb = static['Netting']['Netted imbalances']
#     plt.plot(imb['NO2'][:3600])
#     plt.show()
#     stat_up = static['RI']['Up capacity'].sum(axis=1)[0] + static['FRR NI']['Up capacity'].sum(axis=1)[0]
#     stat_down = static['RI']['Down capacity'].sum(axis=1)[0] + static['FRR NI']['Down capacity'].sum(axis=1)[0]


# start = datetime.strptime('2019-01-01', '%Y-%m-%d')
# dates = [start + timedelta(days=d) for d in range(100)]
#
# pre_da = pd.DataFrame(columns=['Up tot', 'Down tot'], index=list(range(365)))
# post_da = pd.DataFrame(columns=['Up tot', 'Down tot'], index=list(range(365)))
#
# i = 0
# for d in dates:
#     with open(f'{result_path}\\DynamicPreDA\\Day_{datetime.strftime(d, "%Y-%m-%d")}_Scenarios_15_RIs_22_WC.pickle', 'rb') as handle:
#         results = pkl.load(handle)
#         pre_da['Up tot'][i] = results['RI']['Up capacity'].sum(axis=1)[0] + results['FRR NI']['Up capacity'].sum(axis=1)[0]
#         pre_da['Down tot'][i] = results['RI']['Down capacity'].sum(axis=1)[0] + results['FRR NI']['Down capacity'].sum(axis=1)[0]
#     # with open(f'{result_path}\\DynamicPostDA\\Day_{datetime.strftime(d, "%Y-%m-%d")}_Scenarios_15_RIs_22_WC.pickle','rb') as handle:
#     #     results = pkl.load(handle)
#     #     post_da['Up tot'][i] = results['RI']['Up capacity'].sum(axis=1)[0]  + results['FRR NI']['Up capacity'].sum(axis=1)[0]
#     #     post_da['Down tot'][i] = results['RI']['Down capacity'].sum(axis=1)[0]  + results['FRR NI']['Down capacity'].sum(axis=1)[0]
#     i+=1



# Line plots total FRR
# plt.plot(pre_da['Up tot'].tolist(), label=f'Dynamic pre-DA, mean = {round(pre_da["Up tot"].mean(),2)}')
# plt.plot(post_da['Up tot'].tolist(), label=f'Dynamic post-DA, mean = {round(post_da["Up tot"].mean(),2)}')
# plt.axhline(stat_up, label=f'Static = {round(stat_up, 2)}', color='black')
# plt.xlabel('Days')
# plt.ylabel('FRR [MW]')
# plt.legend()
# plt.title('Upwards FRR')
# plt.show()
#
# plt.plot(pre_da['Down tot'].tolist(), label=f'Dynamic pre-DA, mean = {round(pre_da["Down tot"].mean(), 2)}')
# plt.plot(post_da['Down tot'].tolist(), label=f'Dynamic post-DA, mean = {round(post_da["Down tot"].mean(),2)}')
# plt.axhline(stat_down, label=f'Static = {round(stat_down, 2)}', color='black')
# plt.xlabel('Days')
# plt.ylabel('FRR [MW]')
# plt.legend()
# plt.title('Downwards FRR')
# plt.show()


# #Read static
# no_zones = ['NO1', 'NO2', 'NO3', 'NO4', 'NO5']
# se_zones = ['SE1', 'SE2', 'SE3', 'SE4']
# results = pd.DataFrame(columns=['RI', 'aFRR', 'mFRR'], index=['SE', 'NO', 'DK', 'FI', 'Total'])
# with open(f'{result_path}\\Static\\Start_2019-01-01_Days_270_05.pickle','rb') as handle:
#    static = pkl.load(handle)
#
# results['RI']['FI'] = static['RI']['Up capacity']['FI'][0]
# results['aFRR']['FI'] = static['aFRR NI']['Up capacity']['FI'][0]
# results['mFRR']['FI'] = static['mFRR NI']['Up capacity']['FI'][0]
# results['RI']['DK'] = static['RI']['Up capacity']['DK2'][0]
# results['aFRR']['DK'] = static['aFRR NI']['Up capacity']['DK2'][0]
# results['mFRR']['DK'] = static['mFRR NI']['Up capacity']['DK2'][0]
#
# ri = 0
# afrr = 0
# mfrr = 0
# for a in no_zones:
#     ri += static['RI']['Up capacity'][a][0]
#     afrr += static['aFRR NI']['Up capacity'][a][0]
#     mfrr += static['mFRR NI']['Up capacity'][a][0]
#
# results['RI']['NO'] = ri
# results['aFRR']['NO'] = afrr
# results['mFRR']['NO'] = mfrr
#
# ri = 0
# afrr = 0
# mfrr = 0
# for a in se_zones:
#     ri += static['RI']['Up capacity'][a][0]
#     afrr += static['aFRR NI']['Up capacity'][a][0]
#     mfrr += static['mFRR NI']['Up capacity'][a][0]
#
# results['RI']['SE'] = ri
# results['aFRR']['SE'] = afrr
# results['mFRR']['SE'] = mfrr
#
# results['RI']['Total'] = results['RI'].sum()
# results['aFRR']['Total'] = results['aFRR'].sum()
# results['mFRR']['Total'] = results['mFRR'].sum()
#
# print(results)

# #Read pre-da to csv
# start = datetime.strptime('2019-01-01', '%Y-%m-%d')
# dates = [start + timedelta(days=d) for d in range(365)]
#
# pre_da_up = []
# pre_da_down = []
# labels = []
# pre_da = pd.DataFrame(columns=['Date', 'Uptot', 'Downtot'])
#
# i = 0
# for d in dates:
#     with open(f'{result_path}\\DynamicPreDA_01\\Day_{datetime.strftime(d, "%Y-%m-%d")}_Scenarios_15_RIs_22_WC.pickle',
#               'rb') as handle:
#         results = pkl.load(handle)
#     up = 0
#     down = 0
#     for a in areas:
#         up += results['RI']['Up capacity'][a][0] + \
#                               results['FRR NI']['Up capacity'][a][0]
#         down += results['RI']['Down capacity'][a][0] + \
#                               results['FRR NI']['Down capacity'][a][0]
#     pre_da_up.append(up)
#     pre_da_down.append(down)
#     labels.append(i)
#     i += 1
# pre_da['Date'] = labels
# pre_da['Uptot'] = pre_da_up
# pre_da['Downtot'] = pre_da_down
# pre_da = pre_da.set_index('Date')
# print((pre_da['Uptot'].mean() + pre_da['Downtot'].mean())/2)
# pre_da.to_csv('pre_da.csv')

# Analyse pre-DA

start = datetime.strptime('2019-01-01', '%Y-%m-%d')
dates = [start + timedelta(days=d) for d in range(365)]

pre_da_up = []
pre_da_down = []
labels = []
pre_da = pd.DataFrame(columns=['Date', 'Uptot', 'Downtot'])

i = 0
for d in dates:
    with open(f'{result_path}\\DynamicPreDA_01\\Day_{datetime.strftime(d, "%Y-%m-%d")}_Scenarios_15_RIs_22_WC.pickle',
              'rb') as handle:
        results = pkl.load(handle)
    up = 0
    down = 0
    for a in areas:
        up += results['RI']['Up capacity'][a][0]
        down += results['RI']['Down capacity'][a][0]
    pre_da_up.append(up)
    pre_da_down.append(down)
    labels.append(datetime.strftime(d, "%Y-%m-%d"))
    i += 1
pre_da['Date'] = labels
pre_da['Uptot'] = pre_da_up
pre_da['Downtot'] = pre_da_down
pre_da = pre_da.set_index('Date')
pre_da = pre_da.sort_values(by='Uptot', ascending=False)
print(pre_da)

# Read post-da to csv
# start = datetime.strptime('2019-01-01', '%Y-%m-%d')
# dates = [start + timedelta(days=d) for d in range(365)]
#
# post_da_up = []
# post_da_down = []
# labels = []
# post_da = pd.DataFrame(columns=['Date', 'Uptot', 'Downtot'])
#
# i = 0
# for d in dates:
#     with open(f'{result_path}\\DynamicPostDA_01\\Day_{datetime.strftime(d, "%Y-%m-%d")}_Scenarios_15_RIs_22_WC.pickle',
#               'rb') as handle:
#         results = pkl.load(handle)
#     up = 0
#     down = 0
#     for a in areas:
#         up += results['RI']['Up capacity'][a][0] + \
#                               results['FRR NI']['Up capacity'][a][0]
#         down += results['RI']['Down capacity'][a][0] + \
#                               results['FRR NI']['Down capacity'][a][0]
#     post_da_up.append(up)
#     post_da_down.append(down)
#     labels.append(i)
#     i += 1
# post_da['Date'] = labels
# post_da['Uptot'] = post_da_up
# post_da['Downtot'] = post_da_down
# post_da = post_da.set_index('Date')
# print((post_da['Uptot'].mean() + post_da['Downtot'].mean())/2)
#post_da.to_csv('post_da.csv')

#
# #Coropleth plot Static
#read per area
# stat_up = pd.DataFrame(columns=['Reserves', 'id'] )
# stat_down = pd.DataFrame(columns=['Reserves', 'id'])
# with open(f'{result_path}\\Static\\Start_2019-01-01_Days_270_01.pickle','rb') as handle:
#    static = pkl.load(handle)
# #
# stat_up['Reserves'] = [static['RI']['Up capacity'][a][0] + static['FRR NI']['Up capacity'][a][0] for a in areas]
# stat_down['Reserves'] = [static['RI']['Down capacity'][a][0] + static['FRR NI']['Down capacity'][a][0] for a in areas]

# stat_up['id'] = [a for a in areas]
# stat_down['id'] = [a for a in areas]
#
#
# ## plot per area
# maps_in = gpd.read_file('C:\\Users\\hnordstr\\OneDrive - KTH\\box_files\KTH\\Papers&Projects\\DynamicFRR\\nordic.geojson')
# maps_in = json.loads(maps_in.to_json())
# maps = geojson_rewind.rewind(maps_in, rfc7946=False)
#
# for f in maps['features']:
#    f['id'] = f['properties']['name']
#
# fig = px.choropleth(stat_down,
#                    locations='id',
#                    geojson=maps,
#                    featureidkey='id',
#                    color='Reserves',
#                    hover_name='id',
#                    color_continuous_scale=px.colors.sequential.Viridis,
#                    range_color=[0, 1600],
#                    scope='europe')
# fig.update_geos(fitbounds="locations", visible=False)
# fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
# fig.update_layout(coloraxis_colorbar=dict(
#    ticks="outside", ticksuffix=" MW",
#    dtick=400, len=0.8, thickness=50, y=0.53,x=0.67,
#    title=dict(text='FRR', font=dict(size=60))
# ))
# fig.update_coloraxes(colorbar_tickfont_size=60)
#
# fig.show()


# # Choropleth plot pre-DA
# start = datetime.strptime('2019-01-01', '%Y-%m-%d')
# dates = [start + timedelta(days=d) for d in range(365)]
#
# pre_da_up = pd.DataFrame(columns=areas, index=list(range(365)))
# pre_da_down = pd.DataFrame(columns=areas, index=list(range(365)))
#
# i = 0
# for d in dates:
#     with open(f'{result_path}\\DynamicPreDA_01\\Day_{datetime.strftime(d, "%Y-%m-%d")}_Scenarios_15_RIs_22_WC.pickle',
#               'rb') as handle:
#         results = pkl.load(handle)
#         for a in areas:
#             pre_da_up[a][i] = results['RI']['Up capacity'][a][0] + \
#                                   results['FRR NI']['Up capacity'][a][0]
#             pre_da_down[a][i] = results['RI']['Down capacity'][a][0] + \
#                                   results['FRR NI']['Down capacity'][a][0]
#     i += 1
#
# preda_up = pd.DataFrame(columns=['Reserves', 'id'])
# preda_down = pd.DataFrame(columns=['Reserves', 'id'])
#
# preda_up['Reserves'] = [pre_da_up[a].mean() for a in areas]
# preda_down['Reserves'] = [pre_da_down[a].mean() for a in areas]
# preda_up['id'] = [a for a in areas]
# preda_down['id'] = [a for a in areas]
# ## plot per area
# maps_in = gpd.read_file('C:\\Users\\hnordstr\\OneDrive - KTH\\box_files\KTH\\Papers&Projects\\DynamicFRR\\nordic.geojson')
# maps_in = json.loads(maps_in.to_json())
# maps = geojson_rewind.rewind(maps_in, rfc7946=False)
#
# for f in maps['features']:
#     f['id'] = f['properties']['name']
#
# fig = px.choropleth(preda_down,
#                     locations='id',
#                     geojson=maps,
#                     featureidkey='id',
#                     color='Reserves',
#                     hover_name='id',
#                     color_continuous_scale=px.colors.sequential.Viridis,
#                     range_color=[0, 1600],
#                     scope='europe')
# fig.update_geos(fitbounds="locations", visible=False)
# fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
# fig.update_layout(coloraxis_colorbar=dict(
#     ticks="outside", ticksuffix=" MW",
#     dtick=200, len=0.8, thickness=50, y=0.53,x=0.67,
#     title=dict(text='FRR', font=dict(size=30))
# ))
# fig.update_coloraxes(colorbar_tickfont_size=30)
#
# fig.show()

## Choropleth plot post-DA
# start = datetime.strptime('2019-01-01', '%Y-%m-%d')
# dates = [start + timedelta(days=d) for d in range(100)]
#
# post_da_up = pd.DataFrame(columns=areas, index=list(range(365)))
# post_da_down = pd.DataFrame(columns=areas, index=list(range(365)))
#
# i = 0
# for d in dates:
#     with open(f'{result_path}\\DynamicPostDA_01\\Day_{datetime.strftime(d, "%Y-%m-%d")}_Scenarios_15_RIs_22_WC.pickle',
#               'rb') as handle:
#         results = pkl.load(handle)
#         for a in areas:
#             post_da_up[a][i] = results['RI']['Up capacity'][a][0] + \
#                                   results['FRR NI']['Up capacity'][a][0]
#             post_da_down[a][i] = results['RI']['Down capacity'][a][0] + \
#                                   results['FRR NI']['Down capacity'][a][0]
#     i += 1
#
# postda_up = pd.DataFrame(columns=['Reserves', 'id'])
# postda_down = pd.DataFrame(columns=['Reserves', 'id'])
#
# postda_up['Reserves'] = [post_da_up[a].mean() for a in areas]
# postda_down['Reserves'] = [post_da_down[a].mean() for a in areas]
# postda_up['id'] = [a for a in areas]
# postda_down['id'] = [a for a in areas]
# ## plot per area
# maps_in = gpd.read_file('C:\\Users\\hnordstr\\OneDrive - KTH\\box_files\KTH\\Papers&Projects\\DynamicFRR\\nordic.geojson')
# maps_in = json.loads(maps_in.to_json())
# maps = geojson_rewind.rewind(maps_in, rfc7946=False)
#
# for f in maps['features']:
#     f['id'] = f['properties']['name']
#
# fig = px.choropleth(postda_down,
#                     locations='id',
#                     geojson=maps,
#                     featureidkey='id',
#                     color='Reserves',
#                     hover_name='id',
#                     color_continuous_scale=px.colors.sequential.Viridis,
#                     range_color=[0, 1600],
#                     scope='europe')
# fig.update_geos(fitbounds="locations", visible=False)
# fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
# fig.update_layout(coloraxis_colorbar=dict(
#     ticks="outside", ticksuffix=" MW",
#     dtick=200, len=0.8, thickness=50, y=0.53,x=0.67,
#     title=dict(text='FRR', font=dict(size=30))
# ))
# fig.update_coloraxes(colorbar_tickfont_size=30)
#
# fig.show()