# Fe Hydrolysis Simulation


#### Initial values

| Header 1 | Header 2 | Header 3 |
| -------- | -------- | -------- |
| **K1**            | 1.0e-4;         |          |
| **K2**            | 1.0e-14         |          |
| **Ctot**          | 5.55e4;         |   $mol/m^3$         |
| **kb1**           | 2.78e3;         |   $s{}^-1$          |
| **kb2**           | 2.78e3;         |   $s^-1$          |


---
#### Initial mole fractions


| Header 1 | Header 2 |
| -------- | -------- |
| **xM**            |   0.1                |
| **xMOH**          |   0.0                |
| **xH**            |   $1e-12$             |
| **xOH**           |   $K_2 / x_H$         |
| **dt**            |   $1e-5$             |
| **Nt**            |   $2e5$              |


---
#### The governing hydrolysis reactions are:

$$
\mathrm{Fe^{2+} + H_2O \leftrightarrow FeOH^+ + H^+}
$$

##### Water self-ionization:
$$
\mathrm{H_2O \leftrightarrow H^+ + OH^-}
$$

##### Rate equations:

$$
\begin{aligned}
R_M   &= k_{b1}(-K_1 x_M + x_H x_{MOH}) \\
R_{MOH} &= k_{b1}( K_1 x_M - x_H x_{MOH}) \\
R_H   &= k_{b1}( K_1 x_M - x_H x_{MOH}) + k_{b2}(K_2 - x_H x_{OH}) \\
R_{OH} &= k_{b2}(K_2 - x_H x_{OH})
\end{aligned}
$$



## Concentration
![Concentration](./ReactionTime_Evolution_Concentrations.png =800x)

## Rates 
![Rates](./ReactionTime_Evolution_Rates.png =800x)



