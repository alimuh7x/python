#!/usr/bin/env -S octave --no-gui --quiet
set(0, "defaultfigurevisible", "off");  % hide figure window
addpath(genpath("./../../src/"));  % add src folder to path
graphics_toolkit qt
% --- Tafel curve for iron corrosion (Fe → Fe2+ + 2e−) ---
clear; clf;

% Constants
F  = 96485;     % C/mol
R  = 8.314;     % J/mol·K
T  = 298;       % K
n  = 1;         % electrons transferred


% Kinetic parameters
% in mA/cm^2 for easier plotting

i0 = 1;      % exchange current density (mA/cm^2)
alpha_a = 0.5;  % anodic transfer coefficient
alpha_c = 0.5;  % cathodic transfer coefficient
E_eq = 0.0;   % equilibrium potential (V vs SHE for Fe)

% Potential range around E_eq
E = linspace(E_eq - 0.1, E_eq + 0.1, 400);

% Current densities (A/cm^2)
i_a =  i0 * exp((alpha_a * n * F * (E - E_eq)) / (R * T));
i_c = -i0 * exp((-alpha_c * n * F * (E - E_eq)) / (R * T));

% convert to miliamps
i_a = i_a;
i_c = i_c;
% Net current
i_net = i_a + i_c;
% --- Plot log|i| vs E (Tafel plot) ---
figure;
semilogy(E, abs(i_net), 'k', 'LineWidth', 2); hold on;
semilogy(E, abs(i_a), '--r', 'LineWidth', 1.5);
semilogy(E, abs(i_c), '--b', 'LineWidth', 1.5);
xlabel('Potential E (V vs SHE)');
ylabel('log_{10}|Current density| (mA/cm^2)');
title('Theoretical Tafel Plot for Platinum Electrode');
set(gca, 'FontSize', 14);
set(gca, 'LineWidth', 1.5);
set(gca, 'TickLength', [0.01, 0.01]);
set(gca, 'Position', [0.15 0.15 0.75 0.75]);  % manual tightening if needed
legend('Total current', 'Anodic', 'Cathodic');
print("Tafel_plot.png", '-dpng');

% --- Plot |i| vs E (linear scale) ---
figure;
plot(E, abs(i_net), 'k', 'LineWidth', 2); hold on;
plot(E, abs(i_a), '--r', 'LineWidth', 1.5);
plot(E, abs(i_c), '--b', 'LineWidth', 1.5);
plot(E, zeros(size(E)), 'k--', 'LineWidth', 1);
xlabel('Potential E (V vs SHE)');
ylabel('|Current density| (mA/cm^2)');
title('Current Density vs Potential for Platinum Electrode');
set(gca, 'FontSize', 14);
set(gca, 'LineWidth', 1.5);
set(gca, 'TickLength', [0.01, 0.01]);
set(gca, 'Position', [0.15 0.15 0.75 0.75]);  % manual tightening if needed
legend('Total current', 'Anodic', 'Cathodic', 'Location', 'southeast');
print("Potential_plot.png", '-dpng');

figure;
plot(E, i_net, 'k', 'LineWidth', 2); hold on;
plot(E, i_a, '--r', 'LineWidth', 1.5);
plot(E, i_c, '--b', 'LineWidth', 1.5);
plot(E, zeros(size(E)), 'k--', 'LineWidth', 1);
xlabel('Potential E (V vs SHE)');
ylabel('Current density (mA/cm^2)');
title('Current Density vs Potential for Platinum Electrode');
set(gca, 'FontSize', 14);
set(gca, 'LineWidth', 1.5);
set(gca, 'TickLength', [0.01, 0.01]);
set(gca, 'Position', [0.15 0.15 0.75 0.75]);  % manual tightening if needed
legend('Total current', 'Anodic', 'Cathodic', 'Location', 'southeast');
print("2Potential_plot.png", '-dpng');

% three different alpha values
alpha_values = [0.3, 0.5, 0.7];
figure;
for alpha = alpha_values
    alpha_a = alpha;
    alpha_c = 1 - alpha;
    i_a =  i0 * exp((alpha_a * n * F * (E - E_eq)) / (R * T));
    i_c = -i0 * exp((-alpha_c * n * F * (E - E_eq)) / (R * T));
    i_net = i_a + i_c;
    plot(E, i_net, 'LineWidth', 2, 'DisplayName', sprintf('\\alpha=%.1f', alpha)); hold on;
end
plot(E, zeros(size(E)), 'k--', 'LineWidth', 1);
xlabel('Potential E (V vs SHE)');
ylabel('Current density (mA/cm^2)');
title('Effect of $\alpha$ on Tafel Plot', 'interpreter', 'latex');
    % remove legend border
legend('alpha : 0.3', 'alpha : 0.5', 'alpha : 0.7', 'Location', 'southeast');
    legend boxoff;
set(gca, 'FontSize', 14);
set(gca, 'LineWidth', 1.5);
set(gca, 'TickLength', [0.01, 0.01]);
set(gca, 'Position', [0.15 0.15 0.75 0.75]);  % manual tightening if needed
print("Tafel_alpha_plot.png", '-dpng');

