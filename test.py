#!/home/alimuh7x/myenv/bin/python3

import Functions.plot as gp

histogram_config = gp.PlotConfig(
    data_files  ="../TextData/Channelwidth_Histogram.txt",
    output_file="histogram_output.png",
    xlabel     ="Channel width [nm]",
    ylabel     ="Frequency",
    x_range    =(40, 350),
    cols       =[(5, 6), (1, 2), (3, 4)],
    multipliers=[(20, 1), (20, 1), (20, 1)],
    legends     =["x - direction", "y - direction", "z - direction"]
)

gp.Histogram(histogram_config)

histogram_config2 = gp.PlotConfig(
    data_files =[
        '../TextData/Channelwidth_Histogram.txt',
        '../../ChannelWidth_011/TextData/Channelwidth_Histogram_XY.txt',
        '../../ChannelWidth_XY/TextData/Channelwidth_Histogram_XY.txt'
    ],
    output_file="Channel_width_Output.png",
    xlabel     ="Channel width [nm]",
    ylabel     ="Frequency",
    x_range    =(40, 350),
    cols       =[(5, 6), (1, 2), (1, 2)],
    multipliers=[(20, 1), (20, 1), (20, 1)],
    legends    =['{/:Bold T}_{100}', '{/:Bold T}_{110}', '{/:Bold T}_{xy}'])

gp.Histogram(histogram_config2)
# Call the plot_with_gnuplot_py function
#gp.Line_plot(plot_config)
