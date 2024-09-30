#!/usr/bin/env python3

import Functions.plot as gp

# Create an instance of PlotConfig with x_range and y_range
plot_config = gp.PlotConfig(
    data_file="datafile.dat",  # Input data file
    output_file="output_plot.png",  # Output image file
    x_range=(0, 10),  # Set x-axis range
    y_range=(0, 100)  # Set y-axis range
)

# Call the plot function using the PlotConfig instance
gp.plot_with_gnuplot_py(plot_config)

