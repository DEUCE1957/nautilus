import sys
from pathlib import Path

base_path = Path(__file__).parent.parent
script_path = base_path / "Scripts"
case_dir = script_path / "Measurements"

if str(script_path) not in sys.path:
    sys.path.append(str(script_path))

from Utils.Interaction import choose_run_and_metric
from Utils.Post_Processing import extract_points, sim_real_difference, plot_measurement_by_loc

if __name__ == "__main__":
    measure_dir, file = choose_run_and_metric()
    measures = {f: batch_no for batch_no, f in enumerate(measure_dir.glob("*.csv"))}
    points, columns = extract_points(file, verbose=False)
    df = sim_real_difference(file, points, method=None,
                             delay=int(input("Delay in time steps")),
                             batch=measures[file])
    plot_measurement_by_loc(df, points)