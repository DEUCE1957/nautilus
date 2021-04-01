from .Interaction import select_case
from .Case_Handling import parse_case
from .Enum import Color as C, CommonDirs
from pathlib import Path

class CaseInfo():
    """Stores information about a specific case"""
    def __init__(self):
        case_path, case_name = select_case()
        case_def, tree = parse_case(case_path)

        self.case_path = case_path
        self.case_name = case_name
        self.case_def = case_def
        self.tree = tree