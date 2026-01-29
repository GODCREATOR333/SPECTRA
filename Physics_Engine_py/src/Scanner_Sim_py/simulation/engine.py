import sys
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from pyqtgraph.opengl import GLMeshItem, GLTextItem, GLLinePlotItem
from PyQt5 import QtGui, QtCore, QtWidgets

# --- MODULE IMPORTS ---
from Scanner_Sim_py.visualization.viewer import MyView
from Scanner_Sim_py.visualization import geometry
from Scanner_Sim_py.core import kinematics
from Scanner_Sim_py.core import physics
from Scanner_Sim_py.core.plant_model import GalvoModel

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Laser Scanning Physics Engine (HIL Simulation)")
        
        # 1. Window Sizing
        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        self.resize(min(1400, screen.width()), min(900, screen.height()))

        # 2. Initialize System
        self.galvo_system = GalvoModel()
        self.objects = {} # Stores 3D mesh items
        
        # State Flags
        self.simulation_active = False
        self.time_elapsed = 0.0
        self.history_len = 500 # How many points to keep in plots

        # Data Buffers for Plotting
        self.data_time = np.zeros(self.history_len)
        self.data_target_x = np.zeros(self.history_len)
        self.data_actual_x = np.zeros(self.history_len)
        self.data_error_x = np.zeros(self.history_len)

        # 3. UI Layout Setup
        self.init_ui()

        # 4. 3D Scene Setup
        self.setup_scene()

        # 5. Timer (The Heartbeat)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.simulation_step)
        # 60 FPS target
        self.timer.setInterval(16) 

    def init_ui(self):
        """Builds the 3-pane layout similar to the Bio-Inspired Project."""
        
        # ============================
        # OUTER SPLITTER (Left | Right)
        # ============================
        self.outer_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.outer_splitter.setHandleWidth(6)
        
        # ============================
        # 1. SIDEBAR (Left)
        # ============================
        self.sidebar = QtWidgets.QWidget()
        sidebar_layout = QtWidgets.QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(8, 8, 8, 8)
        sidebar_layout.setSpacing(8)

        # A. Instructions / Legend
        self.instructions = QtWidgets.QTextEdit()
        self.instructions.setReadOnly(True)
        self.instructions.setMaximumHeight(150)
        self.instructions.setStyleSheet("background-color: #222; color: #EEE;")
        self.instructions.setPlainText(
            "=== LASER STEERING SIM ===\n"
            "   [Left Click]     : Orbit View\n"
            "   [Right Click]    : Pan View\n"
            "   [Scroll]         : Zoom\n\n"
            "=== LEGEND ===\n"
            "   Red Box      : X-Mirror (Fast Axis)\n"
            "   Blue Box     : Y-Mirror (Slow Axis)\n"
            "   Magenta Line : Laser Beam\n"
            "   Green Line   : Trace History\n"
        )
        sidebar_layout.addWidget(self.instructions)

        # B. Parameter Scroll Area
        param_scroll = QtWidgets.QScrollArea()
        param_scroll.setWidgetResizable(True)
        param_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        
        param_container = QtWidgets.QWidget()
        param_layout = QtWidgets.QVBoxLayout(param_container)

        # --- Group 1: Signal Generator ---
        sig_group = QtWidgets.QGroupBox("Input Signal (Target)")
        sig_form = QtWidgets.QFormLayout(sig_group)
        
        self.freq_input = QtWidgets.QDoubleSpinBox()
        self.freq_input.setRange(0.1, 50.0)
        self.freq_input.setValue(1.0)
        self.freq_input.setSuffix(" Hz")
        
        self.amp_input = QtWidgets.QDoubleSpinBox()
        self.amp_input.setRange(0.0, 15.0)
        self.amp_input.setValue(10.0)
        self.amp_input.setSuffix(" deg")

        sig_form.addRow("Frequency", self.freq_input)
        sig_form.addRow("Amplitude", self.amp_input)
        param_layout.addWidget(sig_group)

        # --- Group 2: Plant Physics (The Hardware) ---
        plant_group = QtWidgets.QGroupBox("Actuator Physics")
        plant_form = QtWidgets.QFormLayout(plant_group)
        
        self.inertia_input = QtWidgets.QDoubleSpinBox()
        self.inertia_input.setRange(0.1, 10.0)
        self.inertia_input.setValue(0.5)
        self.inertia_input.setSingleStep(0.1)

        self.damping_input = QtWidgets.QDoubleSpinBox()
        self.damping_input.setRange(0.0, 10.0)
        self.damping_input.setValue(2.0)
        
        self.stiffness_input = QtWidgets.QDoubleSpinBox()
        self.stiffness_input.setRange(0.0, 50.0)
        self.stiffness_input.setValue(0.0)
        
        plant_form.addRow("Inertia (J)", self.inertia_input)
        plant_form.addRow("Damping (b)", self.damping_input)
        plant_form.addRow("Stiffness (k)", self.stiffness_input)
        param_layout.addWidget(plant_group)

        # Add stretch to push everything up
        param_layout.addStretch()
        param_scroll.setWidget(param_container)
        sidebar_layout.addWidget(param_scroll)

        # C. Console Log
        log_group = QtWidgets.QGroupBox("System Log")
        log_layout = QtWidgets.QVBoxLayout(log_group)
        self.console = QtWidgets.QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("background:#111; color:#0f0; font-family:monospace; font-size:9pt;")
        self.console.setPlainText("--- SYSTEM READY ---")
        log_layout.addWidget(self.console)
        sidebar_layout.addWidget(log_group)

        # D. Buttons
        controls = QtWidgets.QHBoxLayout()
        self.start_button = QtWidgets.QPushButton("START")
        self.stop_button = QtWidgets.QPushButton("STOP")
        self.stop_button.setEnabled(False)
        
        self.start_button.clicked.connect(self.start_simulation)
        self.stop_button.clicked.connect(self.stop_simulation)
        
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
        sidebar_layout.addLayout(controls)

        self.outer_splitter.addWidget(self.sidebar)

        # ============================
        # 2. RIGHT SIDE (View + Plots)
        # ============================
        self.right_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)

        # A. 3D View (Top)
        self.view = MyView()
        self.right_splitter.addWidget(self.view)

        # B. Plots (Bottom)
        bottom_plot_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        
        # Plot 1: Tracking (Target vs Actual)
        self.tracking_plot = pg.PlotWidget(title="X-Axis Tracking Response")
        self.tracking_plot.showGrid(x=True, y=True)
        self.tracking_plot.setLabel('left', 'Angle (deg)')
        self.tracking_plot.addLegend()
        self.curve_target = self.tracking_plot.plot(pen=pg.mkPen('y', width=2, style=QtCore.Qt.DashLine), name="Target")
        self.curve_actual = self.tracking_plot.plot(pen=pg.mkPen('c', width=2), name="Actual")
        
        # Plot 2: Error
        self.error_plot = pg.PlotWidget(title="Tracking Error")
        self.error_plot.showGrid(x=True, y=True)
        self.error_plot.setLabel('left', 'Error (deg)')
        self.curve_error = self.error_plot.plot(pen=pg.mkPen('r', width=2), name="Error")

        bottom_plot_splitter.addWidget(self.tracking_plot)
        bottom_plot_splitter.addWidget(self.error_plot)
        
        # Add plots to vertical splitter
        self.right_splitter.addWidget(bottom_plot_splitter)

        # Set initial sizes for vertical splitter (View gets more space)
        self.right_splitter.setSizes([600, 250])

        self.outer_splitter.addWidget(self.right_splitter)
        self.outer_splitter.setSizes([300, 900]) # Sidebar 300px, Right 900px

        # Set Main Layout
        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(self.outer_splitter)
        layout.setContentsMargins(0,0,0,0)

    def setup_scene(self):
        """Initializes the 3D world: Grids, Frames, Mirrors, Laser."""
        
        # 1. Grids
        gx = gl.GLGridItem(); gx.setSize(100, 100); gx.setSpacing(10, 10)
        gx.rotate(90, 0, 1, 0); gx.translate(-50, 0, 0)
        self.view.addItem(gx)
        
        gz = gl.GLGridItem(); gz.setSize(100, 100); gz.setSpacing(10, 10)
        gz.translate(0, 0, -50)
        self.view.addItem(gz)

        # 2. Axes
        self.view.addItem(geometry.axis_line([0,0,0], [60,0,0], (1,0,0,1)))
        self.view.addItem(geometry.axis_line([0,0,0], [0,60,0], (0,1,0,1)))
        self.view.addItem(geometry.axis_line([0,0,0], [0,0,60], (0,0,1,1)))

        # 3. Mirrors (Initial State)
        # Red Mirror (X)
        mesh1 = geometry.create_cuboid(20, 10, 1)
        self.objects["Cuboid 1 (Red)"] = GLMeshItem(meshdata=mesh1, smooth=False, 
            drawEdges=True, color=(1, 0, 0, 0.6), shader='balloon')
        self.view.addItem(self.objects["Cuboid 1 (Red)"])

        # Blue Mirror (Y/Z)
        mesh2 = geometry.create_cuboid(10, 20, 1)
        self.objects["Cuboid 2 (Blue)"] = GLMeshItem(meshdata=mesh2, smooth=False, 
            drawEdges=True, color=(0, 0, 1, 0.6), shader='balloon')
        self.view.addItem(self.objects["Cuboid 2 (Blue)"])

        # 4. Laser Lines
        self.laser_plot = GLLinePlotItem(pos=np.array([[0,0,0], [0,0,0]]), color=(1, 0, 1, 1), width=3, antialias=True)
        self.view.addItem(self.laser_plot)
        self.laser_source = np.array([50, 0, 0])

        # 5. Screen & Trace
        self.screen_grid = gl.GLGridItem()
        self.screen_grid.setSize(70, 70); self.screen_grid.setSpacing(5, 5)
        self.screen_grid.translate(0, 20, 50)
        self.view.addItem(self.screen_grid)

        self.trace_plot = GLLinePlotItem(pos=np.array([[0,0,0]]), color=(0, 1, 0, 1), width=2, antialias=True)
        self.view.addItem(self.trace_plot)
        self.trace_points = []
        
        # Initial Transform Update
        self.update_visuals()

    def log(self, message):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.append(f"[{timestamp}] {message}")
        sb = self.console.verticalScrollBar()
        sb.setValue(sb.maximum())

    # --- SIMULATION CONTROL ---

    def start_simulation(self):
        self.simulation_active = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # Lock Parameters
        self.inertia_input.setEnabled(False)
        self.damping_input.setEnabled(False)
        
        # Apply Parameters to Plant
        self.apply_parameters()
        
        # Reset Data
        self.trace_points = []
        self.time_elapsed = 0.0
        self.data_time[:] = 0
        self.data_target_x[:] = 0
        self.data_actual_x[:] = 0
        self.data_error_x[:] = 0
        
        self.timer.start()
        self.log("Simulation Started.")

    def stop_simulation(self):
        self.simulation_active = False
        self.timer.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        # Unlock Parameters
        self.inertia_input.setEnabled(True)
        self.damping_input.setEnabled(True)
        
        self.log("Simulation Stopped.")

    def apply_parameters(self):
        # Push UI values to the Physics Object
        # Note: We update both axes with the same physics for now
        J = self.inertia_input.value()
        b = self.damping_input.value()
        k = self.stiffness_input.value()
        
        self.galvo_system.galvo_x.J = J
        self.galvo_system.galvo_x.b = b
        self.galvo_system.galvo_x.k = k
        
        self.galvo_system.galvo_y.J = J
        self.galvo_system.galvo_y.b = b
        self.galvo_system.galvo_y.k = k

        self.log(f"Params Applied: J={J}, b={b}, k={k}")

    # --- MAIN LOOP ---

    def simulation_step(self):
        if not self.simulation_active: return

        dt = 0.016 # 16ms
        self.time_elapsed += dt

        # 1. Generate Signal (Sine Wave)
        freq = self.freq_input.value()
        amp = self.amp_input.value()
        
        target_x = amp * np.sin(2 * np.pi * freq * self.time_elapsed)
        target_y = amp * np.cos(2 * np.pi * freq * self.time_elapsed)

        # 2. Physics Update
        self.galvo_system.set_target(target_x, target_y)
        self.galvo_system.update() # Note: Your plant_model currently assumes hardcoded dt=0.01, we might want to pass dt later
        
        # 3. Visual Update (Mirrors & Lasers)
        self.update_visuals()

        # 4. Plot Update
        # Roll data arrays (Shift left, add new at right)
        self.data_time = np.roll(self.data_time, -1)
        self.data_target_x = np.roll(self.data_target_x, -1)
        self.data_actual_x = np.roll(self.data_actual_x, -1)
        self.data_error_x = np.roll(self.data_error_x, -1)

        current_angle_x = self.galvo_system.state["Cuboid 1 (Red)"]['current_angle']
        
        self.data_time[-1] = self.time_elapsed
        self.data_target_x[-1] = target_x
        self.data_actual_x[-1] = current_angle_x
        self.data_error_x[-1] = target_x - current_angle_x

        # Update Curves
        self.curve_target.setData(self.data_time, self.data_target_x)
        self.curve_actual.setData(self.data_time, self.data_actual_x)
        self.curve_error.setData(self.data_time, self.data_error_x)

    def update_visuals(self):
        # Retrieve State
        red_current = self.galvo_system.state["Cuboid 1 (Red)"]['current_angle']
        blue_current = self.galvo_system.state["Cuboid 2 (Blue)"]['current_angle']
        
        # --- 1. Update Matrix Transforms (Kinematics) ---
        
        # Blue Mirror (Origin, Z-Rotation)
        b_pos = self.galvo_system.static_states["Cuboid 2 (Blue)"]['pos']
        b_rest = self.galvo_system.static_states["Cuboid 2 (Blue)"]['rest_rot_z']
        
        m_blue_phys = kinematics.get_model_matrix(b_pos, b_rest + blue_current, [0,0,1])
        m_blue_vis = kinematics.get_model_matrix([0,0,0], 90, [1,0,0]) # Visual correction to stand up
        matrix_blue = m_blue_phys @ m_blue_vis
        self.objects["Cuboid 2 (Blue)"].setTransform(pg.Transform3D(*matrix_blue.flatten()))

        # Red Mirror (Y=20, X-Rotation)
        r_pos = self.galvo_system.static_states["Cuboid 1 (Red)"]['pos']
        r_rest = self.galvo_system.static_states["Cuboid 1 (Red)"]['rest_rot_x']
        
        matrix_red = kinematics.get_model_matrix(r_pos, r_rest + red_current, [1,0,0])
        self.objects["Cuboid 1 (Red)"].setTransform(pg.Transform3D(*matrix_red.flatten()))

        # --- 2. Ray Tracing (Physics) ---
        
        # Path 1: Source -> Blue
        p1 = np.array(b_pos)
        dir_1 = physics.normalize(p1 - self.laser_source)
        
        # Normal 1
        n1 = kinematics.apply_transform_to_vector(matrix_blue, [0, 0, 1])
        n1 = physics.normalize(n1)
        r1 = physics.calculate_reflection(dir_1, n1)

        # Path 2: Blue -> Red
        plane_point_red = np.array(r_pos)
        plane_normal_red = np.array([0, -1, 0]) # Red mirror faces -Y
        p2, t2 = physics.intersect_line_plane(p1, r1, plane_point_red, plane_normal_red)

        # Draw partial beam if miss
        if t2 <= 0 or abs(p2[0]) > 10.0:
            self.laser_plot.setData(pos=np.array([self.laser_source, p1, p1 + r1*20]))
            return

        # Path 3: Red -> Screen
        n2 = kinematics.apply_transform_to_vector(matrix_red, [0, 0, 1])
        n2 = physics.normalize(n2)
        r2 = physics.calculate_reflection(r1, n2)

        plane_point_screen = np.array([0, 0, 50])
        plane_normal_screen = np.array([0, 0, -1])
        p3, t3 = physics.intersect_line_plane(p2, r2, plane_point_screen, plane_normal_screen)

        if t3 <= 0: p3 = p2 + r2 * 20 # Infinite ray if miss
        
        self.laser_plot.setData(pos=np.array([self.laser_source, p1, p2, p3]))

        # --- 3. Trace Logic ---
        if self.simulation_active and t3 > 0:
            self.trace_points.append(p3)
            if len(self.trace_points) > 500: self.trace_points.pop(0)
            if len(self.trace_points) > 1:
                self.trace_plot.setData(pos=np.array(self.trace_points))