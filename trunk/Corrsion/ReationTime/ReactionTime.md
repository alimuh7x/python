# Corrosion Reactions

## Initial values

| Constants | Values| Units |                                             Initial MF | Values | 
| -------- | -------- | :--------: |                                           -------- | :--------: |
| **K1**            | `1.0e-4   `      |  |                                    **xM**            |   `0.1        `  |
| **K2**            | `1.0e-14  `       |  |                                   **xMOH**          |   `0.0        `     |     
| **Ctot**          | `5.55e4   `      |  `  mol/m³`          |                **xH**            |   `1e-12      `      | 
| **kb1**           | `2.78e3   `      |  ` 1/s    `      |                    **xOH**           |   `K_2 / x_H  `      | 
| **kb2**           | `2.78e3   `      |  ` 1/s    `      |                    **dt**            |   `1e-5       `      |
                                                                               **Nt**            |   `2e5        `      |



---

## The governing hydrolysis reactions

$$
\mathrm{Fe^{2+} + H_2O \leftrightarrow FeOH^+ + H^+}
$$

### Water self-ionization:
$$
\mathrm{H_2O \leftrightarrow H^+ + OH^-}
$$


### Rate equations:

$$
\begin{aligned}
R_M   &= k_{b1}(-K_1 x_M + x_H x_{MOH}) \\
R_{MOH} &= k_{b1}( K_1 x_M - x_H x_{MOH}) \\
R_H   &= k_{b1}( K_1 x_M - x_H x_{MOH}) + k_{b2}(K_2 - x_H x_{OH}) \\
R_{OH} &= k_{b2}(K_2 - x_H x_{OH})
\end{aligned}
$$



## Concentration Evolution

<div style="display: flex; flex-wrap: wrap; gap: 10px;" markdown="1">
  <figure markdown="span" style="padding:4px; border-radius:6px; flex: 1 1 45%;">
    ![Final Concentration](./ReactionTime_Evolution_Concentrations.png){ width="600" }
    <figcaption>Concentration</figcaption>
  </figure>
</div>

## Concentration Rates 
<div style="display: flex; flex-wrap: wrap; gap: 10px;" markdown="1">
  <figure markdown="span" style="padding:4px; border-radius:6px; flex: 1 1 45%;">
    ![Final Concentration](./ReactionTime_Evolution_Concentrations.png){ width="600" }
    <figcaption>Concentration Rates</figcaption>
  </figure>
</div>    


