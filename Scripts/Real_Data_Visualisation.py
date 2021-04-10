import matplotlib as mlt
import matplotlib.pyplot as plt
import pandas as pd, math, numpy as np
from pathlib import Path
plt.style.use("seaborn-paper")
# Sampling Frequency: 120hz

data_dir = Path(__file__).parent / "Real_Data"
dfs = {}
for file in data_dir.glob("*.txt"):
    if not "845mm" in file.name:
        dfs[file.name] = pd.read_csv(file, sep="	")

fig, axes = plt.subplots(nrows=math.ceil(len(dfs)/2), ncols=4, figsize=(4*math.ceil(len(dfs)/2), 16), 
                        sharex=False, sharey=True, gridspec_kw={"width_ratios":[3,1,3,1]})
fig.set_tight_layout({'rect': [0, 0, 1, 0.95], 'pad': 0.5, 'h_pad': 0.15})
print(math.ceil(len(dfs)/2), len(dfs))
j = 0
deviations = 0.0
for i, (name, df) in enumerate(dfs.items()):
    if j > 1: j = 0
    ax = axes[i//2][2*j]
    x, y = df.iloc[:, 0], df.iloc[:, 1]
    deviations += y.std()

    zoom_start, zoom_end = round(0.45*len(df)), round(0.55*len(df))
    ax.plot(x, y, color="blue", alpha=0.8)
    for xcoord in [x[zoom_start], x[zoom_end]]:
        ax.axvline(x=xcoord, color="black", alpha=0.5, zorder=5, linestyle="--", label="_nolegend_")
    ax.axhline(y=np.mean(y), color="red", alpha=0.5)
    print(name, len(df))
    title = f"{name.split('.')[0]}"
    ax.set(title=title, xlabel="Time (s)" if i//2 == len(dfs.items())//2 else None, ylabel="Velocity (m/s)" if j == 0 else None,
           xlim=(0,max(x)))
    ax.legend(["LDV Reading", "Mean"], loc="lower right")
    sub_ax = axes[i//2][(2*j)+1]
    x2, y2 = x.iloc[zoom_start:zoom_end], y.iloc[zoom_start:zoom_end]
    sub_ax.plot(x2, y2)
    sub_ax.set(title="Zoomed In", xlim=(min(x2),max(x2)))
    # sub_ax.set(xticks=[0.45*len(df), 0.55*len(df)])
    # sub_ax.set_xticks([]); sub_ax.set_yticks([])
    j += 1
print("Average Standard Deviation", deviations/len(dfs))
plt.tight_layout()
plt.show()

