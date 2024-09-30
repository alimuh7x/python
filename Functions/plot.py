import os
from dataclasses import dataclass
from typing import Optional, Tuple, List
import PyGnuplot as gp

@dataclass
class PlotConfig:
    data_file   : str                                  # Path to the data file
    output_file : str                                  # Path to the output image file
    cols        : List[Tuple[int, int]]                # List of (x_col, y_col) pairs
    multipliers : List[Tuple[float, float]]            # List of (x_multiplier, y_multiplier) pairs
    title       : str = "Plot"                         # Title of the plot
    xlabel      : str = "X Axis"                       # X-axis label
    ylabel      : str = "Y Axis"                       # Y-axis label
    x_range     : Optional[Tuple[int, int]] = None     # X-axis range (min, max)
    y_range     : Optional[Tuple[int, int]] = None     # Y-axis range (min, max)
    legend      : Optional[List[str]] = None           # Legend for the plot lines


# Updated histogram function using the new cols and multipliers format
def histogram(config: PlotConfig):
    """
    A function to plot a histogram using Gnuplot with the provided configuration.

    Parameters:
    config (PlotConfig): An object that contains the plot configuration.
    """
    if not os.path.exists(config.data_file):
        print(f"Error: Data file '{config.data_file}' does not exist.")
        return

    # Setup terminal and output configurations
    gp.c(f'set terminal pngcairo size 1200,800 enhanced font "Helvetica,35"')
    gp.c(f'set output "{config.output_file}"')

    # Set titles and labels
    gp.c(f'set title "{config.title}"')
    gp.c(f'set xlabel "{config.xlabel}"')
    gp.c(f'set ylabel "{config.ylabel}"')

    # Set axis ranges if provided
    if config.x_range:
        gp.c(f'set xrange [{config.x_range[0]}:{config.x_range[1]}]')
    if config.y_range:
        gp.c(f'set yrange [{config.y_range[0]}:{config.y_range[1]}]')

    # Set style for the plot
    gp.c('set style fill transparent solid 0.5')
    gp.c('set style function lines')

    # If legend is provided, use it; otherwise, generate default legends
    if config.legend:
        legends = config.legend
    else:
        legends = [f"Data {i + 1}" for i in range(len(config.cols))]  # Auto-generate legends if not provided

    # Plot the data based on the number of x_col and y_col pairs in cols and their corresponding multipliers
    plot_command = []
    for i, ((x_col, y_col), (x_mult, y_mult)) in enumerate(zip(config.cols, config.multipliers)):
        plot_command.append(
            f'"{config.data_file}" using ({x_mult}*${x_col}):({y_mult}*${y_col}) smooth csplines with filledcurves x1 ls {i + 1} title "{legends[i]}"'
        )

    # Join all plot commands
    full_plot_command = ', '.join(plot_command)
    gp.c(f'plot {full_plot_command}')

    print(f"Histogram saved as '{config.output_file}'.")


# Updated plot_with_gnuplot_py function using the new cols and multipliers format
def Line_plot(config: PlotConfig):
    """
    A function to plot data from a file using PyGnuplot.

    Parameters:
    config (PlotConfig): An object that contains the plot configuration.
    """
    if not os.path.exists(config.data_file):
        print(f"Error: Data file '{config.data_file}' does not exist.")
        return

    # Set up the plot commands
    gp.c(f'set terminal pngcairo size 1000,900 enhanced font "Verdana,26"')
    gp.c(f'set output "{config.output_file}"')
    gp.c(f'set title "{config.title}"')
    gp.c(f'set xlabel "{config.xlabel}"')
    gp.c(f'set ylabel "{config.ylabel}"')

    # Set X and Y ranges if provided
    if config.x_range:
        gp.c(f'set xrange [{config.x_range[0]}:{config.x_range[1]}]')
    if config.y_range:
        gp.c(f'set yrange [{config.y_range[0]}:{config.y_range[1]}]')

    # If legend is provided, use it; otherwise, generate default legends
    if config.legend:
        legends = config.legend
    else:
        legends = [f"Data {i + 1}" for i in range(len(config.cols))]  # Auto-generate legends if not provided

    # Plot the data based on the number of x_col and y_col pairs in cols and their corresponding multipliers
    plot_command = []
    for i, ((x_col, y_col), (x_mult, y_mult)) in enumerate(zip(config.cols, config.multipliers)):
        plot_command.append(
            f'"{config.data_file}" using ({x_mult}*${x_col}):({y_mult}*${y_col}) with lines title "{legends[i]}"'
        )

    # Join all plot commands
    full_plot_command = ', '.join(plot_command)
    gp.c(f'plot {full_plot_command}')

    print(f"Plot saved as '{config.output_file}'.")



