import matplotlib.pyplot as plt
import numpy as np
import sys, os, mplhep, re
plt.style.use(mplhep.style.CMS)

import pandas as pd

try: main_folder = sys.argv[1]
except: sys.exit(" ### ERROR: Please provide the path to the main folder\n"
    " --> python3 examples/PlotMetrics.py optimize.hlt_pixel_optimization_20250127.165402")

pareto_filename = f'{main_folder}/checkpoint/checkpoint/pareto_front.csv'

metric_1 = "1MinusEfficiency"
metric_2 = "FakeDuplicateRate"
vector_cuts = ['phiCuts']

path, name = os.path.split(pareto_filename)
os.system(f'mkdir -p {path}/Plots')

df = pd.read_csv(pareto_filename)
header = df.keys().to_list()

metrics = [item for item in header if metric_1 in item or metric_2 in item]
vars = [item for item in header if item not in metrics]
metrics_pt = [item for item in metrics if "_Pt" in item]
metrics_eta = [item for item in metrics if item not in metrics_pt]

pt_bins = [item.split('_Pt')[-1] for item in metrics_pt]
eta_bins = [item.split('_')[-1] for item in metrics_eta]
pt_bins = list(dict.fromkeys(pt_bins))
eta_bins = list(dict.fromkeys(eta_bins))

def GetMetric (metric):
    if metric_1 in metric: 
        return 'Efficiency'
    if metric_2 in metric:
        return 'Fake + Duplicate Rate'
    return metric

def ConvertMetricBinName (metric):
    name = ''
    if "Pt" in metric_bin:
        metric_bin = metric_bin.replace("Pt", "$p_T$ ")
        metric_bin = re.sub(r'(\d+)_(\d+)GeV', r'\1-\2 GeV', metric_bin)
        name += metric_bin 
    else:
        name += metric_bin 

    return name


# default metrics: efficiency and fake
if len(metrics) == 2:

    fake_rates = df[f"{metric_2}"] # FakeDuplicateRate
    efficiencies = 1-df[f"{metric_1}"] # 1MinusEfficiency
    # Scatter plot of all points
    plt.figure(figsize=(10, 10))
    plt.scatter(efficiencies, fake_rates, color='green', alpha=0.9, label='Pareto Front')

    # Labels and legend
    plt.xlabel(GetMetric(metric_1))
    plt.xlim(0,1)
    plt.ylabel(GetMetric(metric_2))
    plt.ylim(0,1)
    plt.legend()
    plt.grid(alpha=0.3)

    print(f" ### INFO: Saving {path}/Plots/ParetoFront.png")
    plt.savefig(f"{path}/Plots/ParetoFront.png")
    plt.savefig(f"{path}/Plots/ParetoFront.pdf")
    plt.close()

# binned metrics: assume (ordered) one efficiency and one fake for each bin 
# e.g. '1MinusEfficiency_NegEndcap', 'FakeDuplicateRate_NegEndcap', '1MinusEfficiency_Barrel', 'FakeDuplicateRate_Barrel', ...
else:

    for i_eta, eta_bin in enumerate(eta_bins):

        fake_rates = df[f"{metric_2}_{eta_bin}"] # FakeDuplicateRate
        efficiencies = 1-df[f"{metric_1}_{eta_bin}"] # 1MinusEfficiency

        # Scatter plot of all points
        plt.figure(figsize=(10, 10))
        plt.scatter(efficiencies, fake_rates, color='green', alpha=0.9, label=f'Pareto Front')

        # Labels and legend
        plt.xlabel(GetMetric(metric_1))
        plt.xlim(0,1)
        plt.ylabel(GetMetric(metric_2))
        plt.ylim(0,1)
        plt.legend()
        plt.grid(alpha=0.3)

        print(f" ### INFO: Saving {path}/Plots/ParetoFront_EtaBin{i_eta}.png")
        plt.savefig(f"{path}/Plots/ParetoFront_EtaBin{i_eta}.png")
        plt.savefig(f"{path}/Plots/ParetoFront_EtaBin{i_eta}.pdf")
        plt.close()

    for i_pt, pt_bin in enumerate(pt_bins):

        fake_rates = df[f"{metric_2}_Pt{pt_bin}"] # FakeDuplicateRate
        efficiencies = 1-df[f"{metric_1}_Pt{pt_bin}"] # 1MinusEfficiency

        # Scatter plot of all points
        plt.figure(figsize=(10, 10))
        plt.scatter(efficiencies, fake_rates, color='green', alpha=0.9, label=f'Pareto Front')

        # Labels and legend
        plt.xlabel(GetMetric(metric_1))
        plt.xlim(0,1)
        plt.ylabel(GetMetric(metric_2))
        plt.ylim(0,1)
        plt.legend()
        plt.grid(alpha=0.3)

        print(f" ### INFO: Saving {path}/Plots/ParetoFront_PtBin{i_pt}.png")
        plt.savefig(f"{path}/Plots/ParetoFront_PtBin{i_pt}.png")
        plt.savefig(f"{path}/Plots/ParetoFront_PtBin{i_pt}.pdf")
        plt.close()
