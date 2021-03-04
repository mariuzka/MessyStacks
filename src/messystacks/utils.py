def create_df_params(params_dict):
    
    # get list of list of values from dict
    values = list(params_dict.values())
    
    # get all combinations of elements across lists
    combinations = list(itertools.product(*values))
    combinations = [list(c) for c in combinations]
    
    # create dataframe containing rows of unique parameter combinations
    df = pd.DataFrame(combinations, columns=list(params_dict.keys()))
      
    return df

def run_experiment(df_params, reps, n_cores):
    dfs = []
    for i in df_params.index:
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