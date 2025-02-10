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

pareto_file = np.genfromtxt(pareto_filename, delimiter=",", dtype=None)

fake_rates = pareto_file[:,-1]
efficiencies = 1-pareto_file[:,-2]

# Scatter plot of all points
plt.figure(figsize=(10, 10))
plt.scatter(efficiencies, fake_rates, color='red', alpha=0.6, label='All Points')

# Labels and legend
plt.xlabel('Efficiency')
plt.xlim(-0.1,1.1)
plt.ylabel('Fake Rate')
plt.ylim(-0.1,1.1)
plt.legend()
plt.grid(alpha=0.3)

plt.savefig(f"{path}/Plots/ParetoFront.png")
plt.savefig(f"{path}/Plots/ParetoFront.pdf")
plt.close()

# import pdb; pdb.set_trace()

for i in range(np.shape(pareto_file)[1]-2):

    iVar = pareto_file[:,i]

    sorted_indices = np.argsort(iVar)
    iVar = iVar[sorted_indices]
    efficiencies_ordered = efficiencies[sorted_indices]
    fake_rates_ordered = fake_rates[sorted_indices]

    fig, ax1 = plt.subplots()

    # Plot efficiency (y-axis left)
    color = 'tab:blue'
    ax1.set_xlabel(f'Var {i}')
    ax1.set_ylabel('Efficiency', color=color)
    ax1.set_ylim(0.,1.)
    ax1.plot(iVar, efficiencies_ordered, color=color, linestyle='--', marker='s', label='Efficiency')
    ax1.tick_params(axis='y', labelcolor=color)

    # Create a second y-axis sharing the same x-axis
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Fake Rate', color=color)
    ax2.set_ylim(0.,1.)
    ax2.plot(iVar, fake_rates_ordered, color=color, linestyle='--', marker='o', label='Fake Rate')
    ax2.tick_params(axis='y', labelcolor=color)

    # Add legends
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')

    plt.savefig(f"{path}/Plots/Var_{i}.png")
    plt.savefig(f"{path}/Plots/Var_{i}.pdf")
    plt.close()
