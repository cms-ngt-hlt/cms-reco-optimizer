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
first_iteration = np.genfromtxt(first_iteration_file, delimiter=",", dtype=None, skip_header=1)
with open(first_iteration_file, "r") as f:
    var_names = f.readline().strip().split(",")

n_it = len(first_iteration_file)
n_var = len(first_iteration[0])-2
tot_part = len(first_iteration)
n_part = 10

i_p_vars = [] # matrix of cut values, for each iteration and each particle
i_p_efficiency = [] # matrix of efficiencies, for each iteration and each particle
i_p_fake_rate = [] # matrix of fake rates, for each iteration and each particle

# Loop over iterations
for iteration_filename in glob.glob(history_folder+'/*csv'):
    iterations = np.genfromtxt(iteration_filename, delimiter=",", dtype=None, skip_header=1)
    p_vars = [] # matrix of cut values, for each particle
    p_efficiency = [] # vector of efficiencies, for each particle
    p_fake_rate = [] # vector of fake rates, for each particle
    for iteration in iterations:
        p_vars.append(iteration[:-2])
        p_efficiency.append(1-iteration[-2]) # 1MinusEfficiency
        p_fake_rate.append(iteration[-1]) # FakeDuplicateRate
    i_p_vars.append(p_vars)
    i_p_efficiency.append(p_efficiency)
    i_p_fake_rate.append(p_fake_rate)

for i in np.arange(0, tot_part, n_part):

    start_from = i

    # Plot evolution of efficiency and fake rate across iterations
    plt.figure(figsize=(10, 10))
    cmap = plt.cm.viridis

    for p_id in range(start_from,start_from+n_part):
        efficiency = [p_efficiency[p_id] for p_efficiency in i_p_efficiency]
        fake_rate = [p_fake_rate[p_id] for p_fake_rate in i_p_fake_rate]
        plt.plot(efficiency, fake_rate, color=cmap((p_id-start_from)/n_part), 
                 linestyle='--', marker='o', label=f'Part {p_id}')

    # Labels and legend
    plt.xlabel('Efficiency')
    plt.xlim(-0.1,1.1)
    plt.ylabel('Fake + Duplicate Rate')
    plt.ylim(-0.1,1.1)
    plt.legend()
    plt.grid(alpha=0.3)

    print(f" ### INFO: Saving {path}/Plots/Particles_{start_from}_{start_from+n_part}.png")
    plt.savefig(f"{path}/Plots/Particles_{start_from}_{start_from+n_part}.png")
    plt.savefig(f"{path}/Plots/Particles_{start_from}_{start_from+n_part}.pdf")
    plt.close()

    # Plot evolution of efficiency as a function of variables across iterations
    for i_var in range(n_var):

        plt.figure(figsize=(10, 10))
        cmap = plt.cm.viridis

        for p_id in range(start_from,start_from+n_part):
            efficiency = [p_efficiency[p_id] for p_efficiency in i_p_efficiency]
            var = [p_var[p_id][i_var] for p_var in i_p_vars]

            plt.plot(var, efficiency, color=cmap((p_id-start_from)/n_part), 
                    linestyle='--', marker='o', label=f'Part {p_id}')

        # Labels and legend
        plt.xlabel(f'{var_names[i_var]}')
        plt.ylabel('Efficiency')
        plt.ylim(-0.1,1.1)
        plt.legend()
        plt.grid(alpha=0.3)

        print(f" ### INFO: Saving {path}/Plots/Particles_{var_names[i_var]}_Efficiency_{start_from}_{start_from+n_part}.png")
        plt.savefig(f"{path}/Plots/Particles_{var_names[i_var]}_Efficiency_{start_from}_{start_from+n_part}.png")
        plt.savefig(f"{path}/Plots/Particles_{var_names[i_var]}_Efficiency_{start_from}_{start_from+n_part}.pdf")
        plt.close()

    # Plot evolution of fake rate as a function of variables across iterations
    for i_var in range(n_var):

        plt.figure(figsize=(10, 10))
        cmap = plt.cm.viridis

        for p_id in range(start_from,start_from+n_part):
            fake_rate = [p_fake_rate[p_id] for p_fake_rate in i_p_fake_rate]
            var = [p_var[p_id][i_var] for p_var in i_p_vars]

            plt.plot(var, fake_rate, color=cmap((p_id-start_from)/n_part), 
                    linestyle='--', marker='o', label=f'Part {p_id}')

        # Labels and legend
        plt.xlabel(f'{var_names[i_var]}')
        plt.ylabel('Fake + Duplicate Rate')
        plt.ylim(-0.1,1.1)
        plt.legend()
        plt.grid(alpha=0.3)

        print(f" ### INFO: Saving {path}/Plots/Particles_{var_names[i_var]}_FakeRate_{start_from}_{start_from+n_part}.png")
        plt.savefig(f"{path}/Plots/Particles_{var_names[i_var]}_FakeRate_{start_from}_{start_from+n_part}.png")
        plt.savefig(f"{path}/Plots/Particles_{var_names[i_var]}_FakeRate_{start_from}_{start_from+n_part}.pdf")
        plt.close()

