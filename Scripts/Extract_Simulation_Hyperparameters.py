import sys, re, numpy as np
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

# >> Select Case <<
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

# >> Parse Case (Def)inition XML Tree <<<
case_def = [f for f in case_path.glob("*.xml") if case_path.name in f.name][0]
with open(case_def, 'r') as file:
    xml = [line.strip("\n") for line in file.readlines() if not line.startswith("<!--")]
print("\n".join(xml[0:5] + 
     [".".center(len(max(xml[0:5], key=len))) for i in range(3)] + [xml[-1], ""]))  
parser = XMLParser() # Uses standard TreeBuilder
parser.feed("\n".join(xml))
root = parser.close()
tree = ElementTree(element=root)

# >> Identify Experiment by Datetime <<
timestamp = datetime.now().strftime("%d_%m_%Y_%Hh_%Mm")
print(f"{C.BLUE}Timestamp{C.END}: {timestamp}")

print_tree(tree.getroot(), record=False)     

params, param_vector = OrderedDict(), []
with open(Path(__file__).parent / "HyperParameter_Contract-ContinuousOnly.txt", "r") as f:
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

print("\n".join([f"Simulation Parameter ({param}):  {v}" for param, v in params.items()]))
print(param_vector)

DurationNode = SimParam(id="./execution/parameters/parameter", attr="value", count=0, sec_key=("key", "TimeMax"))
swap_params(tree, OrderedDict([(DurationNode, input("Duration in seconds"))]))
TimeStepNode = SimParam(id="./execution/parameters/parameter", attr="value", count=0, sec_key=("key", "#DtMin"))
InitialTimeStepNode = SimParam(id="./execution/parameters/parameter", attr="value", count=0, sec_key=("key", "#DtIni"))
swap_params(tree, OrderedDict([(TimeStepNode, 1.0/120.0), (InitialTimeStepNode, 1.0/120.0)])) # 120 Hz
swap_params(tree, params)
print_tree(tree.getroot(), record=False)

# >> Create backup of Case Definition file <<
backup_path = case_def.parent / (case_name + "_Def_backup.xml")
if not backup_path.exists():
    copyfile(case_def, backup_path)
# >> Overwrite existing case with swapped tree <<
tree.write(case_def, method="xml")

# >> Run Simulation (slow) <<
batch_path = str(case_def.parent / (case_name + "_win64_GPU.bat"))
print(f"Running Batch script: {batch_path}")
p = Popen(batch_path, cwd=str(case_def.parent))
stdout, stderr = p.communicate() # Will print to stdout

print(f"{C.GREEN}{C.BOLD}Simulation Complete{C.END}")

# >> Store MeasureTool output in this workspace <<
copytree(case_def.parent / (case_name + "_out") / "measurements",
         Path(__file__).parent / "Measurements" / (case_name + "_" + timestamp))