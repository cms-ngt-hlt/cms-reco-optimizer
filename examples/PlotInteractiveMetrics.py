import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import sys, os, mplhep, re, textwrap
plt.style.use(mplhep.style.CMS)

try: main_folder = sys.argv[1]
except: sys.exit(" ### ERROR: Please provide the path to the main folder\n"
    " --> python3 examples/PlotMetrics.py optimize.hlt_pixel_optimization_20250127.165402")

keys = ['cellZ0Cut', 'cellPtCut', 'cellMinYSizeB1', 'cellMinYSizeB2', 'cellMaxDYSize12', 'cellMaxDYSize', 'cellMaxDYPred', 
        'phiCuts0', 'phiCuts1', 'phiCuts2', 'phiCuts3', 'phiCuts4', 'phiCuts5', 'phiCuts6', 'phiCuts7', 'phiCuts8', 'phiCuts9', 'phiCuts10', 
        'phiCuts11', 'phiCuts12', 'phiCuts13', 'phiCuts14', 'phiCuts15', 'phiCuts16', 'phiCuts17', 'phiCuts18', 'phiCuts19', 'phiCuts20', 
        'phiCuts21', 'phiCuts22', 'phiCuts23', 'phiCuts24', 'phiCuts25', 'phiCuts26', 'phiCuts27', 'phiCuts28', 'phiCuts29', 'phiCuts30', 
        'phiCuts31', 'phiCuts32', 'phiCuts33', 'phiCuts34', 'phiCuts35', 'phiCuts36', 'phiCuts37', 'phiCuts38', 'phiCuts39', 'phiCuts40', 
        'phiCuts41', 'phiCuts42', 'phiCuts43', 'phiCuts44', 'phiCuts45', 'phiCuts46', 'phiCuts47', 'phiCuts48', 'phiCuts49', 'phiCuts50', 
        'phiCuts51', 'phiCuts52', 'phiCuts53', 'phiCuts54',  
        '1MinusEfficiency_NegEndcap', 'FakeDuplicateRate_NegEndcap', '1MinusEfficiency_Barrel', 'FakeDuplicateRate_Barrel', '1MinusEfficiency_PosEndcap', 'FakeDuplicateRate_PosEndcap', 
        '1MinusEfficiency_Pt0_3GeV', 'FakeDuplicateRate_Pt0_3GeV', '1MinusEfficiency_Pt3_10GeV', 'FakeDuplicateRate_Pt3_10GeV', '1MinusEfficiency_Pt10_100GeV', 'FakeDuplicateRate_Pt10_100GeV']

pareto_filename = f'{main_folder}/checkpoint/checkpoint/pareto_front.csv'

metric_1 = "1MinusEfficiency"
metric_2 = "FakeDuplicateRate"

path, name = os.path.split(pareto_filename)
os.system(f'mkdir -p {path}/Plots')

# df = pd.read_csv(pareto_filename)
df = pd.read_csv(pareto_filename, skiprows=1, header=None)
df.columns = keys
header = df.keys().to_list()

metrics = [item for item in header if metric_1 in item or metric_2 in item]
vars = [item for item in header if item not in metrics] # and 'phiCuts' not in item]
metrics_pt = [item for item in metrics if "_Pt" in item]
metrics_eta = [item for item in metrics if item not in metrics_pt]

pt_bins = {item.split(f'_Pt')[-1] for item in metrics_pt}
eta_bins = {item.split(f'_')[-1] for item in metrics_eta}

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

fig, axs = plt.subplots(2, 3, figsize=(30, 20))
scatter_objects = []

for i_eta, eta_bin in enumerate(eta_bins):

    ax = axs[0][i_eta]

    efficiencies = 1-df[f"{metric_1}_{eta_bin}"] # 1MinusEfficiency
    fake_rates = df[f"{metric_2}_{eta_bin}"] # FakeDuplicateRate

    # Scatter plot of all points
    scatter = ax.scatter(efficiencies, fake_rates, color='red') # [TODO] Change color
    scatter_objects.append(scatter)

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

for i_pt, pt_bin in enumerate(pt_bins):

    ax = axs[1][i_pt]

    efficiencies = 1-df[f"{metric_1}_Pt{pt_bin}"] # 1MinusEfficiency
    fake_rates = df[f"{metric_2}_Pt{pt_bin}"] # FakeDuplicateRate

    # Scatter plot of all points
    scatter = ax.scatter(efficiencies, fake_rates, color='red') # [TODO] Change color
    scatter_objects.append(scatter)

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

annotation = None
highlighted_scatter = []

i_move = 1

def on_hover(event):

    global annotation
    global highlighted_scatter
    global i_move

    if event.inaxes is None:  # Ignore if the cursor is outside any axes
        return
    
    x_cursor, y_cursor = event.xdata, event.ydata

    nearest_idx = None
    current_scatter = None
    min_dist = float('inf')
    current_ax = event.inaxes  # The subplot where the cursor is

    # Find the nearest point in the scatter plot that the cursor is hovering over
    for isc, scatter in enumerate(scatter_objects):
        if scatter.axes == current_ax:
            offsets = scatter.get_offsets()
            for idx, (x, y) in enumerate(offsets):
                dist = (x_cursor - x) ** 2 + (y_cursor - y) ** 2
                if dist < min_dist:
                    min_dist = dist
                    nearest_idx = idx
                    current_scatter = isc

    if nearest_idx is None or min_dist > 0.001:  # Ignore if no close point is found
        if annotation:
            annotation.remove()
            annotation = None
        if highlighted_scatter:
            for point in highlighted_scatter:
                point.remove()
            highlighted_scatter = []
        fig.canvas.draw()
        return

    x_val, y_val = scatter_objects[current_scatter].get_offsets()[nearest_idx]  # Get exact point coordinates

    # Remove previous highlights
    if annotation:
        annotation.remove()
    if highlighted_scatter:
        for point in highlighted_scatter:
            point.remove()
    
    highlighted_scatter = []  # Reset highlighted points

    # Highlight the selected point across all subplots
    for scatter in scatter_objects:
        ax = scatter.axes
        x_point, y_point = scatter.get_offsets()[nearest_idx]
        point = ax.scatter(x_point, y_point, color='blue', edgecolor='black', s=100)  # Highlight with blue
        highlighted_scatter.append(point)

    scatter_objects[current_scatter].axes.set_zorder(3*(i_move))

    # Add annotation above the selected point in the active subplot
    text_1 = f'Point {nearest_idx}: ({x_val:.3f}, {y_val:.3f})\n' # coordinates
    text_2 = textwrap.fill(", ".join([f"{key}: {df.iloc[nearest_idx][key]}" for key in vars]), width=100)
    annotation = current_ax.annotate(f'{text_1 + text_2}',
                                     (x_val, y_val),
                                     textcoords="offset points",
                                     xytext=(10, 10),
                                     ha='center',
                                     fontsize=10,
                                     color='black',
                                     bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3'),
                                     zorder=7*(i_move))

    fig.canvas.draw()
    i_move += 1

# Connect the event handler for cursor movement
fig.canvas.mpl_connect('motion_notify_event', on_hover)

# Initialize list to track highlighted points
highlighted_scatter = []

plt.show()
