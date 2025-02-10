import matplotlib.pyplot as plt
import numpy as np
import sys, os, mplhep, glob
plt.style.use(mplhep.style.CMS)

try: main_folder = sys.argv[1]
except: sys.exit(" ### ERROR: Please provide the path to the main folder\n"
    " --> python3 examples/PlotMetrics.py optimize.hlt_pixel_optimization_20250127.165402")

history_folder = f'{main_folder}/checkpoint/history'

path = history_folder
os.system(f'mkdir -p {path}/Plots')
print(f" ### INFO: Saving plots in {path}/Plots")

first_iteration_file = glob.glob(history_folder+'/*csv')[0]
first_iteration = np.genfromtxt(first_iteration_file, delimiter=",", dtype=None)

tot_part = len(first_iteration)
n_part = 10

for i in np.arange(0, tot_part, n_part):

    start_from = i

    plt.figure(figsize=(10, 10))
    cmap = plt.cm.viridis

    for p_id in range(start_from,start_from+n_part):
        efficiencies = []
        fake_rates = []
        for iteration_filename in glob.glob(history_folder+'/*csv'):

            iteration_file = np.genfromtxt(iteration_filename, delimiter=",", dtype=None)
            efficiencies.append(1-iteration_file[p_id][-2])
            fake_rates.append(iteration_file[p_id][-1])

        plt.plot(efficiencies, fake_rates, color=cmap((p_id-start_from)/n_part), 
                 linestyle='--', 
                 marker='o',
                 label=f'Part {p_id}')

    # Labels and legend
    plt.xlabel('Efficiency')
    plt.xlim(-0.1,1.1)
    plt.ylabel('Fake Rate')
    plt.ylim(-0.1,1.1)
    plt.legend()
    plt.grid(alpha=0.3)

    print(f" ### INFO: Saving {path}/Plots/Particles_{start_from}_{start_from+n_part}.png")
    plt.savefig(f"{path}/Plots/Particles_{start_from}_{start_from+n_part}.png")
    plt.savefig(f"{path}/Plots/Particles_{start_from}_{start_from+n_part}.pdf")
    plt.close()

    ### Plot efficiency of first variable across iterations

    plt.figure(figsize=(10, 10))
    cmap = plt.cm.viridis

    for p_id in range(start_from,start_from+n_part):

        efficiencies = []
        # fake_rates = []
        var_0 = []

        for iteration_filename in glob.glob(history_folder+'/*csv'):

            iteration_file = np.genfromtxt(iteration_filename, delimiter=",", dtype=None)
            efficiencies.append(1-iteration_file[p_id][-2])
            # fake_rates.append(iteration_file[p_id][-1])
            var_0.append(iteration_file[p_id][0])

        plt.plot(var_0, efficiencies, color=cmap((p_id-start_from)/n_part), 
                 linestyle='--', 
                 marker='o',
                 label=f'Part {p_id}')

    # Labels and legend
    plt.xlabel('Var 0')
    # plt.xlim(-0.1,1.1)
    plt.ylabel('Efficiency')
    plt.ylim(-0.1,1.1)
    plt.legend()
    plt.grid(alpha=0.3)

    print(f" ### INFO: Saving {path}/Plots/Particles_Efficiency_{start_from}_{start_from+n_part}.png")
    plt.savefig(f"{path}/Plots/Particles_Efficiency_{start_from}_{start_from+n_part}.png")
    plt.savefig(f"{path}/Plots/Particles_Efficiency_{start_from}_{start_from+n_part}.pdf")
    plt.close()

    ### Plot fake rate of first variable across iterations

    plt.figure(figsize=(10, 10))
    cmap = plt.cm.viridis

    for p_id in range(start_from,start_from+n_part):

        fake_rates = []
        var_0 = []

        for iteration_filename in glob.glob(history_folder+'/*csv'):

            iteration_file = np.genfromtxt(iteration_filename, delimiter=",", dtype=None)
            fake_rates.append(iteration_file[p_id][-1])
            var_0.append(iteration_file[p_id][0])

        plt.plot(var_0, fake_rates, color=cmap((p_id-start_from)/n_part), 
                 linestyle='--', 
                 marker='o',
                 label=f'Part {p_id}')

    # Labels and legend
    plt.xlabel('Var 0')
    # plt.xlim(-0.1,1.1)
    plt.ylabel('Fake Rate')
    plt.ylim(-0.1,1.1)
    plt.legend()
    plt.grid(alpha=0.3)

    print(f" ### INFO: Saving {path}/Plots/Particles_FakeRate_{start_from}_{start_from+n_part}.png")
    plt.savefig(f"{path}/Plots/Particles_FakeRate_{start_from}_{start_from+n_part}.png")
    plt.savefig(f"{path}/Plots/Particles_FakeRate_{start_from}_{start_from+n_part}.pdf")
    plt.close()
