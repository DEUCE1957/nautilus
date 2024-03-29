from .Enum import Color as C

import numpy as np, numpy
from collections import OrderedDict

class HyperParameters(object):
    """
    Wrapper for Simulation HyperParameters. Provides convenient conversions for use in Bayesian Optimizer and for 
    use in updating XML tree elements. Otherwise acts like an OrderedDictionary.
    """

    def __init__(self, *params, use_defaults=False):
        d = OrderedDict()
        for param in params:
            d[param] = param.default if use_defaults else self._select_value(param)
        self.ParamLookup = d

    def _select_value(self, param):
        while param.bounds[0] <= float(resp := input("Provide a value")) <= param.bounds[1]:
            print(f"{resp} not within bounds ({param.bounds[0]}, {[param.bounds[1]]}), please try again. ")
        return param.type(resp)

    def set_with_vector(self, paramvector):
        """
        Update Parameter values from a 1D array.
        Args:
            paramvector (list/tuple): Ordered list of parameter values
        """
        if len(paramvector) != len(self.ParamLookup): raise ValueError("Length of parameter vector does not match")
        for i, param in enumerate(self.ParamLookup.keys()):
            self.ParamLookup[param] = paramvector[i]

    def set_with_dict(self, paramdict, surpress_warnings=False):
        """
        Updates Parameter values from a dictionary.
        Args:
            paramdict (dict): Unordered maps from string representations of SimParam objects to values
        """
        for key, value in paramdict.items():
            param = SimParam.from_slug(key)
            if self.ParamLookup.get(param) is not None:
                self.ParamLookup[param] = value
            elif not surpress_warnings:
                raise KeyError(f"{param}\nNot found in Parameter Lookup.")
    
    def get(self, param):
        return self.ParamLookup.get(param)

    def append(self, param, value):
        self.ParamLookup[param] = value

    def get_bounds(self):
        """
        Converts HyperParameters Object to UNORDERED dictionary. 
        Returns:
            A String representation of each Parameter mapped to a 2-tuple with (lower, upper) bounds.
        """
        d = {}
        for param in self.ParamLookup:
            d[repr(param)] = param.bounds
        return d

    def keys(self):
        return self.ParamLookup.keys()

    def items(self):
        return self.ParamLookup.items()

    def __setitem__(self, item, value):
        self.ParamLookup[item] = value

    def __getitem__(self, item):
        return self.ParamLookup[item]
    
    def __len__(self):
        return len(self.ParamLookup)


class SimParam(object):
    """
    id (str): Tag or XML Path (XPath) of element(s) in tree
    attr (str): Name of element's attribute that is to be modified
    count (int): If multiple elements with this id exist, distinguish between them (in order)
        Default: 0
    bound (type): Lowest and highest possible value for this Parameter, specified by type.
        Default: np.int8 (i.e. sets bounds between -128 and 127, inclusive)
    default (val): Default value for this parameter. Should be from CaseDef and must be within bounds. 
    sec_key (2-tuple): Key-Value pair that acts as secondary (attribute-value) key that must be present for match in XML. 
        Default: (None, None)
    """

    def __init__(self, id, attr, default, count=0, bound=np.float32, sec_key=(None, None)):
        self.id = id
        self.attr = attr
        self.count = count
        
        self.bounds, self.type = self._set_bound(bound)
        if self.bounds[0] <= self.type(default) <= self.bounds[1]:
            self.default = self.type(default) # Convert to same type as Bounds
        else:
            raise ValueError(f"Default value ({default}) is not within bounds {self.bounds}")
        self.sec_key = sec_key

    def _set_bound(self, bound):
        type_lookup = {elt: k for k, v in np.sctypes.items() for elt in v}
        if bound is None: # Interactive
            name_lookup = {elt.__name__: elt for v in np.sctypes.values() for elt in v}
            type_str = "\n".join([f"{C.DARKCYAN}{C.BOLD}{k}{C.END}: " +
                                    ", ".join([f"{elt.__name__}" for elt in v]) for k,v in np.sctypes.items()])
            print("Available Types:\n" + type_str)
            while (resp := input("Provide a type")) not in name_lookup:
                print(f"{resp} not a valid type, please try again. ")
            bound = name_lookup[resp]

        if len(bound) == 2 if type(bound) in [tuple, list] else False: # I.e. only check length if it is a tuple/list
            bounds = (bound[0], bound[1])
            bound = type(bound[0])     
        elif type_lookup[bound] in ["int", "uint"]: # Is integer
            info = np.iinfo(bound)
            bounds = (bound(info.min), bound(info.max))
        elif type_lookup[bound] == "float": # Is float
            info = np.finfo(bound)
            bounds = (bound(info.min), bound(info.max))
        elif np.issubdtype(bound, np.bool): # Is Boolean
            bounds = (bound(0), bound(1))
        else: 
            raise ValueError(f"Currently do not support {bound} as a Bound type, consider Encoding to a supported type")
            
        return bounds, bound

    def __hash__(self): # Fully Identifies a Simulation Parameter
        return hash((self.id, self.attr, self.default, self.type, self.count, self.sec_key, self.bounds))

    def __eq__(self, other): # Bounds and Default do NOT define equality for the object
        return ((self.id, self.attr, self.count, self.sec_key) ==  
                (other.id, other.attr, other.count, other.sec_key))

    def __ne__(self, other):
        return not(self == other)

    def __str__(self):
        return (f"{C.BOLD}ID{C.END}: '{self.id}', {C.BOLD}Attribute{C.END}: {self.attr}, " + 
                f"{C.BOLD}Count{C.END}: {self.count}, {C.BOLD}Secondary Key (Optional){C.END}: {self.sec_key}" +
                f"{C.BOLD}Bounds{C.END}: {self.bounds}, {C.BOLD}Default Value{C.END}: {self.default}")

    def __repr__(self): # Not directly executable for security
        return (f"{self.id}::{self.attr}::{self.count}::{self.type.__module__}.{self.type.__name__}"+
                f"::{self.default}::{self.sec_key}::{self.bounds}") 

    def from_slug(slug): # Class Method
        parts = slug.split("::")
        id, attr, count = parts[0], parts[1], int(parts[2])
        param_type = eval(parts[3])
        default = param_type(parts[4])
        sec_key = tuple(parts[5].strip("()").split(",")) if parts[5].split(",") != "(None, None)" else (None, None)
        bounds = tuple([param_type(np.float64(elt)) for elt in parts[6].strip("()").split(",")]) # Casting ensures type is propagated correctly
        return SimParam(id, attr, default, count, bounds, sec_key)
            