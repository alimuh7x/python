#!/usr/bin/env -S octave --no-gui --quiet
set(0, "defaultfigurevisible", "off");  % hide figure window
addpath(genpath("./../../src"));  % add src folder to path
% === Corrosion hydrolysis reaction rates ===
clc; clear; format long;
fprintf("===============================================================\n");

% --- Constants ---
L0  = 1e-10;       % base mobility
aa  = 0.5;         % anodic transfer coefficient
nM  = 2;           % electrons
F   = 96485;       % C/mol
Rg  = 8.314;       % J/mol/K
T   = 298;         % K
phi_m = 0.2;       % applied metal potential [V]

% --- Liquid potential range ---
phi_l = linspace(0.0, 0.3, 200);   % V
eta   = phi_m - phi_l;            % overpotential [V]

% --- Compute La ---
La = L0 .* exp((aa * nM * F .* eta) ./ (Rg * T));

exp((aa * nM * F .* phi_m) ./ (Rg * T))

Subplot(phi_l, La, eta, '\phi_l  [V]', 'L_a  [m^4 / Js]', 'Overpotential \eta [V]', 'Anodic_Mobility_vs_Liquid_Potential.png', true);
