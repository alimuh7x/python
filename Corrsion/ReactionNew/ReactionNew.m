#!/usr/bin/env -S octave --no-gui --quiet
set(0, "defaultfigurevisible", "off");  % hide figure window
addpath(genpath("./../../src"));  % add src folder to path
% === Corrosion hydrolysis reaction rates ===
clc; clear; format long;
fprintf("===============================================================\n");
fprintf("Fe hydrolysis kinetics (Hageman & Martínez-Pañeda, 2023)\n");
fprintf("===============================================================\n");

#!/usr/bin/env octave
clear; clc; format long;

% ==========================================================
% --- Constants ---
K1    = 1.625e-4;     % equilibrium constant 1
K2    = 1.0e-8;       % equilibrium constant 2
C_tot = 5.55e4;       % total molar conc. of water [mol/m^3]

% effective mole-fraction rate constants (scaled slower for visibility)
kb1 = 2.78e7 * 1e-5;   % s^-1
kb2 = 2.78e8 * 1e-5;   % s^-1

% ==========================================================
% --- Parameter sweep ---
xM     = linspace(0, 0.2, 200)';   % Fe mole fraction (from 0 to 0.2)
xSolid = ones(size(xM));           % assume solid fraction = 1
xH     = ones(size(xM)) * 1e-7;    % H+
xOH    = K2 ./ xH;                 % OH-
xMOH   = ones(size(xM)) * 1e-9;    % FeOH+

% ==========================================================
% --- Rate equations in mole-fraction form ---
R_M   = kb1 .* (-K1 .* xM .* xSolid + xH .* xMOH);
R_MOH = kb1 .* ( K1 .* xM .* xSolid - xH .* xMOH);
R_H   = kb1 .* ( K1 .* xM .* xSolid - xH .* xMOH) + kb2 .* (K2 - xH .* xOH);
R_OH  = kb2 .* (K2 - xH .* xOH);

% --- pH calculation ---
conc_H = xH .* C_tot / 1000;  % mol/L
PH = -log10(conc_H);
% ==========================================================
% --- Plot results ---
% ==========================================================

Subplot(xM, R_M, R_MOH, 'x', 'R_M', 'R_{MOH}', 'Metal_Oxide.png');
Subplot(xM, R_H, R_OH, 'x', 'R_H', 'R_{OH}', 'Hydrogen_Oxide.png');
SinglePlot(xM, PH, 'xM', 'PH', 'PH.png');

clear; clc; format long;

% === Constants ===
C_tot = 5.55e4;   % mol/m^3 (water total concentration)

% --- Range of H+ mole fraction ---
xH = linspace(0, 5e-3, 300)';   % from 0 to 0.005

% --- Prevent log of zero ---
xH(xH <= 0) = 1e-12;

% --- Convert mole fraction to mol/L ---
conc_H = xH .* C_tot / 1000;   % mol/L

% --- pH calculation ---
pH = -log10(conc_H);

% === Plot ===
figure(1, 'position', [100 100 700 500]);
plot(xH, pH, 'b', 'LineWidth', 2);
xlabel('H^+ mole fraction, x_H');
ylabel('pH');
title('pH vs H^+ mole fraction');
grid on;
xlim([0 5e-3]);
ylim([0 14]);

print('PH.png', '-dpng', '-r300');
% --- Add guide lines ---
% hold on;
% yline(7, '--k', 'pH 7 (neutral)');
% yline(4, ':r', 'pH 4');
% yline(10, ':g', 'pH 10');
% hold off;

figure(2, 'position', [100 100 700 500]);
semilogx(xH, pH, 'b', 'LineWidth', 2);
xlabel('H^+ mole fraction, x_H (log scale)');
ylabel('pH');
title('pH vs H^+ mole fraction (log scale)');
grid on;

print('log_PH.png', '-dpng', '-r300');
disp('✅ Saved: pH_vs_xH_linear.png');

