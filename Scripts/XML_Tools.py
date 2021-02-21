from xml.etree.ElementTree import ElementTree, XMLParser, TreeBuilder
from Color import Color as C
from pathlib import Path

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

def is_number(s):
    """ Returns True if string is a number. """
    try: float(s); return True
    except ValueError: return False

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