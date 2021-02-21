from xml.etree.ElementTree import ElementTree, XMLParser, TreeBuilder
from collections import OrderedDict
from pathlib import Path
from shutil import copyfile, copytree
from Color import Color as C
from subprocess import Popen
from datetime import datetime
import re, numpy as np

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

def is_number(s):
    """ Returns True if string is a number. """
    try: 
        float(s) 
        return True
    except ValueError: 
        return False
    
def print_tree(root, parent_path=".", record=False, depth=0):
    """"Recursively print tree (left to right). 
    record (Bool): Store nodes in 'HyperParameter_Contract.txt' [Default: False]
    depth (int): Tracks level in tree, used for indentation [Default: 0]
    parent_path (str): Tracks paths to nodes, used for direct access. [Default: '.']
    """
    if depth == 0: # Is Root
        print(f">> {C.BOLD}{C.RED}{root.tag}{C.END} <<")
        print(depth * "    " + f"{', '.join([f'{C.BOLD}{str(k).capitalize()}{C.END}: {v}' for k,v in root.attrib.items()])}")

    skip = True
    for child in root: 
        # Print Child Tag in DarkCyan if LeafNode and Purple if internal node
        print("    "*(depth+1) + f"{C.BOLD}{C.PURPLE if len(child) else C.DARKCYAN}{child.tag}{C.END} :: ", end="")
        if record:
            resp = input("\nPress enter to process contract for this tag, any other key to skip.")
            skip = True if resp == "" else False # Ensures contract is only overwritten if desired. 
        for i, (k, v) in enumerate(child.attrib.items()):
            print(f"{k}: {v}; ", end="") # Attributes are concatenated to previous string 
            with open(Path(__file__).parent / "HyperParameter_Contract.txt", "a+") as f:
                written = False
                if record and skip:
                    if i == 0: f.write(f"{parent_path}/{child.tag}::")
                    if is_number(v):
                        if child.get("comment") and i == 0: print(child.get("comment"))
                        if (resp := input("Keep this key?")) == "":
                            written = True
                            f.write(f"{k}->{v};" if child.tag != "parameter" else f"{k}->{v}({child.get('key', 'name')});")
                    if (i == len(child.attrib.keys()) - 1) and written:
                        f.write("\n")
        print("") # Newline for new child node
        print_tree(child, parent_path=f"{parent_path}/{child.tag}",
                   record=record and skip, depth=depth+1)

def search_tree(root, tag, res=[]):
    """Recursively finds all elements in Tree with provided tag.
    root (node): Root of tree, must be iterable and have tag attribute.
    tag (str): String identifier of node(s) we are searching for
    res (list): Tracks matching nodes. [Default: []]"""
    if root.tag == tag:
        res.append(root)
    for child in root:
        new_match = search_tree(child, tag, res=res)
        if res != new_match:
            res = new_match
            break
    return res

def swap_params(root, params):
    """Swaps list of Simulation parameters in tree, using full XML paths.
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
            node.set(param.attr, v)
        else:
            raise KeyError(f"Attribute {param.attr} not in node with id: {param.id}")

class SimParam(object):
    """
    id (str): Tag or XML Path (XPath) of element(s) in tree
    attr (str): Name of element's attribute that is to be modified
    sec_key (2-tuple): Key-Value pair that acts as secondary (attribute-value) key
        Default: None
    count (int): If multiple elements with this id exist, distinguish between them (in order)
        Default: 0
    """
    def __init__(self, id, attr, count=0, sec_key=None):
        self.id = id
        self.attr = attr
        self.count = count
        self.sec_key = sec_key

    def __hash__(self):
        return hash((self.id, self.attr, self.count, self.sec_key))

    def __eq__(self, other):
        return (self.id, self.attr, self.count, self.sec_key) == (other.id, other.attr, other.count, other.sec_key)

    def __ne__(self, other):
        return not(self == other)

    def __str__(self):
        return (f"ID: '{self.id}', Attribute: {self.attr}, " + 
               f"Count: {self.count}, Secondary Key (Optional): {self.sec_key}")

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