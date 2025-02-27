import matplotlib.pyplot as plt
import numpy as np
import sys, os, mplhep, re
plt.style.use(mplhep.style.CMS)

try: main_folder = sys.argv[1]
except: sys.exit(" ### ERROR: Please provide the path to the main folder\n"
    " --> python3 examples/PlotMetrics.py optimize.hlt_pixel_optimization_20250127.165402")

pareto_filename = f'{main_folder}/checkpoint/checkpoint/pareto_front.csv'

path, name = os.path.split(pareto_filename)
os.system(f'mkdir -p {path}/Plots')

# read header to get metrics names
with open(pareto_filename) as f:
    header = f.readline().strip('\n').split(',')

# get the number of metrics used (default is one efficiency and one fake, but binned metrics have more)
n_metrics = sum(1 for item in header if "1MinusEfficiency" in item)

# get the pareto front
pareto_file = np.genfromtxt(pareto_filename, delimiter=",", dtype=None, skip_header=1)

def GetMetric (metric):
    if '1MinusEfficiency' in metric: 
        return 'Efficiency'
    if 'FakeDuplicateRate' in metric:
        return 'Fake + Duplicate Rate'
    return metric

def GetMetricBin (metric):

    if '1MinusEfficiency_' in metric: 
        metric = metric.replace("1MinusEfficiency_", "")
    if 'FakeDuplicateRate_' in metric:
        metric = metric.replace("FakeDuplicateRate_", "")
    
    return metric

def ConvertMetricBinName (metric_bin):
    name = ''
    if "Pt" in metric_bin:
        metric_bin = metric_bin.replace("Pt", "$p_T$ ")
        metric_bin = re.sub(r'(\d+)_(\d+)GeV', r'\1-\2 GeV', metric_bin)
        name += metric_bin 
    else:
        name += metric_bin 

    return name

# default metrics: efficiency and fake
if n_metrics == 1:

    fake_rates = pareto_file[:,-1] # FakeDuplicateRate
    efficiencies = 1-pareto_file[:,-2] # 1MinusEfficiency

    # Scatter plot of all points
    plt.figure(figsize=(10, 10))
    plt.scatter(efficiencies, fake_rates, color='red', alpha=0.9, label='Pareto Front')

    # Labels and legend
    plt.xlabel(GetMetric(header[-2]))
    plt.xlim(0,1)
    plt.ylabel(GetMetric(header[-1]))
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

    for im in range(n_metrics):

        fake_rates = pareto_file[:,(-2*im)-1] # FakeDuplicateRate
        efficiencies = 1-pareto_file[:,(-2*im)-2] # 1MinusEfficiency

        # Scatter plot of all points
        plt.figure(figsize=(10, 10))
        plt.scatter(efficiencies, fake_rates, color='red', alpha=0.9, 
            label=f'Pareto Front {ConvertMetricBinName(GetMetricBin(header[(-2*im)-2]))}')

        # Labels and legend
        plt.xlabel(GetMetric(header[(-2*im)-2]))
        plt.xlim(0,1)
        plt.ylabel(GetMetric(header[(-2*im)-1]))
        plt.ylim(0,1)
        plt.legend()
        plt.grid(alpha=0.3)

        print(f" ### INFO: Saving {path}/Plots/ParetoFront_{GetMetricBin(header[(-2*im)-2])}.png")
        plt.savefig(f"{path}/Plots/ParetoFront_{GetMetricBin(header[(-2*im)-2])}.png")
        plt.savefig(f"{path}/Plots/ParetoFront_{GetMetricBin(header[(-2*im)-2])}.pdf")
        plt.close()
