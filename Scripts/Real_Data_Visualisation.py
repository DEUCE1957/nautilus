import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

# Sampling Frequency: 120hz

data_dir = Path(__file__).parent / "Real_Data"
dfs = {}
for file in data_dir.glob("*.txt"):
    dfs[file.name] = (pd.read_csv(file, sep="	"))
fig, axes = plt.subplots(nrows=len(dfs), ncols=len(dfs[file.name].columns), figsize=(4*len(dfs), 3*len(dfs[file.name].columns)))
for i, (name, df) in enumerate(dfs.items()):
    for j, col in enumerate(df.columns):
        ax = axes[i][j]
        ax.plot(df[col])
        title = f"{name.split('.')[0]}\n{col}" if j == len(df.columns) // 2 else col
        ax.set(title=title, xlabel="Step", ylabel=col)
plt.tight_layout()
plt.show()

