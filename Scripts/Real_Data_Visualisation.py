import matplotlib.pyplot as plt
import pandas as pd, math
from pathlib import Path

# Sampling Frequency: 120hz

data_dir = Path(__file__).parent / "Real_Data"
dfs = {}
for file in data_dir.glob("*.txt"):
    dfs[file.name] = pd.read_csv(file, sep="	")
fig, axes = plt.subplots(nrows=math.ceil(len(dfs)/3), ncols=3, figsize=(4*math.ceil(len(dfs)/3), 9))
print(math.ceil(len(dfs)/3), len(dfs))
j = 0
for i, (name, df) in enumerate(dfs.items()):
    if j > 2: j = 0
    ax = axes[i//3][j]
    ax.plot(df.iloc[:, 0], df.iloc[:, 1])
    print(name, len(df))
    title = f"{name.split('.')[0]}"
    ax.set(title=title, xlabel="Time (s)", ylabel="Velocity (m/s)")
    j += 1
plt.tight_layout()
plt.show()

