from .Enum import CommonDirs

def choose_from_folder(dir_path, condition = lambda x: True, item="item", glob_rule="**/*", choice=None):
    items =  [x for x in dir_path.glob(glob_rule) if condition(x)]
    print("\n".join([f"{i}: {item}" for i, item in enumerate(items)]))
    resp = input(f"Choose {item} by number (e.g. 0)") if not choice else choice
    while True:
        if resp.isdigit():
            if int(resp) >= 0 and int(resp) < len(items):
                break
        resp = input(f"Choose {item} by number (e.g. 0)")
    return items[int(resp)]

def select_case():
    case_name = choose_from_folder(CommonDirs.CASES, condition=lambda f: f.is_dir(),
                                   item="case", glob_rule="*").name
    case_path = CommonDirs.CASES / case_name
    print(f"You selected the Case path: {case_path}")
    return case_path, case_name

def select_hyperparameters():
    file_name = choose_from_folder(CommonDirs.HYPERPARAMS, item="a Hyperparameter combination",
                                   glob_rule="*.txt")
    return file_name

def select_log():
    file_name = choose_from_folder(CommonDirs.LOGS, item="a previous session's log", glob_rule="*.json")
    return file_name

def choose_run_and_metric(preset=(None, None), verbose=True):
    measure_dir = CommonDirs.MEASURES / choose_from_folder(CommonDirs.MEASURES, condition=lambda x: x.is_dir(), choice=preset[0]) # 1
    file = measure_dir / choose_from_folder(measure_dir, condition=lambda x: x.is_file(), choice=preset[1]) # 8
    if verbose:
        print(f"You selected the Measurement file: {file}")
    return measure_dir, file
