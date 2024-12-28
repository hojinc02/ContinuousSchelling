import pandas as pd
import pickle
import os
from itertools import combinations

race_types = ['White', 'Black or African American', 'American Indian or Alaska Native', 'Asian', 'Native Hawaiian or Other Pacific Islander', 'Some Other Race']
# used for looking through data. name does not fully represent race group
race_aliases = ['white', 'black', 'indian', 'asian', 'pacific', 'some']
num_singular_groups = len(race_aliases)
all_types = []
for i in range(1, len(race_aliases)+1): 
    all_types.extend(combinations(list(range(len(race_aliases))), i))
pkl_path = f'PopulationData/DECENNIALPL2020.P1_2024-08-01T160402/data.pkl'

def load_data(): 
    if not os.path.exists(pkl_path): 
        save_data()

    with open(pkl_path, 'rb') as pklfile: 
        return pickle.load(pklfile)

def save_data(): 
    data_path = f'PopulationData/DECENNIALPL2020.P1_2024-08-01T160402/DECENNIALPL2020.P1-Data.csv'
    separator = ','
    labeldict = get_labeldata()

    categories = [col for col in pd.read_csv(data_path, nrows=1, sep=separator).columns \
                  if col in labeldict]

    data_types = {cat: 'int64' for cat in categories} | {'GEO_ID': 'object'}

    data = pd.read_csv(data_path, skiprows=[1], dtype=data_types, sep=separator, 
                       usecols=data_types.keys())
    data['GEO_ID'] = data['GEO_ID'].str.replace('1500000US', '')
    data = data.rename(columns={cat: labeldict[cat] for cat in categories})
    datadict = data.set_index('GEO_ID').apply(lambda row: row[row != 0].to_dict(), axis=1).to_dict()

    with open(pkl_path, 'wb') as pklfile: 
        pickle.dump(datadict, pklfile)

def get_labeldata(): 
    label_path = f'PopulationData/DECENNIALPL2020.P1_2024-08-01T160402/DECENNIALPL2020.P1-Column-Metadata.csv'

    labeldata = pd.read_csv(label_path, skiprows=[0,1])

    type_to_idx = {all_types[i]:i for i in range(len(all_types))}
    label_to_idx = {}
    for i in range(labeldata.shape[0]): 
        label = labeldata.iloc[i]['Geographic Area Name'].lower()
        name = labeldata.iloc[i]['NAME']

        race_type = []
        for k, r in enumerate(race_aliases): 
            if r.lower() in label: 
                race_type.append(k)

        if len(race_type) == 0: 
            continue
        else: 
            label_to_idx[name] = type_to_idx[tuple(race_type)]
        
    return label_to_idx

if __name__=='__main__': 
    data = save_data()
    
