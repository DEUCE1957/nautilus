import sys, re, numpy as np, argparse
from xml.etree.ElementTree import ElementTree, XMLParser, TreeBuilder
from collections import OrderedDict
from pathlib import Path
from shutil import copyfile, copytree, rmtree
from Color import Color as C
from subprocess import Popen, PIPE, DEVNULL
from datetime import datetime

base_path = Path(__file__).parent.parent
script_path = base_path / "Scripts"
if str(script_path) not in sys.path:
    sys.path.append(str(script_path))

from XML_Tools import (HyperParameters, SimParam, print_tree, swap_params)

# >> Identify Experiment by Datetime <<
DEFAULT_TIMESTAMP = datetime.now().strftime("%d_%m_%Y_%Hh_%Mm_%Ss")
print(f"{C.BLUE}Timestamp{C.END}: {DEFAULT_TIMESTAMP}")

# >> Select Case <<
def select_case():
    cases_dir = Path(__file__).parent.parent / "Cases"
    case_names = {i: f.name for i, f in enumerate(cases_dir.glob("*")) if f.is_dir()}
    print("\n".join([f"{i}: {case_names[i]}" for i in range(len(case_names)) if i in case_names]))
    while (resp := input("Please select a Case by number")):
        if resp.isdigit():
            if int(resp) in case_names:
                case_name = case_names[int(resp)]
                break
    case_path = cases_dir / case_name
    print(f"You selected the Case path: {case_path}")
    return case_path, case_name


# >> Parse Case (Def)inition XML Tree <<<
def parse_case(case_path):
    case_def = [f for f in case_path.glob("*.xml") if case_path.name in f.name][0]
    with open(case_def, 'r') as file:
        xml = [line.strip("\n") for line in file.readlines() if not line.startswith("<!--")]
    print("\n".join(xml[0:5] + 
        [".".center(len(max(xml[0:5], key=len))) for i in range(3)] + [xml[-1], ""]))  
    parser = XMLParser() # Uses standard TreeBuilder
    parser.feed("\n".join(xml))
    root = parser.close()
    tree = ElementTree(element=root)
    return case_def, tree 

def find_simulation_parameters(tree, file_name=None,
                               swap=True, record=False, verbose=False):
    print_tree(tree.getroot(), record=record) # Record Parameters to TXT File

    params, param_vector = HyperParameters(), []
    hyperparam_dir = Path(__file__).parent / "HyperParameters"
    if file_name is None:
        file_names = {i: f.name for i, f in enumerate(hyperparam_dir.glob("*.txt"))}
        print("\n".join([f"{i}: {file_names[i]}" for i in range(len(file_names)) if i in file_names]))
        while (resp := input("Please select a Case by number")):
            if resp.isdigit():
                if int(resp) in file_names:
                    file_name = file_names[int(resp)]
                    break
    with open(hyperparam_dir / file_name, "r") as f:
        for line in f.readlines():
            param_str, value = line.strip().split("=>")
           
            param = SimParam.from_slug(param_str) 
            while params.get(param) is not None: # ToDo: Check if this works
                count += 1
                param.count = count
            params.append(param, param.type(value))
            param_vector.append(param.type(value)) # Note: List may contain multiple different types!
    if verbose:
        print("\n".join([f"Simulation Parameter ({param}):  {v}" for param, v in params.items()]))
    if swap: # Swap parameters InPlace (does not update CaseFile itself yet)
        swap_params(tree, params)
    return params, param_vector

def set_duration_and_freq(tree, duration=None, freq=1.0/120.0):
    DurationNode = SimParam(id="./execution/parameters/parameter", attr="value", count=0,
                            default=duration if duration else input("Duration in seconds"),
                            bound=np.float32, sec_key=("key", "TimeMax"))
    TimeStepNode = SimParam(id="./execution/parameters/parameter", attr="value", count=0,
                            default=str(round(freq, 15)), # 120 Hz
                            bound=np.float32, sec_key=("key", "TimeOut"))
    swap_params(tree, HyperParameters(DurationNode, TimeStepNode, use_defaults=True)) # 120 Hz

def update_case_file(tree, case_def, case_name, verbose=True):
    # >> Create backup of Case Definition file <<
    backup_path = case_def.parent / (case_name + "_Def_backup.xml")
    if not backup_path.exists():
        copyfile(case_def, backup_path)
    # >> Overwrite existing case with swapped tree <<
    tree.write(case_def, method="xml")
    if verbose:
        print_tree(tree.getroot(), record=False)
    
# >> Run Simulation (slow) <<
def run_simulation(case_def, case_name, os="win64", timestamp=DEFAULT_TIMESTAMP, copy_measurements=True, verbose=True):
    batch_path = str(case_def.parent / (case_name + f"_{os}_GPU" + (".bat" if os == "win64" else ".sh")))
    start_time = datetime.now()
    if verbose:
        print(f"Running Batch script: {batch_path}")  
    p = Popen(("" if  os=="win64" else "sudo ") + batch_path, shell=False if os=="win64" else True, 
                stdin=PIPE,
                stdout=DEVNULL, # Don't print output of Script
                cwd=str(case_def.parent))
    if Path(case_def.parent / f"{case_name}_out").exists():
        stdout, stderr = p.communicate(input=b"1") # Deletes existing '_out'
    # stdout, stderr = p.communicate(input=b"A") # Will print to stdout, input ensures program exits
    duration = datetime.now()-start_time
    if verbose:
        print(f"{C.GREEN}{C.BOLD}Simulation Complete{C.END} in {duration} (HH:MM:SS)")

    if copy_measurements:
        # >> Store MeasureTool output in this workspace <<
        copytree(case_def.parent / (case_name + "_out") / "measurements",
                Path(__file__).parent / "Measurements" / (case_name + "_" + timestamp))
    return duration
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='>> Manually Swap Simulation Hyperparameters <<')
    parser.add_argument('-d', dest="duration", type=float, nargs='?', default=None, const=True,
                        help='Duration of Simulation')
    args = parser.parse_args()

    case_path, case_name = select_case()
    case_def, tree = parse_case(case_path)
    params, param_vector = find_simulation_parameters(tree, file_name="HyperParameter_Contract-VelocityOnly.txt",
                                                      swap=True, record=True, verbose=False)
    swap_params(tree.getroot(), params)
    set_duration_and_freq(tree, duration=args.duration, freq=1.0/120.0)
    update_case_file(tree, case_def, case_name, verbose=True)
    run_simulation(case_def, case_name, os="linux64", copy_measurements=True)

