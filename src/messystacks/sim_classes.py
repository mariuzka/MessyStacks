import pandas as pd
import math
import random
import time
import joblib as jbl
import ast
import itertools
import seaborn as sns
import matplotlib.pyplot as plt
import copy
import celluloid as cld

class Model:
    def __init__(
            self,
            s = None, 
            n = None,
            p = None,
            m = None, 
            n_agents = None,
            avg_util = None,
            n_ticks = None,
            lending_ticks = None,
            dict_get_mode = None,
            dict_return_mode = None,
            save_mode = None,
            scenario = None,
            ):
        
        
        # number of stacks
        assert s > 0
        self.s = int(s)
        
        # max. load / max. number of elements per stack
        self.m = int(m)
        
        # number of elements per stack
        # assert (n and not p) or (not n and p)
        if n:
            assert 0 <= n <= m
            self.n = n
            self.p = n / m 
       
        else:
            assert 0 <= p <= 1
            self.p = p
            self.n = round(m*p)
        
        # total number of elements in the system
        self.total_n = self.n * self.s
        
        # total carrying capacity
        self.total_m = self.m * self.s
        
        # number of simulated time steps
        self.n_ticks = n_ticks
        self.ticks = range(self.n_ticks)
        
        # duration of element use per agent 
        assert lending_ticks < n_ticks
        self.lending_ticks = lending_ticks
        
        # number of agents
        # assert (n_agents and not avg_util) or (not n_agents and avg_util)
        if n_agents:
            self.n_agents = int(n_agents)
            
            # average demand for elements per tick
            self.avg_demand = self.n_agents / self.n_ticks * self.lending_ticks
        
            # average proportion of elements utilized per tick
            if self.total_n > 0:
                self.avg_util = self.avg_demand / self.total_n
            else:
                self.avg_util = 1
            
        else:
            self.avg_util = avg_util
            self.avg_demand = self.total_n * self.avg_util
            self.n_agents = int(round(self.avg_demand / self.lending_ticks * self.n_ticks))
               
        
        # dictionary containing the rel. freqs of        
        self.dict_get_mode = dict_get_mode

        self.dict_return_mode = dict_return_mode
        
        # how the output is saved
        self.save_mode = save_mode
        
        # dataframe for storing the output data
        self.df = pd.DataFrame
        
        self.scenario = scenario
        
    def internal_run(self, rep):
        
        # prepare simulation
        agents = self.create_agents()
        schedule = self.create_schedule(agents)
        stacks = self.create_stacks()
        
        dfs_stacks = []
        
        if self.save_mode in ["one_line", "last_tick"]:
            for t, time_slot in enumerate(schedule):
                for agent in time_slot:
                    agent.get_or_return_element(t, stacks)
        
        elif self.save_mode in ["all"]:
            for t, time_slot in enumerate(schedule):
                dfs_stacks.append(self.create_stacks_df(rep, t, stacks))
                for agent in time_slot:
                    agent.get_or_return_element(t, stacks)
            
        dfs_stacks.append(self.create_stacks_df(rep, t+1, stacks))
        
        df_internal_run = pd.concat(dfs_stacks)
        return df_internal_run
    
    def create_stacks_df(self, rep, tick, stacks):
        df = stacks.df
        df["tick"] = tick
        df["rep"] = rep
        return df
    
    def prepare_output_df(self, dfs):
        
        df = pd.concat(dfs, ignore_index=True)
        df = (
            df
            .sort_values(by=["rep", "tick", "stack_id"])
            .reset_index(drop=True)
            )
        
        # calculate disorder
        df["single_stack_disorder"] = (
            df
            .n_elements
            .apply(lambda x: self.get_single_stack_disorder(x))
            )
        df["disorder"] = (
            df
            .groupby(["rep", "tick"])
            .single_stack_disorder
            .transform(sum)
            )
        df["prop_disorder"] = df.disorder / self.total_m
        
        if self.save_mode == "one_line":
            df = (
                df
                .groupby("rep")
                .first()
                .reset_index(drop=True)
                .iloc[:,4:] # drop single stack variables
                )
        
        # add some model informations
        df["n_agents"] = self.n_agents
        df["p"] = self.p
        df["s"] = self.s
        df["m"] = self.m
        df["n"] = self.n
        df["dict_get_mode"] = str(self.dict_get_mode)
        df["dict_return_mode"] = str(self.dict_return_mode)
        df["avg_demand"] = self.avg_demand
        df["avg_util"] = self.avg_util
        df["max_prop_disorder"] = self.get_max_prop_disorder()
        df["max_disorder"] = df.max_prop_disorder * self.total_m
        df["scenario"] = self.scenario
        
        return df
        
    
    
    def run(self, reps=1, n_cores=1):
        
        start_time = time.time()
        
        # run simulation
        if n_cores > 1:
            dfs = jbl.Parallel(n_jobs=n_cores)(map(jbl.delayed(self.internal_run), list(range(reps))))
        else:
            dfs = [self.internal_run(rep) for rep in range(reps)]
                        
        df = self.prepare_output_df(dfs)
        df["run_time"] = time.time() - start_time
        
        self.df = df
        return df
        
    def get_single_stack_disorder(self, n_elements):
        return max(0, n_elements - self.n)
    
    def get_max_prop_disorder(self):
        
        # number of filled stacks
        fs = self.s * self.p
        
        # number of completely filled stacks
        cfs = math.floor(fs)
        
        # surplus in completely filled stacks
        scfs = cfs*(1-self.p)
        
        # surplus in incompletely filled stacks
        sifs = max(0, fs - cfs - self.p)
        
        # total (proportional) disorder in system of stacks
        proportional_disorder = (scfs + sifs) / self.s
        
        return proportional_disorder
    
    def create_schedule(self, agents):
        
        # create list of lists for each tick
        schedule = [[] for t in self.ticks]
        
        # put agents in corresponding tick-lists
        for agent in agents:
            schedule[agent.tick_get].append(agent)
            schedule[agent.tick_return].append(agent)
        
        return schedule
            
    
    def create_stacks(self):
        return Stacks(self.s, self.n, self.m)
        
    
    def create_mode_list(self, dict_mode):
        """
        Erstellt Listen in denen sich die Verhaltensmodi der Agenten
        in der entsprechenden Häufigkeit befinden.
        Falls durch Rundung die Liste nicht der gewünschten Populationsgröße
        entspricht, wird "random" als Modus angehängt.
        """
        modes = []
        for k in dict_mode.keys():
            modes.extend([k] * math.floor(dict_mode[k]*self.n_agents))
        
        # Ist die Liste so lang wie die Population?
        if len(modes) < self.n_agents:
            for i in range(self.n_agents - len(modes)):
                modes.append("random")
        
        random.shuffle(modes)
        
        return modes
        
    def create_agents(self):
        modes_get = self.create_mode_list(self.dict_get_mode)
        modes_return = self.create_mode_list(self.dict_return_mode)
        ticks_get = [
            random.choice(range(0, self.n_ticks-self.lending_ticks)) 
            for i in range(self.n_agents)
            ]
        
        agents = []
        for i in range(self.n_agents):
            agent = Agent(
                mode_get = modes_get[i],
                mode_return = modes_return[i],
                tick_get = ticks_get[i],
                lending_ticks = self.lending_ticks,
                )
            agents.append(agent)
            
        return agents
    
    def create_animation(self, output_path):
        
        # temporarily change save-mode
        save_mode = self.save_mode
        self.save_mode = "all"
        
        # run the model one time
        df = self.run()
        
        # undo the change of self.save_only_last_tick
        self.save_mode = save_mode
        
        # create animation
        fig, ax = plt.subplots()
        camera = cld.Camera(fig)
        
        for t in self.ticks:
            df_temp = df[df.tick == t]
        
            ax.bar(df_temp.stack_id, [self.n for i in range(self.s)], color = "red")
            ax.bar(df_temp.stack_id, df_temp.n_elements, color="black")
            ax.set(ylim=[0, self.m])
            camera.snap()
        animation = camera.animate()
        animation.save(output_path)
        return animation



class Stacks:
    def __init__(self, s, n, m):
        self.s = s
        self.n = n 
        self.m = m
        self.df = pd.DataFrame({
            "stack_id": range(s),
            "n_elements": [n for i in range(s)],
            })
    
    def sort_stacks(self, mode):
        
        # random stack selection
        if mode == "random":
            self.df = self.df.sample(frac=1)
        
        # select the stack with smallest number of elements
        elif mode == "min":
            self.df = self.df.sort_values(
                by = "n_elements", 
                ascending = True,
                )
        
        # select stack with highest number of elements
        elif mode == "max":
            self.df = self.df.sort_values(
                by = "n_elements", 
                ascending = False,
                )
            
        # randomly select stacks weighted by f(n_elements)
        elif mode == "weighted_max":
            self.df["weight1"] = (self.df.n_elements + 1)
            self.df = self.df.sample(frac=1, weights="weight1", replace=False)
        
        # add some jitter around n_elements and 
        elif mode == "jitter_max":
            self.df["jitter_n_elements"] = self.df.n_elements.apply(lambda x: x + random.randint(-x, x))
            
            self.df = self.df.sort_values(
                by = "jitter_n_elements", 
                ascending = False,
                )
            
        self.df = self.df.reset_index(drop = True)
        

class Agent:
    def __init__(
            self, 
            mode_get, 
            mode_return,
            tick_get,
            lending_ticks,
            ):
        self.mode_get = mode_get
        self.mode_return = mode_return
        self.tick_get = tick_get
        self.tick_return = tick_get + lending_ticks
        self.element = False
    
    def get_element(self, stacks):
        if not self.element:
            stacks.sort_stacks(self.mode_get)
            
            for i in stacks.df.index:
                if stacks.df.loc[i, "n_elements"] > 0:
                    stacks.df.loc[i, "n_elements"] -= 1
                    self.element = True
                    break
    
    def return_element(self, stacks):
        if self.element:
            stacks.sort_stacks(self.mode_return)
            for i in stacks.df.index:
                if stacks.df.loc[i, "n_elements"] < stacks.m:
                    stacks.df.loc[i, "n_elements"] += 1
                    self.element = False
                    break


    def get_or_return_element(self, tick, stacks):
        """Evaluates the given time step (tick) and decides whether it is the agent's turn to pick up or return an element."""
        
        if tick == self.tick_get:
            self.get_element(stacks)
        
        if tick == self.tick_return:
            self.return_element(stacks)
