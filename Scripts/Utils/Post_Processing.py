import matplotlib.pyplot as plt,pandas as pd, csv, numpy as np, math

from .Enum import CommonDirs

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
                print(" ".join([f"{rsound(float(elt), 5)}".center(width) for elt in row]))
                if i > 5: break
    return points, columns
            
def sim_real_difference(file, points, method=None, delay=0, batch=0):
    """Compares the simulated measurements to the real data using specific method
    file (Path): Path to CSV file containing velocity readings for current step
    points (Dict): Dictionary mapping integers to 3-tuples representing point coordinates
    method (str): Metric to use for comparing the two times-series [Default: None]
        None  : Return data instead
        'mad' : Mean Absolute Difference
        'mse' : Mean Square Error 
    delay (int): How many time steps to skip from simulated data when comparing [Default: 0]
    batch (int): Which batch in the real data to compare to [Default: 0]"""
    df_simul = pd.read_csv(file, sep=";", index_col=0, header=1)

    dfs_real = {} # Read the Real Data (LDV Measurements inside Flume)
    for point in points.values():
        loc = int(point[0])
        height = "Bottom" if point[2] < 0.8 else "Top" if point[2] > 1.2 else "Middle"
        dfs_real[loc] = pd.read_csv(CommonDirs.REAL / f"Data_Depth{1000}mm_Upstream{loc}m_{height}.txt",
                                    sep="\s", names=["Time","Velocity"], engine="python")

    running_sum = 0
    data = {"Time": [], "Vel_X_Sim": [], "Vel_X_Real": [], "X": [], "Y": [], "Z": []}
    for point_no, point in points.items():
        (x,y,z) = points[point_no]
        simulated_x_velocity = df_simul[f"Vel_{point_no}.x [m/s]"][delay:] # Optional delay allows for simulation to stabilise
        batch_size = len(simulated_x_velocity)
        # Compare to real data, shifted by batch_number. Delay not needed here. 
        real_x_velocity = np.roll(dfs_real[loc]["Velocity"], batch*batch_size)[0: batch_size] # Will eventually wrap around
        time = np.roll(dfs_real[loc]["Time"], batch*batch_size)[0: batch_size]
        if method == "mad": # Mean Absolute Difference
            abs_differences = np.absolute(np.subtract(simulated_x_velocity, real_x_velocity))
            running_sum += np.mean(abs_differences)
        elif method == "mse": # Mean Square Error
            square_dist = np.power(np.subtract(simulated_x_velocity, real_x_velocity), 2)
            running_sum += np.mean(square_dist)
        else: # Return as DataFrame
            data["Time"].extend(time); data["Vel_X_Sim"].extend(simulated_x_velocity); data["Vel_X_Real"].extend(real_x_velocity)
            data["X"].extend([x]*len(time)); data["Y"].extend([y]*len(time)); data["Z"].extend([z]*len(time))
    if method is None:
        return pd.DataFrame(data)
    else:
        average_distance = running_sum / len(points) # Taking mean of subsets == mean of all data
        return 1.0 / average_distance # Inverted as we want to maximise the objective

def plot_measurement_by_loc(df, points, batch=0, save_path=None, show=True):
    fig, axes = plt.subplots(nrows=math.ceil(len(points)/2), ncols=2, sharey=True,
                            figsize=(16, math.ceil(len(points)/2)*9))
    for point_no in range(len(points)):
        point = points[point_no]
        ax = axes[(math.floor(point_no/2), point_no % 2) if len(points) > 2 else point_no]

        subset = df.loc[(df.X == point[0]) & (df.Y == point[1]) & (df.Z == point[2])]
        ax.plot(subset.Time, subset.Vel_X_Sim, color="blue", label="Simulated")

        loc = int(points[point_no][0]-4)
        ax.plot(subset.Time, subset.Vel_X_Real, color="red", label="Objective") # The Objective Function! 
        ax.set(title=f"Measurement at X: {points[point_no][0]}m, Y: {points[point_no][1]}m, Z: {points[point_no][2]}m",
               xlabel="Time (s)", ylabel="Velocity_X (m/s)" if point_no % 2 == 0 else None,
               xlim=(min(subset.Time),max(subset.Time)))
        ax.legend()
    plt.tight_layout(h_pad=24.0)
    if save_path is not None:
        plt.savefig(save_path)
    if show:
        plt.show()
    plt.close()