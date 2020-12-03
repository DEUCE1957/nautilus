# Paper Notes

## Books

### Dive into Deep Learning
Source: https://d2l.ai/

Free-interactive textbook in Numpy, Pytorch and Tensorflow that has a good coverage of the mathematics of deep learning.

## Papers


### Learning to Simulate Complex Physics with Graph Networks
Source: https://arxiv.org/abs/2002.09405
Date: Feb 2020
Video: https://www.youtube.com/watch?v=2Bw5f4vYL98
Using graph-based representation of particles AI capable of continuing a fluid simulation based on existing simulation. Although pre-training is expensive, trained model is super fast. Takes 0.60s/step compared to 2.56s/step in original. Does not work as well outside of training domain. Handles water, smoke and sand. Able to be trained on small domains and upscale to larger domains. 


### Fast Fluid Simulations with Sparse Volumes on the GPU
Source: https://people.csail.mit.edu/kuiwu/gvdb_sim.html
Date: 2018
Paper: https://people.csail.mit.edu/kuiwu/GVDB_FLIP/gvdb_flip.pdf
Code: https://developer.nvidia.com/gvdb
Video: https://www.youtube.com/watch?v=i4KWiq3guRU
Handles tens of millions of particles in unbounded simulation domain using FLIP (Fluid Implicit Particle) (the same simulation model used in Blender!). Uses **sparse representation**, effecient parallel data gathering and fast incremental updates on the GPU for moving particles. Able to simulate 29 Million particles on a Quadro GP100 at 1.8s/frame. 


### Animating fluid sediment mixture in particle-laden flows
Source: https://dl.acm.org/doi/10.1145/3197517.3201309
Date: July 2018
Interaction of debris (e.g. sand) in fluids (water). Includes density correction step. Uses **Material Point Method**. Includes 100s of millions of points. Able to compute 1 frame in minutes.

### Real-Time Particle Systems in the Blender Game Engine
Source: https://fsu.digital.flvc.org/islandora/object/fsu%3A182933
Date: 2011
Developed a particle system library for Blender using Smoothed Particle Hydrodynamics. Achieved real-time performance (40fps/100,000 particles) using Nvidia GTX480

### A scalable Schur-complement fluids solver for heterogeneous compute platforms
Source: https://graphics.cs.wisc.edu/Papers/2016/LMAS16/
Video: https://www.youtube.com/watch?v=Yd4blFeRTEw
Allows large-scale fluid simulation on consumer GPUs by subdiving large fluid domains into smaller chunks (divide and conquer)


### Highly Adaptive Liquid Simulations on Tetrahedral Meshes
Source: http://pub.ist.ac.at/group_wojtan/projects/2013_Ando_HALSoTM/index.html
Code: http://pub.ist.ac.at/group_wojtan/projects/2013_Ando_HALSoTM/download/code.zip
Date: 2013
Speeds up simulation of large-scale fluid domains by applying adaptive resolution, with more resolution in visible (non-occluded) regions or interaction areas (e.g. collision with boundaries). Uses Tetrahedral Mesh Subdivision (discretization) to reduce complexity of pressure calculations. Finds 2nd order boundary conditions to allow for a free surface (i.e. surface tension). 

### Wavelet Turbulence for Fluid Simulation
Source: http://www.cs.cornell.edu/~tedkim/WTURB/
Date: 2008
Simulates high-resolution fluids in Blender by upsampling from a low-resolution simulation to a high-resolution one using Wavelet Decomposition instead of traditional Navier-Stokes equations.

### Fluid Simulation with Blender for Scientific Illustration
Source: https://go.gale.com/ps/anonymous?id=GALE%7CA611171887&sid=googleScholar&v=2.1&it=r&linkaccess=abs&issn=2446564X&p=IFME&sw=w
Date: July 2019
Example usage of built-in fluid simulation provided by Blender 3D.

### 'Rotor load prediction using downstream flow measurements' 
#### Abstract
Aim to decrease damage to turbine caused by large load fluctuations.

Explored:
* Flow Measure at 3 **downstream positions**
* 3 different **rotor depths**
* 3  Laser-Doppler Vibrometer **vertical positions** per rotor depth: Top, Centre, Depth

Calculated: **Time Lag** [Turbulent Structures and Wave-Induced Fluctuations]
* Linear Wave Theory + Classic Velocity ($v = d/t$) [Numerical Methods]
* Cross-Correlation Functions

    
Results:
* Good Agreement on LDV with:
    * Close downstream position to rotor
    * Placed on 'Top', near water surface
* If turbulent structure **Amplitude** is larger than wave-induced fluctuations can predict rotor load

#### Introduction
Want to anticipate large load to increase **survivability** and **predict power**.

Taylor's **Frozen Turbulence** hypothesis, turbulent structures travel with $v = d/t$. INCOMPLETE as wind evolves between upstream measurments and turbine location.

Flow **slows down** in front of rotor due to **upstream induction**. <br/>Range: 3 * Rotor Diameter.

#### Methology

##### Turbine Specifications
**Stanchion Diameter**: 0.105m <br/>
**Flume**: 4 x 2 x 18m (Controlled Environment) <br/>
**Rotor Depths**: 1m, 0.825m, 0.65m <br/>
**Centred**: 2m from side of walls <br/>
**LDV Locations**: 1m, 2m, 3m <br/>
**Rotor Measurements**: Top, Hub (Centre), Bottom (per rotor depth)
**Wave Measurements**: 0.78m from centre of rotor (rotor plane)

Turbine
* 3 Bladed
* Horizontal Axis
* Diameter: 0.9m (scaled down from 18m full-scale tidal turbine)
* Profile: **Wortman FX 63-137**
Model Development: 'The Development and Testing of a Lab-Scale Tidal Stream Turbine for the Study of Dynamic Device Loading'

Measurements:
* Rotor Torque
* Rotor Thrust Signals
* Out-of-plane bending moment (root bending moment from 1 blade used in study)
* Wave Height
* Local Speed at LDV 

#### Theory
##### Time Lag Calculation
For current-only cases:
$t_{lag} = \frac{x_{LDV}}{u}$ (1) <br/>
Waves superimposed on a mean current experience a **Doppler Shift**. Change in frequency experience by observer moving relative to wave source:
$\sigma = \omega - kU$ (2) <br/>
Where $\sigma$ is rotational frequency of waves seen from reference frame in which U=0 (i.e. viewer is moving with current) and $\omega$ is the rotational frequences of the waves seen from reference frame in which U is the current velocity. U is the streamwise flow velocity.

Free-propagating waves exist if **Frequency Dispersion Relation** is satisfied by wavenumber $k$. For deep water:
$\Omega = \sqrt{gk}$ (3) <br/>
And
$\Omega^2 = \sigma^2$ (4) <br/>
Where $\Omega$ is the **dispersion relation** and $g$ is **gravity**.

For waves following a current, combine eq. 2 and eq.4:
$\Omega^2 = (\omega - kU)^2$ (5)<br/> 
Combine eq.3 and eq.5:
$(\sqrt{gk})^2=(\omega-kU)^2$ (6)<br/>
Solve for angular frequency of waves $\omega$:
$\omega = kU + \sqrt(gk)$ (7) <br/>

Phase velocity of waves:
$c_p = \frac{\omega}{k}$ (8)<br/>
Wave Number:
$k=\frac{2\pi}{L}$ (9) <br/>
Wave Length:
$L=\frac{gT^2}{2\pi}$ (10) <br/>
Where T is the period of the wave.

Combining eqs 7,8,9,10:
$c_p = U + \frac{gT}{2\pi}$ (11) <br/>
Can also define phase velocity in terms of time lag and known distance from LDV position:
$c_p = \frac{x_{LDV}}{t_lag}$ (12) <br/>
Equating eqs. 11 and 12:
$t_lag = \frac{x_{LDV}}{U+\frac{gT}{2\pi}}$ (13) <br/>
Two velocities exist, one due to current and one due to waves - hence expect 2 time lags.

##### Loading and Power Output Prediction
Loading (thrust) of ideal turbine:
$T_{water} = \frac{1}{2} \rho Au^2$ (14) <br/>
Multiplying this by effeciency rating of turbine:
$T_{water} = \frac{1}{2} \rho Au^2C_{T,\lambda}$ (15) <br/>
Power output of ideal turbine:
$P_{water} = \frac{1}{2}\rho Au^3$ (16) <br/>
Multiplying this by effeciency rating of turbine:
$P_{water} = \frac{1}{2}\rho Au^3C_{P,\lambda}$ (17) <br/>


#### Results
**Conditions**: Current Only (C0) and JONSWAP (Current w. irregular waves).

**Reynolds Number**:
$R_e = \frac{\rho\bar{u}L_{chord}}{\mu}$ <br/>
Where $L_{chord} = 0.7 * blade-length$.

Turbine Intensity in 2D is calculated by:
$TI_{2D} = 100 \times \sqrt{\frac{1}{2}(\frac{\sigma_u^2 + \sigma_v^2)}{\bar{u}^2+\bar{v}^2}}$ (18) <br/>

Turbine Kinetic Energy is given by:
$TKE_{2D}=\frac{1}{2}(\sigma_u^2+\sigma_v^2)$ <br/>

Current-only has (marginally) hgigher Turbine Intensity values than Current+Wave.

Estimate **Integral Length Scale** and **Integral Time Scale**.
$\Tau = \int_0^{T_0} R(t')\cdot dt'$ (19) <br/>
Where:
$R(t') = \frac{\bar{u'(t)u'(t-t')}}{\sigma_u^2}$ (20) <br/>
For length scale use velocity equation:
$L = \bar{u_x}\cdot T$ <br/>
Find that Integral length Scale is of the order of submergence depth of the wave maker.

Power Spectral Densitities calculated for each flow velocity time series captured in wave-number space (i.e. k-space).
$E(K) = \int_{-\infty}^{\infty} R(t')e^(-iKt')dt'$ (21) <br/>
Where:
$K = \frac{2\pi f}{U}$

Observe reduction in energy at low K. See some devitation from 5/3 law.

Turbulent Energy more important than wave contributions to fluid velocity fluctuations. Spectral Energy is a function of depth, with greater energy near the surface, but presence of waves has little impact.

Kolomogoroff's Law (Asssumes Homogenous, Isotropic Turbulent Fluctuations):
$E(K) = C\epsilon^{2/3}K^{\beta}$ (23) <br/>
Where $\beta$ is the slope of the spectral energy and $epsilon$ is the TKE dissipation rate:
$\epsilon = \frac{C_o^{3/2}}{C}$ (24) <br/>

##### **Load Ranges - Rotor Depth**
Setup used at varying depths:
* Wavelength: 4m
* Rotational Speed of turbine: 85 RPM +- 2% (std dev.)
* Flow Velocity: 1m/s
Closer to surface: Average Thurst reduced by ~12%. I.e. thrust increases with depth. Due to flow-velocity deficit near surface.
Current-only versus current-plus-waves has negligible impact on Average Thrust. 
Std. Dev in load increases as rotor depth decreases(about 1.5x near surface relative to mid-depth)
Good agreement with previous studies with similar turbine model.

##### **Load ranges - Angular Position**
Each blade is 120* from the next, which is seen in RBM signal for turbine (With 45* shift).

Increased rotor depth, increased operational range of RBM signals (from 6% to 12%).

Load on rotor is NOT symmetrical, can cause damage.

##### **Single-Event Load Anticipation**
Time lag for current-only case:
$t_{lag} = \frac{x_{LDV}}{u}$ (1) <br/>
Time lag for irregular wave case:
$t_lag = \frac{x_{LDV}}{U+\frac{gT}{2\pi}}$ (13) <br/>
Cross-Correlation Timelab obtained using **xcorr** function in MATLAB.

For current-only find calculated lag matches best when LDV probe is close to rotor and to the water surface.

For irregular-waves find calculate lag metches best when using $\frac{u}{T}$. 

##### **2 lag hypothesis** <br/>
Cross-correlation **xcorr** does between upstream LDV signal and rotor thrust does not work all the time: Flow Velocity is different from Phase Velocity but xcorr can only identify one.

Both current and waves have tangible influence on the rotor loads with their own time signatures.

If flow measurements too far upstream (>3D) OR too deep, cross-correlation fails on wave patterns but still holds for **mean flow**.