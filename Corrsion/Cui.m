#!/usr/bin/env -S octave --no-gui --quiet
set(0, "defaultfigurevisible", "off");  % hide figure window
addpath(genpath("./../src"));  % add src folder to path




C_solid = 143; % mol/L
C_sat = 5.1; % mol/L


CSe = C_solid/C_solid;
CLe = C_sat/C_solid;

myprint("CSe", CSe);
myprint("CLe", CLe);
