from pathlib import Path
from collections import OrderedDict
from datetime import datetime
import sys, copy, json, numpy as np, pandas as pd 

base_path = Path(__file__).parent.parent
script_path = base_path / "Scripts"
submodule_path = base_path / "BayesianOptimization"
if str(script_path) not in sys.path: sys.path.append(str(script_path))
if str(submodule_path) not in sys.path: sys.path.append(str(submodule_path))

from bayes_opt import BayesianOptimization, SequentialDomainReductionTransformer
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
    global BATCH_NO, DELAY, REAL_DURATION
    # >> Convert Kwargs to Simulation Parameters <<
    params = HyperParameters()
    for SimParamStr, value in kwargs.items(): # Kwargs are ORDERED, see PEP 468
        param = SimParam.from_slug(SimParamStr)
        params[param] = str(value) # String ensures it is serialisable

    swap_params(case.tree.getroot(), params)
    set_duration_and_freq(case.tree, duration=REAL_DURATION, freq=1.0/120.0) # Should be fixed
    update_case_file(case.tree, case.case_def, case.case_name, verbose=False)
    

    timestamp = datetime.now().strftime("%d_%m_%Y_%Hh_%Mm_%Ss")
    # >> Run the simulation (warning: SLOW) <<
    run_simulation(case.case_def, case.case_name, os="linux64", timestamp=timestamp, copy_measurements=True)

    measure_dir = Path(__file__).parent / "Measurements" / (case.case_name + "_" + timestamp)
    file_path = measure_dir / (case.case_path.name + "_Vel.csv")

    points, columns = extract_points(file_path, verbose=False)
    
    target = sim_real_difference(file_path, points, method="mse", delay=DELAY, batch=BATCH_NO)
    BATCH_NO = BATCH_NO + 1
    return target

REAL_DURATION = 15.0 # In Seconds
DELAY = 600 # In Time Steps (~120 steps per second)
if (DELAY / 120.0) > REAL_DURATION:
    raise ValueError("Delay too large relative to the simulation duration")

BATCH_NO = 0 # Real data batch index to compare simulated data to
case = CaseInfo()

params, _ = find_simulation_parameters(case.tree, file_name="HyperParameter_Contract.txt",
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

#  Init_points: How many steps of **random** exploration you want to perform.
#  n_iter: How many steps of bayesian optimization you want to perform.
optimizer.maximize(init_points=5,
                 n_iter=15,
                 acq='ucb', # UCB: Upper Confidence Bound, EI: Expected Improvement, # POI: Probability of Improvement 
                 kappa=2.576, # Higher: Favours least explored spaces
                 kappa_decay=1, # Kappa is multiplied by this every iteration
                 kappa_decay_delay=0, # Wait before starting with decay
                 xi=0.0 # Unused
                 )

print(optimizer.max)
with open("Optimisation_Results.txt", "w+") as f:
    f.write(str(optimizer.max))