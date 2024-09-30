#!/home/alimuh7x/myenv/bin/python3

import os
import Functions.PlotLibrary as gp
pwd = os.getcwd()

########################################################################################
# NOTE: Hystogram                                -
########################################################################################

Path011='/mnt/e/RUB/1_Learn_PPT/OPLearn/trunk/examples/ChannelWidth_011/python'

histogram_config = gp.PlotConfig(
    data_files  ="../TextData/Channelwidth_Histogram.txt",
    output_file="histogram_output.png",
    xlabel     ="Channel width [nm]",
    ylabel     ="Frequency",
    x_range    =(40, 350),
    cols       =[(1, 2), (3, 4), (5, 6)],
    multipliers=[(20, 1), (20, 1), (20, 1)],
    legends     =["x - direction", "y - direction", "z - direction"]
)

if pwd == Path011:
    gp.Histogram(histogram_config)

########################################################################################
# NOTE: Hystogram                                -
########################################################################################

PathDiagonal='/mnt/e/RUB/1_Learn_PPT/OPLearn/trunk/examples/ChannelWidthDiagonal/python'
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

if pwd == PathDiagonal:
    gp.Histogram(histogram_config)
    gp.Histogram(histogram_config2)

###########################################################################################
