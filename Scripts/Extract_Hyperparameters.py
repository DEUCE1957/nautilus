import os, sys, argparse
from pathlib import Path

base_path = Path(__file__).parent.parent
script_path = base_path / "Scripts"
if str(script_path) not in sys.path:
    sys.path.append(str(script_path))

from Utils.Case_Handling import parse_case, find_simulation_parameters, swap_params, swap_duration_and_freq, walk_tree
from Utils.Interaction import select_case
from Utils.Enum import Color as C, CommonDirs

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='>> Create Simulation Hyperparameters <<')
    parser.add_argument('-d', dest="duration", type=float, nargs='?', default=None, const=True,
                        help='Duration of Simulation')
    args = parser.parse_args()

    case_path, case_name = select_case()
    case_def, tree = parse_case(case_path)
    params, param_vector = find_simulation_parameters(tree, hyp_name=None, record=1, verbose=False)
    print(f"Generated new HyperParameter Contract at '{CommonDirs.HYPERPARAMS / 'HyperParameter_Contract-Default.txt'}'")