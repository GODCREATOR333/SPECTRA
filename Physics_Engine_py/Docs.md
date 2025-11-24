SPECTRA/
├── config/                 <-- DON'T HARDCODE CONSTANTS. Put YAML/JSON configs here.
│   ├── sim_config.yaml
│   └── hardware_params.yaml
├── scripts/
│   └── run_sim.py          <-- Entry point.
├── src/                    <-- Use a src layout to prevent import errors.
│   └── scanner_sim/        <-- The actual package.
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── plant.py    <-- Abstract Base Class for the system (Sim vs HW).
│       │   ├── physics.py  <-- The differential equations (State Space models).
│       │   └── kinematics.py <-- Coordinate transforms (World -> Galvo -> Screen).
│       ├── control/
│       │   ├── __init__.py
│       │   ├── pid.py      <-- Simple controller for POC.
│       │   ├── lqr.py      <-- Advanced controller.
│       │   └── signals.py  <-- Waveform generators (Sine, Step, Raster).
│       ├── simulation/
│       │   ├── __init__.py
│       │   ├── loop.py     <-- The fixed-time-step integrator.
│       │   └── sensors.py  <-- Noise models and sensor discretization.
│       └── viz/
│           ├── __init__.py
│           ├── viewer.py   <-- OpenGL/PyQtGraph window.
│           └── render.py   <-- Separate the "what" from the "how".
├── tests/
├── requirements.txt
└── setup.py