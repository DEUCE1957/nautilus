from pathlib import Path
import sys, csv, math, seaborn as sns, matplotlib.pyplot as plt
import pandas as pd, numpy as np

base_path = Path(__file__).parent.parent
script_path = base_path / "Scripts"
case_dir = script_path / "Measurements"

if str(script_path) not in sys.path:
    sys.path.append(str(script_path))

def choose_from_folder(dir_path, condition, choice=None):
    items =  [x for x in dir_path.glob("**/*") if condition(x)]
    print("\n".join([f"{i}: {item}" for i, item in enumerate(items)]))
    resp = input("Choose item by number (e.g. 0)") if not choice else choice
    while True:
        if resp.isdigit():
            if int(resp) >= 0 and int(resp) < len(items):
                break
        resp = input("Choose item by number (e.g. 0)")
    return items[int(resp)]

def choose_run_and_metric(case_dir, preset=(None, None), verbose=True):
    measure_dir = case_dir / choose_from_folder(case_dir, lambda x: x.is_dir(), choice=preset[0]) # 1
    file = measure_dir / choose_from_folder(measure_dir, lambda x: x.is_file(), choice=preset[1]) # 8
    if verbose: print(f"Chose file: {file}")
    return measure_dir, file


def extract_points(file, verbose=True):
    with open(file) as csvfile:
        measure_reader = csv.reader(csvfile, delimiter=";")
        point_list = [float(point) for point in measure_reader.__next__()[2:]]
        points = {i: (point_list[3*i:3*i+3]) for i in range(len(point_list) // 3)}
        columns = measure_reader.__next__()
        if verbose:
            print("Points: ", points)            
            width = len(max(columns, key = lambda k: len(k)))
            print(" ".join([col.center(width) for col in columns]))
            for i, row in enumerate(measure_reader):
                if i == 0: continue # 1st step is empty
                print(" ".join([f"{round(float(elt), 5)}".center(width) for elt in row]))
                if i > 5: break
    return points, columns

def magnitude(row):
    return math.sqrt(row.pow(2).sum())

def append_magnitude(df, points):
    for point_no in range(len(points)):
        idx = (point_no * 3) + 1
        # start_idx, end_idx = (point_no*3)+1,min(1+(point_no+1)*3, len(columns))
        df[f"Vel_{point_no} (m/s)"] = df.iloc[:, start_idx:end_idx].apply(magnitude, axis=1)
        columns.append(f"Vel_{point_no} [m/s]")

def match_real_and_simulated(file, points, columns):
    df_simul = pd.read_csv(file, sep=";", index_col=0, header=1)

    dfs_real = {}
    for point in points.values():
        loc = int(point[0])
        dfs_real[loc] = pd.read_csv(script_path / "Real_Data" / f"Data-Upstream{loc}m-Depth{1}m-Middle.txt",
                                    sep="\s", header=0)
    data = {"Time": [], "Vel_X_Sim": [], "Vel_X_Real": [], "X": [], "Y": [], "Z": []}
    for point_no in range(len(points)):
        point = points[point_no]
        loc = int(point[0])
        t, vel_sim = df_simul[columns[1]], df_simul[f"Vel_{point_no}.x [m/s]"]
        vel_real = dfs_real[loc]["Velocity_x"][0:len(vel_sim)]
        data["Time"].extend(t); data["Vel_X_Sim"].extend(vel_sim); data["Vel_X_Real"].extend(vel_real)
        data["X"].extend([point[0]]*len(t)); data["Y"].extend([point[1]]*len(t)); data["Z"].extend([point[2]]*len(t))
    df = pd.DataFrame(data)
    return df

def plot_measurement_by_loc(df, points):
    fig, axes = plt.subplots(nrows=math.ceil(len(points)/2), ncols=2, figsize=(16,45))
    for point_no in range(len(points)):
        point = points[point_no]
        ax = axes[(math.floor(point_no/2), point_no % 2) if len(points) > 2 else point_no]

        subset = df.loc[(df.X == point[0]) & (df.Y == point[1]) & (df.Z == point[2])]
        ax.plot(subset.Time, subset.Vel_X_Sim, color="blue", label="Simulated")

        loc = int(points[point_no][0]-4)
        ax.plot(subset.Time, subset.Vel_X_Real, color="red", label="Objective") # The Objective Function! 

        ax.set(title=f"Measurement at X: {points[point_no][0]}m, Y: {points[point_no][1]}m, Z: {points[point_no][2]}m",
            xlabel="Time (s)", ylabel="Velocity_X (m/s)")
        ax.legend()
    plt.show()

if __name__ == "__main__":
    measure_dir, file = choose_run_and_metric(case_dir, preset=("1", "8"))
    points, columns = extract_points(file)
    df = match_real_and_simulated(file, points, columns)
    plot_measurement_by_loc(df, points)