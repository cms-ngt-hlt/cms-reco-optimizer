import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import sys, os, mplhep, re, textwrap
plt.style.use(mplhep.style.CMS)

try: main_folder = sys.argv[1]
except: sys.exit(" ### ERROR: Please provide the path to the main folder\n"
    " --> python3 examples/PlotInteractiveMetrics.py optimize.hlt_pixel_optimization_20250127.165402")

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

fig, axs = plt.subplots(2, 3, figsize=(18, 12))
scatter_objects = []

for i_eta, eta_bin in enumerate(eta_bins):

    ax = axs[0][i_eta]

    efficiencies = 1-df[f"{metric_1}_{eta_bin}"] # 1MinusEfficiency
    fake_rates = df[f"{metric_2}_{eta_bin}"] # FakeDuplicateRate

    # Scatter plot of all points
    scatter = ax.scatter(efficiencies, fake_rates, color='green') # [TODO] Change color
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
    scatter = ax.scatter(efficiencies, fake_rates, color='green') # [TODO] Change color
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

print(f" ### INFO: Saving {path}/Plots/ParetoFront_Interactive.png")
plt.savefig(f"{path}/Plots/ParetoFront_Interactive.png")
plt.savefig(f"{path}/Plots/ParetoFront_Interactive.pdf")

annotations = []
picked_annotations = []
highlighted_scatter = []
i_move = 1

nearest_idx = None
current_ax = None
current_scatter = None

def on_hover(event):
    """Highlight all points corresponding to the selected one, add annotation with coordinates."""
    global annotations, highlighted_scatter, i_move, nearest_idx, current_ax, current_scatter

    # Ignore if the cursor is outside any axes
    if event.inaxes is None:
        return
    
    # Get coordinates of the cursor
    x_cursor, y_cursor = event.xdata, event.ydata
    current_ax = event.inaxes

    # Find the nearest point in the scatter plot that the cursor is hovering over
    nearest_idx = None
    min_dist = float('inf')
    for isc, scatter in enumerate(scatter_objects):
        if scatter.axes == current_ax:
            offsets = scatter.get_offsets()
            for idx, (x, y) in enumerate(offsets):
                dist = (x_cursor - x) ** 2 + (y_cursor - y) ** 2
                if dist < min_dist:
                    min_dist = dist
                    nearest_idx = idx
                    current_scatter = isc

    # When there is no close point, do nothing
    if nearest_idx is None or min_dist > 0.001:
        if annotations:
            for annotation in annotations:
                annotation.remove()
            annotations = []
        if highlighted_scatter:
            for point in highlighted_scatter:
                point.remove()
            highlighted_scatter = []
        fig.canvas.draw()
        return

    # Get coordinates of the closest point
    x_val, y_val = scatter_objects[current_scatter].get_offsets()[nearest_idx]

    # Remove previous highlights
    if annotations:
        for annotation in annotations:
            annotation.remove()
        annotations = []
    if highlighted_scatter:
        for point in highlighted_scatter:
            point.remove()
        highlighted_scatter = []
    
    # Highlight the selected point across all subplots
    for scatter in scatter_objects:
        ax = scatter.axes
        x_point, y_point = scatter.get_offsets()[nearest_idx]
        point = ax.scatter(x_point, y_point, color='blue', edgecolor='black', s=70, zorder=5)
        highlighted_scatter.append(point)

    # Bring the current subplot above the others
    scatter_objects[current_scatter].axes.set_zorder(3*(i_move))

    # Display hover
    text_1 = f'Point {nearest_idx}:\n ({x_val:.3f}, {y_val:.3f})'
    annotations.append(current_ax.annotate(f'{text_1}', (x_val, y_val), textcoords="offset points", xytext=(0, 10), 
        ha='center', va='bottom', fontsize=12, color='blue', weight='bold',
        bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3'), zorder=7*(i_move)))

    lines = []
    for key in vars:
        # Remove vector cuts
        is_vector = False
        for vector_cut in vector_cuts:
            if vector_cut in key:
                is_vector = True
        if is_vector: continue
        if df.iloc[nearest_idx][key] % 1 == 0:
            # if it's an integer, round it
            lines.append(f"{key}: {int(df.iloc[nearest_idx][key])}")
        else:
            # if it's a float, only print first 3 decimals
            lines.append(f"{key}: {df.iloc[nearest_idx][key]:.3f}")

    text_2 = "\n".join(lines)

    # Check if training has been performed on phiCuts (int)
    for vector_cut in vector_cuts:
        if any(vector_cut in key for key in vars):
            text_3 = "\n".join(textwrap.wrap(f'{vector_cut} = [' + \
                ','.join([f'{int(df.iloc[nearest_idx][key])}' for key in vars if vector_cut in key]) + \
                ']', width=51))
            text_2 = text_2 + '\n' + text_3
    
    annotations.append(current_ax.annotate(f'{text_2}', (x_val, y_val), textcoords="offset points", xytext=(-10, -10), 
        ha='center', va='top', fontsize=10, color='black', 
        bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3'), zorder=7*(i_move)))

    fig.canvas.draw()
    i_move += 1

fig.canvas.mpl_connect('motion_notify_event', on_hover)

plt.show()

'''
The following intractive functions make the visualization very slow

def on_pick(event):
    """Add picked annotation with cut values when clicking on the point."""
    global i_move, nearest_idx, current_ax, current_scatter, picked_annotations

    print("Picked point at nearest_idx", nearest_idx)

    if nearest_idx is None:
        return

    # Check if the point is already annotated (toggle behavior)
    if picked_annotations:
        for ann in picked_annotations:
            ann.remove()
        picked_annotations = []
        fig.canvas.draw()
        return  

    lines = []
    for key in vars:
        # Remove vector cuts
        is_vector = False
        for vector_cut in vector_cuts:
            if vector_cut in key:
                is_vector = True
        if is_vector: continue
        if df.iloc[nearest_idx][key] % 1 == 0:
            # if it's an integer, round it
            lines.append(f"{key}: {int(df.iloc[nearest_idx][key])}")
        else:
            # if it's a float, only print first 3 decimals
            lines.append(f"{key}: {df.iloc[nearest_idx][key]:.3f}")

    text_2 = "\n".join(lines)

    # Check if training has been performed on phiCuts (int)
    for vector_cut in vector_cuts:
        if any(vector_cut in key for key in vars):
            text_3 = "\n".join(textwrap.wrap(f'{vector_cut} = [' + \
                ','.join([f'{int(df.iloc[nearest_idx][key])}' for key in vars if vector_cut in key]) + \
                ']', width=50))
            text_2 = text_2 + '\n' + text_3
    
    print("Text = ", text_2)

    x_val, y_val = scatter_objects[current_scatter].get_offsets()[nearest_idx]
    picked_annotations.append(current_ax.annotate(f'{text_2}', (x_val, y_val), textcoords="offset points", xytext=(-10, -10), 
        ha='center', va='top', fontsize=10, color='black', 
        bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3'), zorder=7*(i_move)))

    fig.canvas.draw()
    i_move += 1

fig.canvas.mpl_connect('pick_event', on_pick)

def on_click(event):
    """Clear all picked annotations when clicking outside a scatter point."""
    global picked_annotations, min_dist

    if event.inaxes is None:
        if picked_annotations:
            for ann in picked_annotations:
                ann.remove()
            picked_annotations = []
            fig.canvas.draw()
        else:
            return

fig.canvas.mpl_connect('button_press_event', on_click)
'''