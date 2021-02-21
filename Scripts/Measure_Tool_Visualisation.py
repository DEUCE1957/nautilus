from pathlib import Path
import csv
import math
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

case_dir = Path(__file__).parent / "Measurements"

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

measure_dir = case_dir / choose_from_folder(case_dir, lambda x: x.is_dir(), choice="0")
condition = lambda x: x.is_file()
file = measure_dir / choose_from_folder(measure_dir, lambda x: x.is_file(), choice="8")
print(f"Choose file: {file}")

with open(file) as csvfile:
    measure_reader = csv.reader(csvfile, delimiter=";")
    point_list = [float(point) for point in measure_reader.__next__()[2:]]
    print(point_list)
    points = {i: (point_list[3*i:3*i+3]) for i in range(len(point_list) // 3)}
    print("Points: ", points)
    columns = measure_reader.__next__()
    print("Columns: ", columns)
    for row in measure_reader:
        print(", ".join(row))

# df = pd.read_csv(file, sep=";", index_col=0, header=1)

# def magnitude(row):
#     return math.sqrt(row.pow(2).sum())

# for point_no in range(len(points)):
#     start_idx, end_idx = (point_no*3)+1,min(1+(point_no+1)*3, len(columns))
#     df[f"Vel_{point_no} (m/s)"] = df.iloc[:, start_idx:end_idx].apply(magnitude, axis=1)
#     columns.append(f"Vel_{point_no} (m/s)")

# fig, axes = plt.subplots(nrows=math.ceil(len(points)/2), ncols=2, figsize=(16,45))
# for point_no in range(len(points)):
#     ax = axes[(math.floor(point_no/2), point_no % 2) if len(points) > 2 else point_no]
#     ax.plot(df[columns[1]],df[f"Vel_{point_no} (m/s)"])
#     ax.set(title=f"Measurement at X: {points[point_no][0]}m, Y: {points[point_no][1]}m, Z: {points[point_no][2]}m",
#         xlabel="Time (s)", ylabel="Velocity (m/s)")
# plt.show()