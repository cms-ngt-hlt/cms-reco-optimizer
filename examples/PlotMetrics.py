import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import sys, os, mplhep, re, textwrap
plt.style.use(mplhep.style.CMS)

'''
To run:
    python3 examples/PlotMetrics.py --dir optimize.hlt_pixel_optimization_20250127.165402
    python3 examples/PlotMetrics.py --dir optimize.hlt_pixel_optimization_20250127.165402 --interactive
    python3 examples/PlotMetrics.py --dir optimize.hlt_pixel_optimization_20250127.165402 --point 3,10,56
    python3 examples/PlotMetrics.py --dir optimize.hlt_pixel_optimization_20250127.165402 --best_efficiency
'''

if __name__ == "__main__" :

    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("--dir",              dest="dir",             default=None,      help='Name for the input directory',                 type=str           )
    parser.add_option("--points",           dest="points",          default=None,      help='Comma separated point to highlight',           type=str           )
    parser.add_option("--interactive",      dest="interactive",     default=False,     help='Whether to show the interactive plot',         action='store_true')
    parser.add_option("--best_efficiency",  dest="best_efficiency", default=False,     help='Whether to save highest efficiency points',    action='store_true')
    (options, args) = parser.parse_args()

    if not options.dir:
        sys.exit(" ### ERROR: Please provide the path to the main folder\n"
        " --> python3 examples/PlotMetrics.py --dir optimize.hlt_pixel_optimization_20250127.165402")

    main_folder = options.dir
    pareto_filename = f'{main_folder}/checkpoint/checkpoint/pareto_front.csv'

    # Defined in the main script optimize_reco.py
    metric_1 = "1MinusEfficiency"
    metric_2 = "FakeDuplicateRate"
    vector_cuts = ['phiCuts', 'cellMinz', 'cellMaxz', 'cellMaxr']

    path, name = os.path.split(pareto_filename)
    os.system(f'mkdir -p {path}/Plots')

    df = pd.read_csv(pareto_filename)
    header = df.keys().to_list()

    plot_ref = True

    # Split header into variables and metrics
    metrics = [item for item in header if metric_1 in item or metric_2 in item]
    vars = [item for item in header if item not in metrics]
    metrics_pt = [item for item in metrics if "_Pt" in item]
    metrics_eta = [item for item in metrics if "_" in item and item not in metrics_pt]

    pt_bins = [item.split('_Pt')[-1] for item in metrics_pt]
    eta_bins = [item.split('_')[-1] for item in metrics_eta]
    pt_bins = list(dict.fromkeys(pt_bins))
    eta_bins = list(dict.fromkeys(eta_bins))

    def GetMetric (metric):
        if metric_1 in metric: 
            return 'Efficiency'
        if metric_2 in metric:
            return 'Fake Rate'
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

    ###########################################################
    # Plot all metrics 
    ###########################################################

    if len(eta_bins) > 0 or len(pt_bins) > 0:

        n_rows = 2  # One row for eta_bins, one for pt_bins
        n_cols = max(len(eta_bins), len(pt_bins))

        fig, axs = plt.subplots(n_rows, n_cols, figsize=(n_cols * 5, n_rows * 5))
        axs = axs.reshape(n_rows, n_cols) if n_cols > 1 else [[ax] for ax in axs]

        scatter_objects = []
        axs_objects = []

        old_eff = [0.8348240906380441, 0.7068607068607069, 0.8415637860082305]
        old_fake = [0.14919501585706116, 0.050137516552918406, 0.14759909202025492]
        for i_eta, eta_bin in enumerate(eta_bins):

            ax = axs[0][i_eta]

            efficiencies = 1-df[f"{metric_1}_{eta_bin}"] # 1MinusEfficiency
            fake_rates = df[f"{metric_2}_{eta_bin}"] # FakeDuplicateRate

            # Scatter plot of all points
            scatter = ax.scatter(efficiencies, fake_rates, color='blue', alpha=0.5, label='Pareto Front')
            scatter_objects.append(scatter)
            axs_objects.append(ax)

            # Add default point
            ax.scatter(old_eff[i_eta], old_fake[i_eta], color='orange', marker="*", label='Default')

            # Labels and legend
            title_size = 12
            ax.set_title(f'{eta_bin}', fontsize=title_size)
            ax.set_xlabel(GetMetric(metric_1), fontsize=title_size)
            ax.set_ylabel(GetMetric(metric_2), fontsize=title_size)
            ax.tick_params(axis='x', labelsize=title_size)
            ax.tick_params(axis='y', labelsize=title_size)
            ax.set_xlim(0,1)
            ax.set_ylim(0.01,1)
            # ax.set_yscale('log')
            ax.grid(alpha=0.3)
            ax.legend(loc='upper left', fontsize=title_size)

        old_eff = [0.346081335847024, 0.7720048899755502, 0.729607250755287]
        old_fake = [0.11819015905401677, 0.11074505828687278, 0.2697841726618705]
        for i_pt, pt_bin in enumerate(pt_bins):

            ax = axs[1][i_pt]

            efficiencies = 1-df[f"{metric_1}_Pt{pt_bin}"] # 1MinusEfficiency
            fake_rates = df[f"{metric_2}_Pt{pt_bin}"] # FakeDuplicateRate

            # Scatter plot of all points
            scatter = ax.scatter(efficiencies, fake_rates, color='blue', alpha=0.5, label='Pareto Front')
            scatter_objects.append(scatter)
            axs_objects.append(ax)

            # Add default point
            if plot_ref:
                ax.scatter(old_eff[i_pt], old_fake[i_pt], color='orange', marker="*", label='Default')

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
            ax.set_ylim(0.01,1)
            # ax.set_yscale('log')
            ax.grid(alpha=0.3)
            ax.legend(loc='upper left', fontsize=title_size)
        # Hide unused subplots (if eta_bins and pt_bins are of different lengths)
        for i in range(len(pt_bins), n_cols):
            fig.delaxes(axs[1][i])

        plt.tight_layout()

        print(f" ### INFO: Saving {path}/Plots/ParetoFront_AllMetrics.png")
        plt.savefig(f"{path}/Plots/ParetoFront_AllMetrics.png")
        plt.savefig(f"{path}/Plots/ParetoFront_AllMetrics.pdf")

    else:

        fig, ax = plt.subplots(1, 1, figsize=(5, 5))

        scatter_objects = []
        axs_objects = []

        efficiencies = 1-df[f"{metric_1}"] # 1MinusEfficiency
        fake_rates = df[f"{metric_2}"] # FakeDuplicateRate

        # Scatter plot of all points
        scatter = ax.scatter(efficiencies, fake_rates, color='blue', alpha=0.5, label='Pareto Front')
        scatter_objects.append(scatter)
        axs_objects.append(ax)

        # Add default point
        old_eff = 0.7307026652821045; old_fake = 0.11862810620329303
        if plot_ref:
            ax.scatter(old_eff, old_fake, color='orange', marker="*", label='Default')

        # Add SingleMuon point
        singlemu_eff = 0.7663551401869159; singlemu_fake = 0.1926975292160447
        if plot_ref:
            ax.scatter(singlemu_eff, singlemu_fake, color='green', marker="*", label='Single Muon')

        # Labels and legend
        title_size = 12
        ax.set_xlabel(GetMetric(metric_1), fontsize=title_size)
        ax.set_ylabel(GetMetric(metric_2), fontsize=title_size)
        ax.tick_params(axis='x', labelsize=title_size)
        ax.tick_params(axis='y', labelsize=title_size)
        ax.set_xlim(0,1)
        ax.set_ylim(0.001,1)
        # ax.set_yscale('log')
        ax.grid(alpha=0.3)
        ax.legend(loc='upper left', fontsize=title_size)

        plt.tight_layout()

        print(f" ### INFO: Saving {path}/Plots/ParetoFront_AllMetrics.png")
        plt.savefig(f"{path}/Plots/ParetoFront_AllMetrics.png")
        plt.savefig(f"{path}/Plots/ParetoFront_AllMetrics.pdf")

    ###########################################################
    # Define highlights
    ###########################################################

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
            point = ax.scatter(x_point, y_point, color='red', edgecolor='black', s=70, zorder=5)
            highlighted_scatter.append(point)

            x_, y_ = scatter.get_offsets()[nearest_idx]

            text_1 = f'Point {nearest_idx}:\n ({x_:.3f}, {y_:.3f})'
            annotations.append(ax.annotate(f'{text_1}', (x_, y_), textcoords="offset points", xytext=(0, 10), 
                ha='center', va='bottom', fontsize=12, color='red', weight='bold',
                bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3'), zorder=7*(i_move)))
        # Bring the current subplot above the others
        scatter_objects[current_scatter].axes.set_zorder(3*(i_move))

        lines = []
        for key in sorted(vars):
            # Remove vector cuts
            if any(vector_cut in key for vector_cut in vector_cuts): continue
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
        
        annotations.append(current_ax.annotate(f'{text_2}', (x_val, y_val), textcoords="offset points", xytext=(0, -10), 
            ha='center', va='top', fontsize=10, color='black', 
            bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3'), zorder=7*(i_move)))

        fig.canvas.draw()
        i_move += 1

    ###########################################################
    # Highlight highest-efficiency points
    ###########################################################

    class MockEvent:
        def __init__(self, xdata=None, ydata=None, inaxes=None):
            self.xdata = xdata
            self.ydata = ydata
            self.inaxes = inaxes

    if options.best_efficiency == True:

        # find highest efficiency point in each metric
        for i_s, scatter in enumerate(scatter_objects):
            data = scatter.get_offsets().data
            x_val, y_val = data[np.argmax(data[:,0])]
            event = MockEvent(xdata=x_val, ydata=y_val, inaxes=axs_objects[i_s])
            on_hover(event)
            print(f" ### INFO: Saving {path}/Plots/ParetoFront_AllMetrics_Best{i_s}.png")
            plt.savefig(f"{path}/Plots/ParetoFront_AllMetrics_Best{i_s}.png")
            plt.savefig(f"{path}/Plots/ParetoFront_AllMetrics_Best{i_s}.pdf")

    ###########################################################
    # Highlight selected points
    ###########################################################

    if options.points:
        points = options.points
        if ',' in options.points: list_of_points = options.points.split(',')
        else:                     list_of_points = [options.points]

        # The point configuration will be shown in the top left plot
        i_s = 0
        for point in list_of_points:
            x_val, y_val = scatter_objects[i_s].get_offsets()[int(point)]
            event = MockEvent(xdata=x_val, ydata=y_val, inaxes=axs_objects[i_s])
            on_hover(event)
            print(f" ### INFO: Saving {path}/Plots/ParetoFront_AllMetrics_Point{point}.png")
            plt.savefig(f"{path}/Plots/ParetoFront_AllMetrics_Point{point}.png")
            plt.savefig(f"{path}/Plots/ParetoFront_AllMetrics_Point{point}.pdf")

            # Check if there are overlapping points and print them
            print("\n ### Cut parameters: ", vars)
            if len(eta_bins) > 0 or len(pt_bins) > 0:
                for i_eta, eta_bin in enumerate(eta_bins):
                    print(f"\n ### INFO: Searching overlapping points with {point} in {eta_bin}")
                    overlap_idx = df[(df[f"{metric_1}_{eta_bin}"] == df.iloc[nearest_idx][f"{metric_1}_{eta_bin}"]) & (df[f"{metric_2}_{eta_bin}"] == df.iloc[nearest_idx][f"{metric_2}_{eta_bin}"])].index.values
                    for idx in overlap_idx:
                        print(" >>> ", idx, "   : ", [df.iloc[idx][var] for var in vars])

                for i_pt, pt_bin in enumerate(pt_bins):
                    print(f"\n ### INFO: Searching overlapping points with {point} in {pt_bin}")
                    overlap_idx = df[(df[f"{metric_1}_Pt{pt_bin}"] == df.iloc[nearest_idx][f"{metric_1}_Pt{pt_bin}"]) & (df[f"{metric_2}_Pt{pt_bin}"] == df.iloc[nearest_idx][f"{metric_2}_Pt{pt_bin}"])].index.values
                    for idx in overlap_idx:
                        print(" >>> ", idx, "   : ", [df.iloc[idx][var] for var in vars])                

            else:
                print(f"\n ### INFO: Searching overlapping points with {point}")
                overlap_idx = df[(df[f"{metric_1}"] == df.iloc[nearest_idx][f"{metric_1}"]) & (df[f"{metric_2}"] == df.iloc[nearest_idx][f"{metric_2}"])].index.values
                for idx in overlap_idx:
                    print(" >>> ", idx, "   : ", [df.iloc[idx][var] for var in vars])

            print("\n")

    ###########################################################
    # Start interactive window
    ###########################################################

    if options.interactive == True:
        fig.canvas.mpl_connect('motion_notify_event', on_hover)
        plt.show()
