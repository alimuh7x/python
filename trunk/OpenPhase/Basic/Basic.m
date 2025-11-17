#!/usr/bin/env -S octave --no-gui --quiet
set(0, "defaultfigurevisible", "off");  % hide figure window
addpath(genpath("./../src/"));  % add src folder to path

warning("off", "all");


fprintf("=============================================================== \n");

% --- Parameters ---
W = 1;          % double-well strength
kappa = 0.5;    % gradient coefficient
L = 20;         % domain length
Nx = 500;       % number of points

% --- Space and order parameter ---
x = linspace(-L/2, L/2, Nx);

phi = 0.5 * (1 + tanh(x));              % diffuse interface

% --- Derivatives and energies ---
dphidx = gradient(phi, x);

f_bulk = W * (phi.^2) .* ((1 - phi).^2);

f_grad = 0.5 * kappa * (dphidx.^2);

% Assuming you already have x and phi defined
phi_lower = 0.1;
phi_upper = 0.9;

% Find indices closest to phi = 0.1 and phi = 0.9
[~, i1] = min(abs(phi - phi_lower));
[~, i2] = min(abs(phi - phi_upper));


% Interface thickness
xi = abs(x(i2) - x(i1));

fprintf('Interface thickness ξ = %.4f\n', xi);


dx = x(2) - x(1);
F_total = trapz(x, f_bulk + f_grad);
fprintf('Total energy F = %.6f\n', F_total);

% ==============================
% Plot 1: single figure
% ==============================


P = GnuPlot("Emperical.png");
P.add_plot(x, phi, "x", "phi", "phi");
P.add_plot(x, f_bulk, "x", "potential", "potential");
P.add_plot(x, f_grad, "x", "grad", "grad");
P.set_xrange(-5,5);
P.set_yrange(-0.02, 1.02);
P.save();

disp('✅ Plots created and saved with Qt.');

fprintf("=============================================================== \n");

disp('---  By putting physical parameters ---');


eta = 4;
sigma = 1;

fprintf('Input sigma = %.6f\n', sigma);

phi = 0.5 * (1 + tanh(3 * x / eta));              % diffuse interface

dphidx = gradient(phi, x);

f_bulk = 18 * sigma / eta * (phi.^2) .* ((1 - phi).^2);

f_grad = 0.5 * sigma * eta * (dphidx.^2);

dx = x(2) - x(1);
F_total = trapz(x, f_bulk + f_grad);
fprintf('Total energy F = %.6f\n', F_total);

F_bulk = trapz(x, f_bulk);
fprintf('Potential energy F = %.6f\n', F_bulk);

F_grad = trapz(x, f_grad);
fprintf('Gradient energy F = %.6f\n', F_grad);

P = CurvePlot("physical.png");
P.plot_curve(x, phi, "x", "phi");
P.add_plot(x, f_bulk, "x", "potential");
P.add_plot(x, f_grad, "x", "grad");
P.save();

disp('✅ Plots created and saved with Qt.');




