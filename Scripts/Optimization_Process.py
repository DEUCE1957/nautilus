from pathlib import Path
from collections import OrderedDict
from datetime import datetime
import sys, copy, json, numpy as np

base_path = Path(__file__).parent.parent
script_path = base_path / "Scripts"
submodule_path = base_path / "BayesianOptimization"
if str(script_path) not in sys.path: sys.path.append(str(script_path))
if str(submodule_path) not in sys.path: sys.path.append(str(submodule_path))

from bayes_opt import BayesianOptimization
from Measurements_Visualisation import choose_run_and_metric, extract_points, match_real_and_simulated
from Extract_Simulation_Hyperparameters import *
from XML_Tools import SimParam

case = CaseInfo()
dfs_real = {}
for point in points.values():
    loc = int(point[0]-4)
    dfs_real[loc] = pd.read_csv(script_path / "Real_Data" / f"Data-Downstream{loc}m-Depth{1}m-Middle.txt",
                                sep="\s", header=0)

class CaseInfo():
    def __init__(self):
        case_path, case_name = select_case()
        case_def, tree = parse_case(case_path)

        self.case_path = case_path
        self.case_name = case_name
        self.case_def = case_def
        self.tree = tree

def sim_real_difference(file, points):
    df_simul = pd.read_csv(file, sep=";", index_col=0, header=1)

    running_mean = 0
    for point_no, point in enumerate(points):
        loc = int(point[0]-4) # Position downstream from Turbine (located at X=4m)
        simulated_x_velocity = df_simul[f"Vel_{point_no}.x [m/s]"]
        real_x_velocity = dfs_real[loc]["Velocity_x"][0:len(vel_sim)]
        abs_differences = np.absolute(np.subtract(simulated_x_velocity, real_x_velocity))
        running_mean += np.mean(abs_differences)
    average_distance = running_mean / len(points) # Taking mean of subsets == mean of all data
    return 1.0 / average_distance # Inverted as we want to minimise the objective

def objective(**kwargs):
    # >> Convert Kwargs to Simulation Parameters <<
    params = OrderedDict()
    for SimParamStr, value in kwargs.items(): # Kwargs are ORDERED, see PEP 468
        id, attr, count, sec_key = SimParamStr.split("::")
        count = int(count)
        sec_key = (None, None) if sec_key.split(";;") == ["None","None"] else sec_key.split(";;") # Should be 2-tuple

        param = SimParam(id, attr, count, sec_key=sec_key)
        params[param] = value

    swap_params(case.tree.getroot(), params)
    set_duration_and_freq(case.tree, duration=duration, freq=1.0/120.0) # Should be fixed
    update_case_file(tree, case_def, case_name, verbose=False)

    timestamp = datetime.now().strftime("%d_%m_%Y_%Hh_%Mm")
    # >> Run the simulation (warning: SLOW) <<
    run_simulation(case_def, case_name, timestamp=timestamp, copy_measurements=True)

    measure_dir = case_dir / timestamp
    file_path = measure_dir / "MeasurePart_Vel.csv"

    points, columns = extract_points(file_path, verbose=False)
    target = sim_real_difference(file_path, points)
    return target

# Maximize: 
#   Suggest (generate param vector)
#   Probe (run the black box func)
#   Register (update surrogate with new evidence)

original_params, _ = find_simulation_parameters(case.tree, file="HyperParameter_Contract-ContinuousOnly.txt",
                                                swap=True, record=False, verbose=False)
# bounds = OrderedDict([(repr(param), param.bounds) for param in original_params])
# Use panning and zooming on initial bounds to encourage faster convergence
bounds_transformer = SequentialDomainReductionTransformer()

optimizer = BayesianOptimization(
    f=None,
    pbounds=None, # {'x': (-2, 2), 'y': (-3, 3)},
    verbose=2, # verbose = 1 prints only when a maximum is observed, verbose = 0 is silent
    random_state=1,
    bounds_transformer=bounds_transformer,
)

from bayes_opt import UtilityFunction # Wrapper for Acquisition Function

# Options: UCB: Upper Confidence Bound, EI: Expected Improvement, POI: Probability of Improvement
acquisition = UtilityFunction(kind="ei", kappa=2.5, xi=0.0, kappa_decay=1, kappa_decay_delay=0)

for i in range(5): # Optimisation Loop
    next_params = optimizer.suggest(acquistion)
    print("Next parameters to try are:", next_params)

    target = objective(**next_params)
    print("Found target to be:", target)

    optimizer.register(
        params=next_params,
        target=target,
    )

print(optimizer.max)