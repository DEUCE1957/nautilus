from pathlib import Path
from collections import OrderedDict
from datetime import datetime
import sys, copy, json, numpy as np

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

def sim_real_difference(file, points, method="MAD"):
    df_simul = pd.read_csv(file, sep=";", index_col=0, header=1)

    running_sum = 0
    for point_no, point in enumerate(points):
        loc = int(point[0]-4) # Position downstream from Turbine (located at X=4m)
        simulated_x_velocity = df_simul[f"Vel_{point_no}.x [m/s]"]
        real_x_velocity = dfs_real[loc]["Velocity_x"][0:len(vel_sim)]
        if metric == "mad": # Mean Absolute Difference
            abs_differences = np.absolute(np.subtract(simulated_x_velocity, real_x_velocity))
            running_sum += np.mean(abs_differences)
        elif metric == "mse": # Mean Square Error
            square_dist = np.power(np.subtract(simulated_x_velocity, real_x_velocity), 2)
            running_sum += np.mean(square_dist)
    average_distance = running_sum / len(points) # Taking mean of subsets == mean of all data
    return 1.0 / average_distance # Inverted as we want to minimise the objective

def objective(**kwargs):
    # >> Convert Kwargs to Simulation Parameters <<
    params = HyperParameters()
    for SimParamStr, value in kwargs.items(): # Kwargs are ORDERED, see PEP 468
        param = SimParam.from_slug(SimParamStr)
        params[param] = str(value) # String ensures it is serialisable

    swap_params(case.tree.getroot(), params)
    set_duration_and_freq(case.tree, duration=DURATION, freq=1.0/120.0) # Should be fixed
    update_case_file(case.tree, case.case_def, case.case_name, verbose=False)

    timestamp = datetimee.now().strftime("%d_%m_%Y_%Hh_%Mm")
    # >> Run the simulation (warning: SLOW) <<
    run_simulation(case.case_def, case.case_name, timestamp=timestamp, copy_measurements=True)

    measure_dir = case.case_path / timestamp
    file_path = measure_dir / "MeasurePart_Vel.csv"

    points, columns = extract_points(file_path, verbose=False)
    target = sim_real_difference(file_path, points, method="mse")
    return target

DURATION = 0.1 # In Seconds
case = CaseInfo()

params, _ = find_simulation_parameters(case.tree, file="HyperParameter_Contract.txt",
                                                  swap=True, record=False, verbose=False)

# Use panning and zooming on initial bounds to encourage faster convergence
bounds_transformer = SequentialDomainReductionTransformer()

optimizer = BayesianOptimization(
    f=None, # Want to control optimisation more finely
    pbounds=params.get_bounds(), # {'x': (-2, 2), 'y': (-3, 3)},
    verbose=2, # verbose = 1 prints only when a maximum is observed, verbose = 0 is silent
    random_state=1,
    bounds_transformer=bounds_transformer,
)

from bayes_opt import UtilityFunction # Wrapper for Acquisition Function

# Options: UCB: Upper Confidence Bound, EI: Expected Improvement, POI: Probability of Improvement
acquisition = UtilityFunction(kind="ei", kappa=2.5, xi=0.0, kappa_decay=1, kappa_decay_delay=0)

for i in range(5): # Optimisation Loop
    # >> Use acquistion function to generate new suggestion <<
    next_params = optimizer.suggest(acquisition)
    print("Next parameters to try are:", next_params)

    # >> Evaluate Objective Function (SLOW) <<
    target = objective(**next_params)
    print("Found target to be:", target)

    # >> Update Surrogate <<
    optimizer.register(
        params=next_params,
        target=target,
    )

print(optimizer.max)