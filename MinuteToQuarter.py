import pandas as pd

"""Takes minute resolution imbalances and atc and generates quarter-hourly data
Example run: slow_imbalance, fast_imbalance, atc = minute_to_quarter(df_imbalance, df_atc)
"""

def minute_to_quarter(imbalance, atc_pos_in, atc_neg_in):
    areas = ('SE1', 'SE2', 'SE3', 'SE4', 'NO1', 'NO2', 'NO3', 'NO4', 'NO5', 'DK2', 'FI')
    #quarters = int(imbalance.__len__() / 15)
    quarters = int(imbalance.__len__() / 5)
    slow_imbalances = pd.DataFrame(index=list(range(quarters)), columns=areas)
    fast_imbalances = pd.DataFrame(index=list(range(quarters)), columns=areas)
    atc_pos = pd.DataFrame(index=list(range(quarters)), columns=atc_pos_in.columns.tolist())
    atc_neg = pd.DataFrame(index=list(range(quarters)), columns=atc_neg_in.columns.tolist())

    for l in atc_pos.columns.tolist():
        #atc_pos[l] = [atc_pos_in[l][x * 15: (x + 1) * 15].mean() for x in range(quarters)]
        #atc_neg[l] = [atc_neg_in[l][x * 15: (x + 1) * 15].mean() for x in range(quarters)]
        atc_pos[l] = [atc_pos_in[l][x * 5] for x in range(quarters)]
        atc_neg[l] = [atc_neg_in[l][x * 5] for x in range(quarters)]

    for a in areas:
        fifteen_min_rolling = imbalance[a].rolling(window=15).mean()
        for i in range(15):
            fifteen_min_rolling[i] = fifteen_min_rolling[15]
        five_min_rolling = imbalance[a].rolling(window=5).mean()
        for i in range(5):
            five_min_rolling[i] = five_min_rolling[5]
        # take the value in middle of each quarter
        #slow_imbalances[a] = [five_min_rolling[x * 15 + 7] for x in range(quarters)]
        #fast_imbalances[a] = [five_min_rolling[x * 15 + 7] - fifteen_min_rolling[x * 15 + 7] for x in range(quarters)]
        slow_imbalances[a] = [five_min_rolling[x * 5] for x in range(quarters)]
        fast_imbalances[a] = [five_min_rolling[x * 5] - fifteen_min_rolling[x * 5] for x in range(quarters)]

    return slow_imbalances, fast_imbalances, atc_pos, atc_neg