import src
from src.messystacks import utils

import pandas as pd
import numpy as np


S = 4
M = 40
N_AGENTS = 1000
LENDING_TICKS = 20
N_TICKS = 12*60
STEP = 0.05

params_dict = {
    "s": [S-1, S, S+1],
    "n": [None],
    "p": list(np.arange(0, 1.01, STEP)),
    "m": [M-20, M, M+20],
    "n_agents": [N_AGENTS],
    "avg_util": [None],
    "n_ticks": [N_TICKS],
    "lending_ticks": [LENDING_TICKS],
    "save_mode": ["one_line"],
    "dict_get_mode": [],
    "dict_return_mode": [],
    "scenario" : [],
    }
df_params = pd.concat([
    utils.create_df_params(utils.add_1_strategy(params_dict, "random")), 
    utils.create_df_params(utils.add_1_strategy(params_dict, "max")),
    #utils.create_df_params(utils.add_1_strategy(params_dict, "weighted_max")),
    ]).reset_index(drop=True)

# run experiment
df_experiment = utils.run_experiment(df_params, reps = 4, n_cores = 4)

# save data
df_experiment.to_csv(str(src.PATH) + "/data/output/experiment1_pstep05.csv", index=False)