from pathlib import Path
from collections import OrderedDict
from datetime import datetime
import time, sys, copy, json, numpy as np, pandas as pd, progress

base_path = Path(__file__).parent.parent
script_path = base_path / "Scripts"
submodule_path = base_path / "BayesianOptimization"
if str(script_path) not in sys.path: sys.path.append(str(script_path))
if str(submodule_path) not in sys.path: sys.path.append(str(submodule_path))

from bayes_opt import BayesianOptimization, SequentialDomainReductionTransformer
from bayes_opt.logger import JSONLogger # Log progress
from bayes_opt.util import load_logs # Allow pause/start
from bayes_opt.event import Events # Subscription to Optimisation events
from sklearn.gaussian_process.kernels import Matern
from Measurements_Visualisation import choose_run_and_metric, extract_points, match_real_and_simulated
from Extract_Simulation_Hyperparameters import *
from XML_Tools import SimParam, HyperParameters

class CaseInfo():
    def __init__(self):
        case_path, case_name = select_case()
        case_def, tree = parse_case(case_path)

        self.case_path = case_path
        self.case_name = case_name
        self.case_def = case_def
        self.tree = tree

def sim_real_difference(file, points, method="mad", delay=0, batch=0):
    df_simul = pd.read_csv(file, sep=";", index_col=0, header=1)

    dfs_real = {}
    for point in points.values():
        loc = int(point[0])
        height = "Bottom" if point[2] < 0.8 else "Top" if point[2] > 1.2 else "Middle"
        dfs_real[loc] = pd.read_csv(script_path / "Real_Data" / f"Data_Depth{1000}mm_Upstream{loc}m_{height}.txt",
                                    sep="\s", names=["Time","Velocity"], engine="python")
    running_sum = 0
    for point_no, point in points.items():
        loc = int(point[0]) # Position downstream from Turbine (located at X=4m)
        simulated_x_velocity = df_simul[f"Vel_{point_no}.x [m/s]"][delay:] # Optional delay allows for simulation to stabilise
        batch_size = len(simulated_x_velocity)
        # Compare to real data, shifted by batch_number. Delay not needed here. 
        real_x_velocity = dfs_real[loc]["Velocity"]
        real_x_velocity = np.roll(real_x_velocity, batch*batch_size)[0: batch_size] # Will eventually wrap around
        if method == "mad": # Mean Absolute Difference
            abs_differences = np.absolute(np.subtract(simulated_x_velocity, real_x_velocity))
            running_sum += np.mean(abs_differences)
        elif method == "mse": # Mean Square Error
            square_dist = np.power(np.subtract(simulated_x_velocity, real_x_velocity), 2)
            running_sum += np.mean(square_dist)
    average_distance = running_sum / len(points) # Taking mean of subsets == mean of all data
    return 1.0 / average_distance # Inverted as we want to minimise the objective

def objective(**kwargs):
    global BATCH_NO, DELAY, REAL_DURATION, OS, RUN_TIMES
    # >> Convert Kwargs to Simulation Parameters <<
    params = HyperParameters()
    for SimParamStr, value in kwargs.items(): # Kwargs are ORDERED, see PEP 468
        param = SimParam.from_slug(SimParamStr)
        if param.type in [np.float, np.float16, np.float32, np.float64, np.double, np.longdouble]: # Continuous
            params[param] = str(value) # String ensures it is serialisable
        else:
            params[param] = str(param.type(value)) # Cast to discrete parameter
    swap_params(case.tree.getroot(), params)
    set_duration_and_freq(case.tree, duration=REAL_DURATION, freq=1.0/120.0) # Should be fixed
    update_case_file(case.tree, case.case_def, case.case_name, verbose=False)
    

    timestamp = datetime.now().strftime("%d_%m_%Y_%Hh_%Mm_%Ss")
    # >> Run the simulation (warning: SLOW) <<
    duration = run_simulation(case.case_def, case.case_name, os=OS, timestamp=timestamp, copy_measurements=True, verbose=False)
    RUN_TIMES.append(duration)

    measure_dir = Path(__file__).parent / "Measurements" / (case.case_name + "_" + timestamp)
    file_path = measure_dir / (case.case_path.name + "_Vel.csv")

    points, columns = extract_points(file_path, verbose=False)
    
    target = sim_real_difference(file_path, points, method="mse", delay=DELAY, batch=BATCH_NO)
    BATCH_NO = BATCH_NO + 1
    return target

def select_log(optimizer, log_dir):
    file_names = {i: f.name for i, f in enumerate(log_dir.glob("*.json"))}
    if len(file_names) < 1:
        print(f"{C.RED}{C.BOLD}Warning{C.END}: No previous sessions exist")
        return optimizer
    print("\n".join([f"{i}: {file_names[i]}" for i in range(len(file_names)) if i in file_names]))
    while (resp := input("Please select a previous session's log by number")):
        if resp.isdigit():
            if int(resp) in file_names:
                file_name = file_names[int(resp)]
                break
    load_logs(optimizer, logs=[str(log_dir / file_name)])
    print(f"{C.CYAN}{C.BOLD}INFO{C.END}: Optimizer is now aware of {len(optimizer.space)} points.")  
    return optimizer

OS = "win64"
SESSION_ID = datetime.now().strftime("%d_%m_%Y_%Hh_%Mm_%Ss")
REAL_DURATION = 0.1 # In Seconds
DELAY = 1 # In Time Steps (~120 steps per second)
if (DELAY / 120.0) > REAL_DURATION:
    raise ValueError("Delay too large relative to the simulation duration")
RUN_TIMES = []
BATCH_NO = 0 # Real data batch index to compare simulated data to
case = CaseInfo()

params, _ = find_simulation_parameters(case.tree, file_name=None,
                                                  swap=False, record=False, verbose=False)

# Use panning and zooming on initial bounds to encourage faster convergence
bounds_transformer = SequentialDomainReductionTransformer()

optimizer = BayesianOptimization(    
    f=objective, # Want to control optimisation more finely
    pbounds=params.get_bounds(),
    verbose=2, # verbose = 1 prints only when a maximum is observed, verbose = 0 is silent
    random_state=1,
    bounds_transformer=bounds_transformer,
)

# >> Logging / Pausing <<
log_path = script_path / "Logs" / f"{SESSION_ID}_OPTIMIZATION_LOG.json"
if not log_path.parent.exists():
    log_path.parent.mkdir()
logger = JSONLogger(path=str(log_path))
optimizer.subscribe(Events.OPTIMIZATION_STEP, logger)

while (resp := input("Load previous session? 'Y' (yes) 'N' (no)")).strip().lower() not in ["y", "n"]:
    continue
if resp.strip().lower() == "y":
    optimizer = select_log(optimizer, log_dir=log_path.parent)

#  Init_points: How many steps of **random** exploration you want to perform.
#  n_iter: How many steps of bayesian optimization you want to perform.
optimizer.maximize(init_points=max(5 - len(optimizer.space), 0), # If previous session already explored space, don't do it again
            n_iter=15,
            acq='ucb', # UCB: Upper Confidence Bound, EI: Expected Improvement, # POI: Probability of Improvement 
            kappa=2.576, # High: Prefer Exploration, Low: Prefer Exploitation
            kappa_decay=1, # Kappa is multiplied by this every iteration
            kappa_decay_delay=0, # Wait before starting with decay
            xi=0.0, # Used by EI and POI, 0.1=Exploration, 0.0=Exploitation
            # Parameters for internal Gaussian Process Regressor:
            kernel=Matern(nu=2.5), #  [Default: Mattern 2.5 kernel]. Specific to problem. Recommended not to change.
            alpha=1e-3, # [Default 1e-6] Controls how much noise GP can handle, increase for discrete parameters. 
            normalize_y=True, # [{]Default: True] Normalise mean 0 variance 1, recommended for unit-normalized priors
            n_restarts_optimizer=5, # [Default: 5] Used to optimize kernel hyperparameters!
)

print(f"{C.BOLD}Run Times (HH:MM:SS){C.END}:\n", "\n".join([f"Iter {i}: {rt}" for i, rt in enumerate(RUN_TIMES)]))
print(f"{C.BOLD}{C.PURPLE}Max of Optimized Combinations{C.END}:\n{optimizer.max}")