import os
from PyGnuplot import gp
from dataclasses import dataclass
from typing import Optional, Tuple, List, Union


@dataclass
class PlotConfig:
    data_files  : Union[str, List[str]]               # Either a single file (str) or a list of files
    output_file : str                                 # Path to the output image file
    cols        : List[Tuple[int, int]]               # List of (x_col, y_col) pairs
    multipliers : List[Tuple[float, float]]           # List of (x_multiplier, y_multiplier) pairs
    legends     : Optional[List[str]] = None          # List of legend labels for each file
    xlabel      : str = "X Axis"                      # X-axis label
    ylabel      : str = "Y Axis"                      # Y-axis label
    x_range     : Optional[Tuple[int, int]] = None    # X-axis range (min, max)
    y_range     : Optional[Tuple[int, int]] = None    # Y-axis range (min, max)


def Histogram(config: PlotConfig):
    fig = gp()

    if isinstance(config.data_files, str):
        data_files = [config.data_files]
    else:
        data_files = config.data_files

    for file in data_files:
        if not os.path.exists(file):
            print(f"Error: Data file '{file}' does not exist.")
            return  # Exit the function if any file is missing

    # Set up terminal and output configurations
    fig.c(f'set terminal pngcairo size 1200,800 enhanced font "Helvetica,35"')
    fig.c('set mxtics 2')
    fig.c('set mytics 2')
    fig.c('set border lw 3')

    fig.c('set style fill transparent solid 0.5')
    fig.c('set style function lines')
    fig.c('set style line 1 lw 3 lc rgb "#0072BD"')
    fig.c('set style line 2 lw 3 lc rgb "#D95319"')
    fig.c('set style line 3 lw 3 lc rgb "#77AC30"')

    fig.c(f'set xlabel "{config.xlabel}"')
    fig.c(f'set ylabel "{config.ylabel}"')

    # Set axis ranges if provided
    if config.x_range:
        fig.c(f'set xrange [{config.x_range[0]}:{config.x_range[1]}]')
    if config.y_range:
        fig.c(f'set yrange [{config.y_range[0]}:{config.y_range[1]}]')

    # Set output file
    fig.c(f'set output "{config.output_file}"')

    fig.c(f'set key font "Cambria, 34"')

    # If legends are not provided, generate default legends
    if config.legends is None:
        legends = [f"Data {i + 1}" for i in range(len(data_files))]
    else:
        legends = config.legends

    # Create plot commands for each data file
    plot_command = []
    for i, data_file in enumerate(data_files):
        x_col, y_col = config.cols[i]
        x_mult, y_mult = config.multipliers[i]
        plot_command.append(
            f'"{data_file}" using ({x_mult}*${x_col}):({y_mult}*${y_col}) smooth csplines with filledcurves x1 ls {i + 1} title "{legends[i]}"'
        )

    # Join all plot commands
    full_plot_command = ', '.join(plot_command)
    fig.c(f'plot {full_plot_command}')

    print(f"Histogram saved as '{config.output_file}'.")


def Line_plot(config: PlotConfig):

    if isinstance(config.data_files, str):
        data_files = [config.data_files]
    else:
        data_files = config.data_files

    for file in data_files:
        if not os.path.exists(file):
            print(f"Error: Data file '{file}' does not exist.")
            return  # Exit the function if any file is missing
    fig = gp()
    # Set up the plot commands
    fig.c(f'set terminal pngcairo size 1000,900 enhanced font "Verdana,26"')
    fig.c(f'set output "{config.output_file}"')
    fig.c(f'set xlabel "{config.xlabel}"')
    fig.c(f'set ylabel "{config.ylabel}"')

    # Set X and Y ranges if provided
    if config.x_range:
        fig.c(f'set xrange [{config.x_range[0]}:{config.x_range[1]}]')
    if config.y_range:
        fig.c(f'set yrange [{config.y_range[0]}:{config.y_range[1]}]')

    # If legend is provided, use it; otherwise, generate default legends
    if config.legends:
        legends = config.legends
    else:
        legends = [f"Data {i + 1}" for i in range(len(config.cols))]  # Auto-generate legends if not provided

    # Plot the data based on the number of x_col and y_col pairs in cols and their corresponding multipliers
    plot_command = []
    for i, data_file in enumerate(data_files):
        x_col, y_col = config.cols[i]
        x_mult, y_mult = config.multipliers[i]
        plot_command.append(
            f'"{data_file}"using ({x_mult}*${x_col}):({y_mult}*${y_col}) with lines title "{legends[i]}"'
        )

    # Join all plot commands
    full_plot_command = ', '.join(plot_command)
    fig.c(f'plot {full_plot_command}')

    print(f"Plot saved as '{config.output_file}'.")
