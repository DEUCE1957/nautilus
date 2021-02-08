from xml.etree.ElementTree import ElementTree, XMLParser, TreeBuilder
from pathlib import Path
from Color import Color as C

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
case_def = [f for f in case_path.glob("*.xml") if case_path.name in f.name][0]
with open(case_def, 'r') as file:
    xml = [line.strip("\n") for line in file.readlines() if not line.startswith("<!--")]
print("\n".join(xml[0:5] + 
     [".".center(len(max(xml[0:5], key=len))) for i in range(3)] + [xml[-1], ""]))  
parser = XMLParser() # Uses standard TreeBuilder
parser.feed("\n".join(xml))
root = parser.close()
tree = ElementTree(element=root)
print([item for item in tree.iterfind("constantsdef")])

def is_number(s):
    """ Returns True is string is a number. """
    try:
        float(s)
        return True
    except ValueError:
        return False


def prompt(k,v):
    
    return True if resp == "" else False
    
def print_tree(root, parent_path=".", record=False, depth=0):
    if depth == 0:
        print(f">> {C.BOLD}{C.RED}{root.tag}{C.END} <<")
        print(depth * "    " + f"{', '.join([f'{C.BOLD}{str(k).capitalize()}{C.END}: {v}' for k,v in root.attrib.items()])}")
    skip = True
    for child in root:
        print((depth+1)*"    " + f"{C.BOLD}{C.PURPLE if len(child) else C.DARKCYAN}{child.tag}{C.END} :: ", end="")
        if record:
            resp = input("\nPress enter to process contract for this tag, any other key to skip.")
            skip = True if resp == "" else False
        for i, (k, v) in enumerate(child.attrib.items()):
            print(f"{k}: {v}; ", end="")
            with open(Path(__file__).parent / "HyperParameter_Contract.txt", "a+") as f:
                written = False
                if record and skip:
                    if i == 0: f.write(f"{parent_path}/{child.tag}::")
                    if is_number(v):
                        if child.get("comment") and i == 0: print(child.get("comment"))
                        if (resp := input("Keep this key?")) == "":
                            written = True
                            f.write(f"{k}->{v};" if child.tag != "parameter" else f"{k}->{v}({child.get('key', 'name')});")
                    if (i == len(child.attrib.keys()) - 1) and written: f.write("\n")
        print("")
        print_tree(child, parent_path=f"{parent_path}/{child.tag}", record=record and skip, depth=depth+1)

def search_tree(root, tag, res=[]):
    if root.tag == tag:
        res.append(root)
    for child in root:
        new_match = search_tree(child, tag, res=res)
        if res != new_match:
            res = new_match
            break
    return res

def swap_params(tree, SimParams):
    for SimParam in SimParams:
        print(SimParam)
        elements = search_tree(tree.getroot(), SimParam.tag)
        print("ELEMENTS", elements)
        for element in elements:
            print(f"ELEMENT: {element.tag} :: {element.attrib}")
            if element.get(SimParam.key) is not None:
                print(f"SET {SimParam.key} to {SimParam.value} (was {element.get(SimParam.key)})")
                element.set(SimParam.key, SimParam.value)
                
class SimParam(object):
    def __init__(self, tag, value, key="value"):
        self.tag = tag
        self.value = value
        self.key = key

    def __str__(self):
        return f"Tag: '{self.tag}' ({type(self.tag)}), Value: {self.value} ({type(self.value)}), Key: {self.key} ({type(self.key)})"

# print("\n TREE BEFORE SWAP")
print_tree(tree.getroot(), record=True)     
# test_param = SimParam("velocity", 2.0, key="v")
# print("Result:", search_tree(tree.getroot(), "velocity"))
# swap_params(tree, [test_param])
# print("\n\n TREE AFTER SWAP")
# print_tree(tree.getroot(), record=False)