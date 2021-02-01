import xml.etree.ElementTree as ET
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
root = ET.fromstring("\n".join(xml))

def walk_tree(root, depth=0):
    if depth == 0:
        print(f">> {C.BOLD}{C.RED}{root.tag}{C.END} <<")
        print(depth * "    " + f"{', '.join([f'{C.BOLD}{str(k).capitalize()}{C.END}: {v}' for k,v in root.attrib.items()])}")
    for child in root:
        print((depth+1)*"    " + f"{C.BOLD}{C.PURPLE if len(child) else C.DARKCYAN}{child.tag}{C.END} :: ", end="")
        for k, v in child.attrib.items():
            print(f"{k}: {v}; ", end="")
        print("")
        walk_tree(child, depth=depth+1)
walk_tree(root)