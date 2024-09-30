from dataclasses import dataclass
import PyGnuplot as gp
from typing import Optional, Tuple
import os


# Define the PlotConfig using dataclass
@dataclass
class PlotConfig:
    data_file: str
    output_file: str
    x_col: int = 1
    y_col: int = 2
    title: str = "Plot"
    xlabel: str = "X Axis"
    ylabel: str = "Y Axis"
    x_range: Optional[Tuple[int, int]] = None  # Allow None or a tuple
    y_range: Optional[Tuple[int, int]] = None  # Allow None or a tuple

# Define the plot function that accepts an instance of PlotConfig
def plot_with_gnuplot_py(config: PlotConfig):
    """
    A function to plot data from a file using PyGnuplot.

    Parameters:
    config (PlotConfig): An object that contains the plot configuration.
    """
    # Check if the data file exists
    if not os.path.exists(config.data_file):
        print(f"Error: Data file '{config.data_file}' does not exist.")
        return

    # Set up the plot commands
    gp.c('set terminal pngcairo size 1000,900 enhanced font "Verdana,26"')
    gp.c(f'set output "{config.output_file}"')
    gp.c(f'set title "{config.title}"')
    gp.c(f'set xlabel "{config.xlabel}"')
    gp.c(f'set ylabel "{config.ylabel}"')

    # Set X and Y ranges if provided
    if config.x_range:
        gp.c(f'set xrange [{config.x_range[0]}:{config.x_range[1]}]')
    if config.y_range:
        gp.c(f'set yrange [{config.y_range[0]}:{config.y_range[1]}]')

    # Plot the data with the specified columns
    gp.c(f'plot "{config.data_file}" using {config.x_col}:{config.y_col} with lines title "{config.title}"')

    print(f"Plot saved as '{config.output_file}'")
