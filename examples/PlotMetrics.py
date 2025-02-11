import matplotlib.pyplot as plt
import numpy as np
import sys, os, mplhep
plt.style.use(mplhep.style.CMS)

try: main_folder = sys.argv[1]
except: sys.exit(" ### ERROR: Please provide the path to the main folder\n"
    " --> python3 examples/PlotMetrics.py optimize.hlt_pixel_optimization_20250127.165402")

pareto_filename = f'{main_folder}/checkpoint/checkpoint/pareto_front.csv'

path, name = os.path.split(pareto_filename)
os.system(f'mkdir -p {path}/Plots')

pareto_file = np.genfromtxt(pareto_filename, delimiter=",", dtype=None, skip_header=1)

fake_rates = pareto_file[:,-1] # FakeDuplicateRate
efficiencies = 1-pareto_file[:,-2] # 1MinusEfficiency

cmap = plt.cm.viridis

# Scatter plot of all points
plt.figure(figsize=(10, 10))
plt.scatter(efficiencies, fake_rates, color='red', alpha=0.9, label='Pareto Front')

# Labels and legend
plt.xlabel('Efficiency')
plt.xlim(0,1)
plt.ylabel('Fake + Duplicate Rate')
plt.ylim(0,1)
plt.legend()
plt.grid(alpha=0.3)

print(f" ### INFO: Saving {path}/Plots/ParetoFront.png")
plt.savefig(f"{path}/Plots/ParetoFront.png")
plt.savefig(f"{path}/Plots/ParetoFront.pdf")
plt.close()