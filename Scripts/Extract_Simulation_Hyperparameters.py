import sys, re, numpy as np, argparse
from xml.etree.ElementTree import ElementTree, XMLParser, TreeBuilder
from collections import OrderedDict
from pathlib import Path
from shutil import copyfile, copytree
from Color import Color as C
from subprocess import Popen
from datetime import datetime

base_path = Path(__file__).parent.parent
script_path = base_path / "Scripts"
if str(script_path) not in sys.path:
    sys.path.append(str(script_path))

from XML_Tools import (SimParam, print_tree, swap_params)

# >> Identify Experiment by Datetime <<
timestamp = datetime.now().strftime("%d_%m_%Y_%Hh_%Mm")
print(f"{C.BLUE}Timestamp{C.END}: {timestamp}")

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

def find_simulation_parameters(tree, file="HyperParameter_Contract-ContinuousOnly.txt",
                               swap=True, record=False, verbose=False):
    print_tree(tree.getroot(), record=record) # Record Parameters to TXT File

    params, param_vector = OrderedDict(), []
    with open(Path(__file__).parent / "Hyperparameters" / file, "r") as f:
        for line in f.readlines():
            xpath, *mappings = re.split("::|;|->|\((.+)\)", line.strip())
            mappings = [elt for elt in mappings if elt not in [None, '']]
            sec_key = ("key", mappings[-1]) if len(mappings) % 2 != 0 else None
            for i in range(len(mappings) // 2):
                count, attr, value = 0, mappings[i], mappings[i+1]
                param = SimParam(xpath, attr=attr, count=count, sec_key=sec_key)
                while params.get(param) is not None:
                    count += 1
                    param = SimParam(xpath, attr=attr, count=count, sec_key=sec_key)
                params[param] = str(value)
                param_vector.append(float(value))
    if verbose:
        print("\n".join([f"Simulation Parameter ({param}):  {v}" for param, v in params.items()]))
        print(param_vector)
    if swap: # Swap parameters InPlace (does not update CaseFile itself yet)
        swap_params(tree, params)
    return params, param_vector

def set_duration_and_freq(tree, duration=None, freq=1.0/120.0):
    DurationNode = SimParam(id="./execution/parameters/parameter", attr="value", count=0, sec_key=("key", "TimeMax"))
    TimeStepNode = SimParam(id="./execution/parameters/parameter", attr="value", count=0, sec_key=("key", "TimeOut"))# "#DtMin"))
    swap_params(tree, OrderedDict([(DurationNode, duration if duration else input("Duration in seconds")),
                                   (TimeStepNode, str(round(freq, 15)))])) # 120 Hz

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
def run_simulation(case_def, case_name, copy_measurements=True):
    batch_path = str(case_def.parent / (case_name + "_win64_GPU.bat"))
    print(f"Running Batch script: {batch_path}")
    p = Popen(batch_path, cwd=str(case_def.parent))
    stdout, stderr = p.communicate(input=b"\n") # Will print to stdout, input ensures program exits
    print(f"{C.GREEN}{C.BOLD}Simulation Complete{C.END}")

    if copy_measurements:
        # >> Store MeasureTool output in this workspace <<
        copytree(case_def.parent / (case_name + "_out") / "measurements",
                Path(__file__).parent / "Measurements" / (case_name + "_" + timestamp))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='>> Manually Swap Simulation Hyperparameters <<')
    parser.add_argument('-d', dest="duration", type=float, nargs='?', default=None, const=True,
                        help='Duration of Simulation')
    args = parser.parse_args()

    case_path, case_name = select_case()
    case_def, tree = parse_case(case_path)
    params, param_vector = find_simulation_parameters(tree, file="HyperParameter_Contract-ContinuousOnly.txt",
                                                      swap=True, record=False, verbose=False)
    swap_params(tree.getroot(), params)
    set_duration_and_freq(tree, duration=args.duration, freq=1.0/120.0)
    update_case_file(tree, case_def, case_name, verbose=True)
    run_simulation(case_def, case_name, copy_measurements=True)
