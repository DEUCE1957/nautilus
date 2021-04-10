from datetime import datetime
import os, sys, argparse, numpy as np, numpy
from pathlib import Path
from sklearn.gaussian_process.kernels import Matern

base_path = Path(__file__).parent.parent
script_path = base_path / "Scripts"
submodule_path = base_path / "BayesianOptimization"
if str(script_path) not in sys.path: sys.path.append(str(script_path))
if str(submodule_path) not in sys.path: sys.path.append(str(submodule_path))

from bayes_opt import BayesianOptimization, SequentialDomainReductionTransformer
from bayes_opt.logger import JSONLogger # Log progress
from bayes_opt.util import load_logs # Allow pause/start
from bayes_opt.event import Events # Subscription to Optimisation events

from Utils.Optimization import CaseInfo
from Utils.Enum import Color as C, CommonDirs
from Utils.Params import HyperParameters, SimParam
from Utils.Case_Handling import find_simulation_parameters, swap_params, swap_duration_and_freq, update_case_file
from Utils.Simulation import run_simulation
from Utils.Post_Processing import sim_real_difference, plot_measurement_by_loc, extract_points

OS = "win64" if os.name == "nt" else "linux64"
TERMINATED = False # Used for error-catching
COLUMNS = None
SESSION_ID = datetime.now().strftime("%d_%m_%Y_%Hh_%Mm_%Ss")
REAL_DURATION = 15.0 # In Seconds
DELAY = 600 # In Time Steps (~120 steps per second)
if (DELAY / 120.0) > REAL_DURATION:
    raise ValueError("Delay too large relative to the simulation duration")
RUN_TIMES = []
BATCH_NO = 0 # Real data batch index to compare simulated data to
case = CaseInfo()

params, _, file_name = find_simulation_parameters(case.tree, hyp_name=None, return_name=True, record=0, verbose=False)
SESSION_NAME = file_name.split(".")[0].split("-")[1]

class TerminationObserver:
    """Broadcasts when a Termination event is registered"""
    def update(self, instance=None):
        global TERMINATED
        print(f"{C.BOLD}{C.GREEN}Info{C.END} Termination Event Registered, Stopping Maximisation")
        TERMINATED = True

class StepObserver:
    """Logs hyper-parameter settings to file for specific Optimization step"""
    def update(self, instance=None):
        global COLUMNS, SESSION_NAME, SESSION_ID
        
        latest = instance.res[len(instance.res)-1]
        params, target = latest["params"], latest["target"]
        print(f"{C.BOLD}{C.GREEN}Info{C.END} Optimisation Step ({C.BOLD}Target{C.END}: {target})")
        with open(CommonDirs.LOGS / f"{SESSION_ID}_{SESSION_NAME}_OPTIMIZATION_LOG.csv", "a+") as f:
            if COLUMNS is None:
                COLUMNS = [col for col in params.keys()]
                f.write("Target," + ",".join(COLUMNS)) # Header
            f.write(f"\n{target}," + ",".join([f"{params[col]}" for col in COLUMNS]))

def objective(**kwargs):
    global BATCH_NO, DELAY, REAL_DURATION, OS, RUN_TIMES, SESSION_NAME, SESSION_ID
    # >> Convert Kwargs to Simulation Parameters <<
    params = HyperParameters()
    for SimParamStr, value in kwargs.items(): # Kwargs are ORDERED, see PEP 468
        param = SimParam.from_slug(SimParamStr)
        if param.type in [float, np.float16, np.float32, np.float64, np.double, np.longdouble]: # Continuous
            params[param] = str(value) # String ensures it is serialisable
        else:
            params[param] = str(param.type(value)) # Cast to discrete parameter
    swap_params(case.tree.getroot(), params)
    swap_duration_and_freq(case.tree, duration=REAL_DURATION, freq=1.0/120.0) # Should be fixed
    update_case_file(case.tree, case.case_def, case.case_name)
    
    timestamp = datetime.now().strftime("%d_%m_%Y_%Hh_%Mm_%Ss")
    # >> Run the simulation (warning: SLOW) <<
    duration = run_simulation(case.case_def, case.case_name, identifier=f"{SESSION_NAME}-{SESSION_ID}", 
                             export_vtk=False, batch=BATCH_NO,
                             os=OS, timestamp=timestamp, copy_measurements=True, verbose=False)
    RUN_TIMES.append(duration)

    measure_dir = CommonDirs.MEASURES / f"{SESSION_NAME}-{SESSION_ID}" / f"{case.case_name}-{timestamp}-Batch{BATCH_NO}"
    file_path = measure_dir / (case.case_path.name + "_Vel.csv")

    points, columns = extract_points(file_path, verbose=False)
    
    target = sim_real_difference(file_path, points, method="mse", delay=DELAY, batch=BATCH_NO)
    df = sim_real_difference(file_path, points, method=None, delay=DELAY, batch=BATCH_NO)
    plot_measurement_by_loc(df, points, save_path=file_path.parent / f"Figure.jpg", show=False) # Save Figure
    BATCH_NO = BATCH_NO + 1
    return target
    
# Use panning and zooming on initial bounds to encourage faster convergence
# bounds_transformer = SequentialDomainReductionTransformer()
optimizer = BayesianOptimization(    
    f=objective, # Want to control optimisation more finely
    pbounds=params.get_bounds(),
    verbose=2, # verbose = 1 prints only when a maximum is observed, verbose = 0 is silent
    random_state=1,
    # bounds_transformer=bounds_transformer,
)

# >> Logging / Pausing <<
log_path = CommonDirs.LOGS / f"{SESSION_ID}_{SESSION_NAME}_OPTIMIZATION_LOG.json"
if not log_path.parent.exists():
    log_path.parent.mkdir()
logger = JSONLogger(path=str(log_path))
optimizer.subscribe(Events.OPTIMIZATION_STEP, logger) 
optimizer.subscribe(event=Events.OPTIMIZATION_STEP, subscriber=StepObserver, callback=None)
optimizer.subscribe(event=Events.OPTIMIZATION_END, subscriber=TerminationObserver, callback=None)


while (resp := input("Load previous session? 'Y' (yes) 'N' (no)")).strip().lower() not in ["y", "n"]:
    continue
if resp.strip().lower() == "y":
    load_logs(optimizer, logs=[CommonDirs.LOGS / select_log()])
    print(f"{C.CYAN}{C.BOLD}INFO{C.END}: Optimizer is now aware of {len(optimizer.space)} points.")  


#  Init_points: How many steps of **random** exploration you want to perform.
#  n_iter: How many steps of bayesian optimization you want to perform.
init_points = max(0, 1 - len(optimizer.space)) # If previous session already explored space, don't do it again
n_iter = 1
no_error_recovery_attempts = 5

while TERMINATED is False and no_error_recovery_attempts > 0:
    # try:
    optimizer.maximize(
        init_points=init_points, 
        n_iter=n_iter,
        acq='ucb', # UCB: Upper Confidence Bound, EI: Expected Improvement, # POI: Probability of Improvement 
        kappa=2.576, # High: Prefer Exploration, Low: Prefer Exploitation
        kappa_decay=1, # Kappa is multiplied by this every iteration
        kappa_decay_delay=0, # Wait before starting with decay
        xi=0.0, # Used by EI and POI, 0.1=Exploration, 0.0=Exploitation
        # Parameters for internal Gaussian Process Regressor:
        kernel=Matern(nu=2.5), #  [Default: Mattern 2.5 kernel]. Specific to problem. Recommended not to change.
        alpha=1e-3, # [Default 1e-6] Controls how much noise GP can handle, increase for discrete parameters. 
        normalize_y=True, # [Default: True] Normalise mean 0 variance 1, recommended for unit-normalized priors
        n_restarts_optimizer=5, # [Default: 5] Used to optimize kernel hyperparameters!
    )
    # except:
    #    print(f"{C.BOLD}{C.RED}Warning{C.END}: Invalid hyper-parameter combination was suggested, trying again.")
    #    n_iter = n_iter if len(optimizer.space) <= init_points else n_iter - (len(optimizer.space) - init_points)
    #    # Ensure next suggestion is random, so we don't re-suggest the failing parameter combination
    #    init_points = 1 if len(optimizer.space) >= init_points else init_points - len(optimizer.space) 
    #    no_error_recovery_attempts -= 1

if no_error_recovery_attempts == 0:
    print(f"{C.BOLD}{C.RED}ERROR{C.END}: Was unable to recover from errors in Objective")

print(f"{C.BOLD}Run Times (HH:MM:SS){C.END}:\n", "\n".join([f"Iter {i}: {rt}" for i, rt in enumerate(RUN_TIMES)]))
print(f"{C.BOLD}{C.PURPLE}Max of Optimized Combinations{C.END}:\n{optimizer.max}")