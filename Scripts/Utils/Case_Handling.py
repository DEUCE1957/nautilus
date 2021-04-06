from .Enum import Color as C, CommonDirs
from .Interaction import select_hyperparameters
from .Params import HyperParameters, SimParam

import numpy as np, numpy
from xml.etree.ElementTree import ElementTree, XMLParser, TreeBuilder
from shutil import copyfile
from pathlib import Path

# >> Parse Case (Def)inition XML Tree <<<
def parse_case(case_path, verbose=False):
    """Parse Case (Def)inition XML file as an Element Tree"""
    case_defs = [f for f in case_path.glob("*.xml") if case_path.name in f.name and "backup" not in f.name]
    case_def = case_defs[0]
    if len(case_defs) > 1:
        print(f"{C.YELLOW}{C.BOLD}WARNING{C.END}::Multiple case def files found at {case_path}, defaulting to first.")

    with open(case_def, 'r') as file:
        xml = [line.strip("\n") for line in file.readlines() if not line.startswith("<!--")]
    
    if verbose: # Show XML header '...'  last element
        print(
            "\n".join(xml[0:5] + 
            [".".center(len(max(xml[0:5], key=len))) for i in range(3)] +  # Vertical Ellipsis
            [xml[-1], ""])
        )  
    parser = XMLParser() # Uses standard TreeBuilder
    parser.feed("\n".join(xml))
    root = parser.close()
    tree = ElementTree(element=root)
    return case_def, tree 

def record_node(params, child, parent_path, out_path, attr, value, record):
    """Record a leaf node to file"""
    if (resp := input("Keep this key?")) == "" or record == 2:
        xpath = f"{parent_path}/{child.tag}"
        # EdgeCase: Parameter elements are uniquely identified by Secondary Key
        sec_key = (None, None) if child.tag != "parameter" else ('key', child.get('key', 'name'))
        count = 0

        param = SimParam(xpath, attr=attr, default=value, count=count, bound=None, sec_key=sec_key)
        while params.get(param) is not None:
            count += 1 # Guarantees param is unique
            param.count = count
        params[param] = param.type(value)
        
        with open(out_path, "a") as f:
            f.write(f"{repr(param)}=>{param.type(value)}\n")
    return params

def is_number(s):
    """ Returns True if string is a number. """
    try: float(s); return True
    except ValueError: return False

def walk_tree(root, identifier="Default", record=0, params=None, parent_path=".", depth=0):
    """Recursively print tree (left to right). 
    identifier (str): Suffix for hyperparameter file. [Default: 'Default']
    record (Bool): Interactively store certain nodes in f'HyperParameter_{IDENTIFIER}.txt' [Default: 0]
        0 = Do Not Record
        1 = Interactively Record
        2 = Record all Hyperparamters
    params (HyperParameters object): Tracks selected Hyperparameters recursively [Default: None]
    parent_path (str): Tracks paths to nodes, used for direct access. [Default: '.']
    depth (int): Tracks level in tree, used for indentation [Default: 0]
    """
    out_path = CommonDirs.HYPERPARAMS / f"HyperParameter_Contract-{identifier}.txt"
    if depth == 0: # Is Root
        print(f">> {C.BOLD}{C.RED}{root.tag}{C.END} <<")
        print("    "*(depth) + ', '.join([f'{C.BOLD}{str(k).capitalize()}{C.END}: {v}' for k,v in root.attrib.items()]))
        # Initialise file
        if record > 0: 
            with open(out_path, "w"): pass
    
    if params is None:
        params = HyperParameters()
    skip = True

    for child in root: 
        # Print Child Tag in DarkCyan if LeafNode and Purple if internal node
        print("    "*(depth+1) + f"{C.BOLD}{C.PURPLE if len(child) else C.DARKCYAN}{child.tag}{C.END} :: ", end="")
        
        if record == 1:
            resp = input("\nPress enter to process contract for this tag, any other key to skip.")
            skip = True if resp == "" else False # Ensures hyperparameters file is only overwritten if desired. 
        elif record == 2:
            skip = False

        for i, (attr, value) in enumerate(child.attrib.items()):
            print(f"'{attr}': {value}; ", end="") # Attributes are concatenated to previous string 
            
            if (record >= 1) and skip and is_number(value):
                if child.get("comment") and i == 0:
                    print(child.get("comment"))
                params = record_node(params, child, parent_path, out_path, attr, value, record)
                print("")

        print("") # Newline for new child node
        walk_tree(child, parent_path=f"{parent_path}/{child.tag}",
                         record=record and skip, params=params, depth=depth+1)

def find_simulation_parameters(tree, hyp_name=None, return_name=False, record=0, verbose=False):
    """Select Simulation Hyperparameters.
    tree (ElementTree): Tree structure representing CaseDef's XML
    file_name (str): Name of hyperparameter file to use [Default: None]
    return_name (Bool): Additionally returns name of file used at end [Default: False]
    record (int): Interactively store certain nodes in f'HyperParameter_{IDENTIFIER}.txt' [Default: 0]
        0 = Do Not Record
        1 = Interactively Record
        2 = Record all Hyperparamters
    verbose (str): Whether to print the selected simulation parameters [Default: False]
    """
    params, param_vector = HyperParameters(), []
    if hyp_name is None:
        walk_tree(tree.getroot(), record=record) # Show CaseDef
        hyp_name = select_hyperparameters() if record == 0 else "HyperParameter_Contract-Default.txt"

    with open(CommonDirs.HYPERPARAMS / hyp_name.name, "r") as f:
        for line in f.readlines():
            param_str, value = line.strip().split("=>")
            param = SimParam.from_slug(param_str) 

            count = 0
            while params.get(param) is not None: # ToDo: Check if this works
                count += 1
                param.count = count
            params.append(param, param.type(value))
            param_vector.append(param.type(value)) # Note: List may contain multiple different types!

    if verbose:
        print("\n".join([f"Simulation Parameter ({param}):  {v}" for param, v in params.items()]))

    if return_name:
        return params, param_vector, hyp_name.name
    else:
        return params, param_vector

def update_case_file(tree, case_def, case_name):
    """Generates a new Case (Def)inition file from an XML Element Tree"""
    backup_path = case_def.parent / (case_name + "_Def_backup.xml")
    if not backup_path.exists():
        copyfile(case_def, backup_path)
    # >> Overwrite existing case with swapped tree <<
    tree.write(case_def, method="xml")

def swap_duration_and_freq(tree, duration=None, freq=1.0/120.0):
    """Swaps CaseDef's XML Element Tree's duration and frequency with new values"""
    DurationNode = SimParam(id="./execution/parameters/parameter", attr="value", count=0,
                            default=duration if duration else input("Duration in seconds"),
                            bound=np.float32, sec_key=("key", "TimeMax"))
    TimeStepNode = SimParam(id="./execution/parameters/parameter", attr="value", count=0,
                            default=str(round(freq, 15)), # 120 Hz
                            bound=np.float32, sec_key=("key", "TimeOut"))
    swap_params(tree, HyperParameters(DurationNode, TimeStepNode, use_defaults=True)) # 120 Hz

def swap_params(root, params):
    """Swaps list of Simulation parameters into tree (No effect on file!), using full XML paths.
    root (node): Root of tree, must be iterable.
    params(list): List of SimParam objects
    """
    for param, v in params.items():
        nodes = root.findall(param.id)
        if nodes == []: raise KeyError(f"XML id: '{param.id}' not found in Tree")
        if param.sec_key:
            for node in nodes:
                if node.get(param.sec_key[0]) == param.sec_key[1]:
                    break
        elif len(nodes) >= param.count + 1:
            node = nodes[param.count]
        else:
            raise KeyError(f"Full key: ({param}) is not unique")
        
        if node.get(param.attr) is not None:
            node.set(param.attr, str(v)) # String conversion ensures it is serialisable
        else:
            raise KeyError(f"Attribute {param.attr} not in node with id: {param.id}")