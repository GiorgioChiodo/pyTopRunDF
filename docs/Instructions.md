# Instruction

## Preprocessing

Before starting a simulation with TopRunDF the following steps and
procedures have to be accomplished and considered by the user. The main
input parameters are:

-   A volume of the debris-flow event to be simulated. $[m^3]$

-   A mobility coefficient [-]

-   A start point of the simulation [X \| Y] 
  
-   A digital terrain model [ASCII-file format]

### Debris-flow event volume

The volume must correspond to the unit of length measurement used for
the projection of the digital terrain input model
[topofan.asc](topofan.asc). In the example the volume is given in $m^3$.

### Mobility coeffcient

The mobility coefficient $k_B$ is a dimensionless parameter and has to
be defined by the user. For back calculation it is recommended to
estimate $k_{obs}$ using the empirical relation: 

$k_{obs}=B_{obs}V_{obs}^{-2/3}$ \tag{1}

In equation (1), $B_{obs}$ is the planimetric deposition area $[L^2]$ and $V_{obs}$ the observed volume $[L^3]$.
In order to perform a forward analysis, $k_{Bpred}$ a mobility coefficient based on the average slope of the channel $S_c$
as well as the average slope of the fan $S_f$, can bei estimated [Scheidl and Rickenmann, 2009](https://onlinelibrary.wiley.com/doi/abs/10.1002/esp.1897{target=_blank})

$k_{Bpred}=5.07S_f^{-0.10}S_c^{-1.68}$ \tag{2}

If $k_{Bpred}$ is used, an uncertainty of a factor of two must be considered. See [Rickenmann et al. (2009)](https://www.e-periodica.ch/digbib/view?pid=wel-004%3A2010%3A102%3A%3A42{target=_blank}) (in german), [Scheidl and Rickenmann, 2009](https://onlinelibrary.wiley.com/doi/abs/10.1002/esp.1897) for more details.