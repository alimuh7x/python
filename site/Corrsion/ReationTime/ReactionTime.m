#!/usr/bin/env -S octave --no-gui --quiet
set(0, "defaultfigurevisible", "off");  % hide figure window
addpath(genpath("./../../src"));        % add src folder to path
clc; clear; format long;

% === Corrosion hydrolysis reaction rates ===

% ==== constants ====
K1  = 1.0e-4;
K2  = 1.0e-14;

Ctot = 5.55e4;              % mol/m3, not used in mole-fraction form
kb1 = 2.78e3;               % s^-1
kb2 = 2.78e3;               % s^-1

% ==== initial mole fractions ====
xM   = 0.1;                 % Fe2+

xMOH = 0.0;                % FeOH+
xH   = 1e-12;                % H+
xOH  = K2 / xH;             % OH- from Kw
dt   = 1e-5;                % s

Nt   = 2e5;                 % number of steps
time = zeros(Nt,1);

% arrays for storage
xM_arr    = zeros(Nt,1);
xMOH_arr  = zeros(Nt,1);
xH_arr    = zeros(Nt,1);
xOH_arr   = zeros(Nt,1);
pH_arr    = zeros(Nt,1);

RM_arr    = zeros(Nt,1);
RMOH_arr  = zeros(Nt,1);
RH_arr    = zeros(Nt,1);
ROH_arr   = zeros(Nt,1);

pRH_arr   = zeros(Nt,1);


fprintf("===============================================================\n");
fprintf("---------------------------------------------------------------\n");
fprintf("===============================================================\n");
fprintf("K1*xM    = %.2e\n", K1*xM);
fprintf("xH*xMOH  = %.2e\n", xH*xMOH);
fprintf("xMOH     = %.2e\n", xMOH);
fprintf("xH       = %.2e\n", xH);
fprintf("xOH      = %.2e\n", xOH);
fprintf("---------------------------------------------------------------\n");


% ==== time loop ====
for n = 1:Nt
    % ------------------------------- Reaction rates--------------------------------------
    RM   = kb1*(-K1*xM + xH*xMOH);
    RMOH = kb1*( K1*xM - xH*xMOH);
    RH   = kb1*( K1*xM - xH*xMOH) + kb2*(K2 - xH*xOH);
    ROH  = kb2*(K2 - xH*xOH);

    RM_arr(n)   =  RM;
    RMOH_arr(n) = RMOH;
    RH_arr(n)   =  RH;
    ROH_arr(n)  =  ROH;


    % -------------------------------Update (explicit Euler)-----------------------------
    xM   += RM*dt;
    xMOH += RMOH*dt;
    xH   += RH*dt;
    xOH  += ROH*dt;

    % ------------------------------ safety: keep positive ------------------------------
    xM   = max(xM, 0);
    xMOH = max(xMOH, 0);
    xH   = max(xH, 1e-14);
    xOH  = max(xOH, 1e-14);

    % -------------------------------Store----------------------------------------------
    time(n)     =  n*dt;
    xM_arr(n)   =  xM;
    xMOH_arr(n) = xMOH;
    xH_arr(n)   =  xH;
    xOH_arr(n)  =  xOH;

    pH_arr(n)   =  -log10(xH*Ctot/1000);
    if mod(n, 1e4) == 0
        disp(['⏳  Time step: ', num2str(n), '/', num2str(Nt)]);
        fprintf("K1*xM    = %.2e\n", K1*xM);
        fprintf("xH*xMOH  = %.2e\n", xH*xMOH);
        fprintf("xMOH     = %.2e\n", xMOH);
        fprintf("xH       = %.2e\n", xH);
        fprintf("xOH      = %.2e\n", xOH);
        fprintf("---------------------------------------------------------------\n");
    end
end

Rarray = [time, RM_arr, RMOH_arr, RH_arr, ROH_arr];
xarray = [time, xM_arr, xMOH_arr, xH_arr, xOH_arr];
yNames_R = {"time", "R_M", "R_{MOH}", "R_H", "R_{OH}"};
yNames_x = {"time","c_M", "c_{MOH}", "c_H", "c_{OH}"};

Subplot4(Rarray, yNames_R, 'ReactionTime_Evolution_Rates.png');
Subplot4(xarray, yNames_x, 'ReactionTime_Evolution_Concentrations.png');


disp('✅  Saved: time_evolution_FeHydrolysis.png');


