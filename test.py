#!/home/alimuh7x/myenv/bin/python3

import Functions.plot as gp

histogram_config = gp.PlotConfig(
    data_file="TextData/Channelwidth_Histogram.txt",
    output_file="histogram_output.png",
    title="Sample Histogram",
    xlabel="X-axis",
    ylabel="Y-axis",
    x_range=(0, 100),
    y_range=(0, 50),
    cols=[(5, 6), (1, 2), (3, 4)],               # Pairs of (x_col, y_col)
    multipliers=[(20, 1), (10, 2), (15, 5)],     # Pairs of (x_multiplier, y_multiplier)
    legend=["x - direction", "y - direction", "z - direction"]
)

gp.histogram(histogram_config)

plot_config = gp.PlotConfig(
    data_file="plot_data.txt",
    output_file="plot_output.png",
    title="Sample Plot",
    xlabel="X-axis",
    ylabel="Y-axis",
    x_range=(0, 100),
    y_range=(0, 50),
    cols=[(5, 6), (1, 2), (3, 4)],               # Pairs of (x_col, y_col)
    multipliers=[(20, 1), (10, 2), (15, 5)],     # Pairs of (x_multiplier, y_multiplier)
    legend=["x - direction", "y - direction", "z - direction"]
)

# Call the plot_with_gnuplot_py function
gp.Line_plot(plot_config)
