import copy
import math
import itertools
import pandas as pd
import time
import statistics

from src.messystacks.sim_classes import Model

def create_df_params(params_dict):
    
    # get list of list of values from dict
    values = list(params_dict.values())
    
    # get all combinations of elements across lists
    combinations = list(itertools.product(*values))
    combinations = [list(c) for c in combinations]
    
    # create dataframe containing rows of unique parameter combinations
    df = pd.DataFrame(combinations, columns=list(params_dict.keys()))
      
    return df

def get_progress(i, max_i):
    return round((i/max_i)*100)

def run_experiment(df_params, reps, n_cores):
    
    df_params = df_params.reset_index(drop=True)
    
    dfs = []
    
    progress = 0
    comp_times = []

    start_time = time.time()
    for i in df_params.index:
        
        progress_temp = get_progress(i, len(df_params))
        if progress != progress_temp:
            end_time = time.time()
            comp_times.append(end_time - start_time)
            start_time = end_time
            
            # mean_time_per_step = sum(comp_times)/len(comp_times)
            median_time_per_step = statistics.median(comp_times)
            minutes_running = round(sum(comp_times)/60, 2)
            hours_running = round(minutes_running/60, 2)

            minutes_remaining = round((median_time_per_step * (100-progress)) / 60, 2)
            hours_remaining = round(minutes_remaining / 60, 2)

            

            progress = progress_temp
            
            print(
                "progress:", progress, "%", "---",
                "minutes running:", minutes_running, "---",
                "hours running:", hours_running, "---",
                "minutes remaining:", minutes_remaining, "---",
                "hours remaining:", hours_remaining, "---",
                )
        
        params_dict = df_params.iloc[i,:].to_dict()
        model = Model(**params_dict)
        results = model.run(reps = reps, n_cores = n_cores)
        dfs.append(results)
    df = pd.concat(dfs)
    return df

def get_max_mess(s, m, n):
    fs = s*n/m
    cfs = math.floor(fs)
    return cfs*(m-n) + max(0, (fs-cfs-n/m)*m)

def max_mess_for_each(dict_params):
    df_params = create_df_params(dict_params)
    df = copy.deepcopy(df_params)
    df["max_mess"] = 0
    for i in df_params.index:
        params = [df_params.iloc[i, j] for j in range(len(df_params.columns))]
        df.loc[i, "max_mess"] = get_max_mess(*params)
    return df
    
def add_1_strategy(params_dict, strategy):
    d = copy.deepcopy(params_dict)
    d["dict_get_mode"] = [{strategy:1}]
    d["dict_return_mode"] = [{strategy:1}]
    d["scenario"] = [strategy]
    return d