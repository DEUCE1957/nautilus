from pathlib import Path

class Color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

class CommonDirs:
   MEASURES = Path(__file__).parent.parent / "Measurements"
   REAL = Path(__file__).parent.parent / "Real_Data"
   LOGS = Path(__file__).parent.parent / "Logs"
   HYPERPARAMS = Path(__file__).parent.parent / "HyperParameters"
   CASES = Path(__file__).parent.parent.parent / "Cases"