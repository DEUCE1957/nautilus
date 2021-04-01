import os, sys, argparse
from pathlib import Path

base_path = Path(__file__).parent.parent
script_path = base_path / "Scripts"
if str(script_path) not in sys.path:
    sys.path.append(str(script_path))

from Utils.Case_Handling import parse_case, find_simulation_parameters, swap_params, swap_duration_and_freq, \
                                walk_tree, update_case_file
from Utils.Simulation import run_simulation
from Utils.Interaction import select_case, select_hyperparameters
from Utils.Enum import Color as C, CommonDirs

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='>> Manually Swap Simulation Hyperparameters <<')
    parser.add_argument('-d', dest="duration", type=float, nargs='?', default=None, const=True,
                        help='Duration of Simulation')
    args = parser.parse_args()

    case_path, case_name = select_case()
    case_def, tree = parse_case(case_path)
    
    params, param_vector = find_simulation_parameters(tree,
                                                      hyp_name=select_hyperparameters(), # From previously generated
                                                      record=0, verbose=False)
    swap_params(tree.getroot(), params) # Swaps hyperparameters into Tree
    swap_duration_and_freq(tree, duration=args.duration, freq=1.0/120.0)

    print(f"{C.BOLD}{C.GREEN} Case (Def)inition content {C.END}\n".center(os.get_terminal_size().columns))
    walk_tree(tree.getroot(), record=0)

    update_case_file(tree, case_def, case_name) # Writes Tree to File
    run_simulation(case_def, case_name, os="win64" if os.name == "nt" else "linux64", copy_measurements=True)