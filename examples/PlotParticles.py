import matplotlib.pyplot as plt
import numpy as np
import sys, os, mplhep, glob
plt.style.use(mplhep.style.CMS)

import pandas as pd

try: main_folder = sys.argv[1]
except: sys.exit(" ### ERROR: Please provide the path to the main folder\n"
    " --> python3 examples/PlotParticles.py optimize.hlt_pixel_optimization_20250127.165402")

history_folder = f'{main_folder}/checkpoint/history'

path = history_folder
os.system(f'mkdir -p {path}/Plots')
print(f" ### INFO: Saving plots in {path}/Plots")

metric_1 = "1MinusEfficiency"
metric_2 = "FakeDuplicateRate"
vector_cuts = ['phiCuts']

def GetMetric (metric):
    if metric_1 in metric: 
        return 'Efficiency'
    if metric_2 in metric:
        return 'Fake + Duplicate Rate'
    return metric

df_list = []
for i, iteration_filename in enumerate(glob.glob(history_folder+'/*csv')):
    df = pd.read_csv(iteration_filename)
    df['iteration'] = i
    df_list.append(df)
df = pd.concat(df_list)
header = df.keys().to_list()
header.remove('iteration')

metrics = [item for item in header if metric_1 in item or metric_2 in item]
vars = [item for item in header if item not in metrics]
metrics_pt = [item for item in metrics if "_Pt" in item]
metrics_eta = [item for item in metrics if item not in metrics_pt]

pt_bins = [item.split('_Pt')[-1] for item in metrics_pt]
eta_bins = [item.split('_')[-1] for item in metrics_eta]
pt_bins = list(dict.fromkeys(pt_bins))
eta_bins = list(dict.fromkeys(eta_bins))

n_cols = max(len(eta_bins), len(pt_bins))
n_rows = 2  # One row for eta_bins, one for pt_bins
n_iterations = len(df.iteration.unique())
n_agents = len(df.index.unique())
max_n_agents = 10

for i in np.arange(0, n_agents, max_n_agents):

    fig, axs = plt.subplots(n_rows, n_cols, figsize=(n_cols * 5, n_rows * 5))
    axs = axs.reshape(n_rows, n_cols) if n_cols > 1 else [[ax] for ax in axs]

    start_from = i
    cmap = plt.cm.viridis

    for i_eta, eta_bin in enumerate(eta_bins):
        ax = axs[0][i_eta]
        for p_id in range(start_from,start_from+max_n_agents):
            if not p_id in df.index: continue
            efficiencies = 1 - df[df.index == p_id][f"{metric_1}_{eta_bin}"] # 1MinusEfficiency
            fake_rates = df[df.index == p_id][f"{metric_2}_{eta_bin}"] # FakeDuplicateRate
            ax.scatter(efficiencies, fake_rates, color=cmap((p_id-start_from)/max_n_agents), 
                    linestyle='--', marker='o', label=f'Part {p_id}')
        # Labels and legend
        title_size = 12
        ax.set_title(f'{eta_bin}', fontsize=title_size)
        ax.set_xlabel(GetMetric(metric_1), fontsize=title_size)
        ax.set_ylabel(GetMetric(metric_2), fontsize=title_size)
        ax.tick_params(axis='x', labelsize=title_size)
        ax.tick_params(axis='y', labelsize=title_size)
        ax.set_xlim(0,1)
        ax.set_ylim(0,1)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=title_size)

    for i_pt, pt_bin in enumerate(pt_bins):
        ax = axs[1][i_pt]
        for p_id in range(start_from,start_from+max_n_agents):
            if not p_id in df.index: continue
            efficiencies = 1 - df[df.index == p_id][f"{metric_1}_Pt{pt_bin}"] # 1MinusEfficiency
            fake_rates = df[df.index == p_id][f"{metric_2}_Pt{pt_bin}"] # FakeDuplicateRate
            ax.scatter(efficiencies, fake_rates, color=cmap((p_id-start_from)/max_n_agents), 
                    linestyle='--', marker='o', label=f'Part {p_id}')
        # Labels and legend
        title_size = 12
        min_pt = pt_bin.split('GeV')[0].split('_')[0]
        max_pt = pt_bin.split('GeV')[0].split('_')[1]
        ax.set_title(f'$p_T \; {min_pt} - {max_pt} \; GeV$', fontsize=title_size)
        ax.set_xlabel(GetMetric(metric_1), fontsize=title_size)
        ax.set_ylabel(GetMetric(metric_2), fontsize=title_size)
        ax.tick_params(axis='x', labelsize=title_size)
        ax.tick_params(axis='y', labelsize=title_size)
        ax.set_xlim(0,1)
        ax.set_ylim(0,1)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=title_size)

    # Hide unused subplots (if eta_bins and pt_bins are of different lengths)
    for i in range(len(pt_bins), n_cols):
        fig.delaxes(axs[1][i])

    plt.tight_layout()

    print(f" ### INFO: Saving {path}/Plots/Particles_{start_from}_{start_from+max_n_agents}.png")
    plt.savefig(f"{path}/Plots/Particles_{start_from}_{start_from+max_n_agents}.png")
    plt.savefig(f"{path}/Plots/Particles_{start_from}_{start_from+max_n_agents}.pdf")
    plt.close()

