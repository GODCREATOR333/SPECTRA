import sys
import numpy as np
import random
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
from Scanner_Sim_py.core.inverse_kinematics import IKSolver
# NEW IMPORT
from Scanner_Sim_py.core.vision_system import VisionWorker
from Scanner_Sim_py.controller.pid_controller import PController, PIDController, LQRController

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Laser Scanning Physics Engine (HIL Simulation)")
        
        # 1. Window Sizing
        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        self.resize(min(1400, screen.width()), min(900, screen.height()))

        # 2. Initialize System
        self.galvo_system = GalvoModel()
        self.ik_solver = IKSolver()
        self.objects = {} 

        # Create Controller Instances
        self.controllers = {
            "Proportional (P)": PController(Kp=8.0),
            "PID Control": PIDController(Kp=1.0, Ki=3.0, Kd=0.2),
            "LQR (State Space)": LQRController()
        }
        self.active_controller = self.controllers["Proportional (P)"]

        # Target Weed Position [x, y, z] (Screen is at Z=100)
        self.current_target_pos = [0.0, 0.0, 100.0] 
        
        # --- VISION SYSTEM INTEGRATION ---
        # Initialize the background thread
        self.vision_thread = VisionWorker()
        
        # Connect Signals
        self.vision_thread.target_detected.connect(self.update_target_from_camera)
        self.vision_thread.frame_signal.connect(self.update_video_feed) # <--- NEW: Video Feed Connection
        
        # Start the camera immediately
        self.vision_thread.start()

        # State Flags
        self.simulation_active = False
        self.time_elapsed = 0.0
        self.history_len = 30

        # Data Buffers
        self.data_time = np.zeros(self.history_len)
        self.data_target_x = np.zeros(self.history_len)
        self.data_actual_x = np.zeros(self.history_len)
        self.data_error_x = np.zeros(self.history_len)

        # 3. UI Layout Setup
        self.init_ui()

        # 4. 3D Scene Setup
        self.setup_scene()

        # 5. Timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.simulation_step)
        self.timer.setInterval(16) 

    def closeEvent(self, event):
        """Cleanup when closing the window"""
        self.vision_thread.stop()
        event.accept()

    def init_ui(self):
        """Builds the 3-pane layout."""
        
        self.outer_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.outer_splitter.setHandleWidth(6)
        
        # ============================
        # 1. SIDEBAR
        # ============================
        self.sidebar = QtWidgets.QWidget()
        sidebar_layout = QtWidgets.QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(8, 8, 8, 8)
        sidebar_layout.setSpacing(8)

        # A. Instructions
        self.instructions = QtWidgets.QTextEdit()
        self.instructions.setReadOnly(True)
        self.instructions.setMaximumHeight(100)
        self.instructions.setStyleSheet("background-color: #FFFFFF; color: #000000; font-family: sans-serif;")
        self.instructions.setPlainText(
            "=== HIL SIMULATION ===\n"
            "   Status: VISION SYSTEM ACTIVE\n"
            "   Input:  PS3 Eye Camera (Live)\n"
            "   Detections are highlighted in Green."
        )
        sidebar_layout.addWidget(self.instructions)

        # B. CAMERA FEED (NEW)
        cam_group = QtWidgets.QGroupBox("Live Camera Feed")
        cam_layout = QtWidgets.QVBoxLayout(cam_group)
        
        # This Label will act as our Screen
        self.video_label = QtWidgets.QLabel("Waiting for Camera...")
        
        # --- FIX: FORCE A FIXED SIZE SO IT CANNOT GROW ---
        self.video_label.setFixedSize(640, 480) 
        # ------------------------------------------------
        
        self.video_label.setAlignment(QtCore.Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black; color: white; border: 1px solid #333;")
        
        cam_layout.addWidget(self.video_label)
        
        # Coordinate Labels
        self.lbl_cam_x = QtWidgets.QLabel("Detected X: 0.00 cm")
        self.lbl_cam_y = QtWidgets.QLabel("Detected Y: 0.00 cm")
        self.lbl_cam_x.setStyleSheet("font-weight: bold; color: green;")
        self.lbl_cam_y.setStyleSheet("font-weight: bold; color: green;")
        
        cam_layout.addWidget(self.lbl_cam_x)
        cam_layout.addWidget(self.lbl_cam_y)
        
        sidebar_layout.addWidget(cam_group)

        # B. Parameter Scroll Area (Physics)
        param_scroll = QtWidgets.QScrollArea()
        param_scroll.setWidgetResizable(True)
        param_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        
        param_container = QtWidgets.QWidget()
        param_layout = QtWidgets.QVBoxLayout(param_container)

        # --- Group 2: Plant Physics ---
        plant_group = QtWidgets.QGroupBox("Actuator Physics")
        plant_form = QtWidgets.QFormLayout(plant_group)


        # NEW: Controller Selector
        self.algo_selector = QtWidgets.QComboBox()
        self.algo_selector.addItems(self.controllers.keys())
        self.algo_selector.currentTextChanged.connect(self.change_controller)
        plant_form.addRow("Control Strategy:", self.algo_selector)
        
        # CHANGE THESE DEFAULTS:
        self.inertia_input = QtWidgets.QDoubleSpinBox()
        self.inertia_input.setRange(0.01, 10.0)
        self.inertia_input.setValue(0.02)          # <--- Low Inertia (Fast)
        self.inertia_input.setSingleStep(0.01)

        self.damping_input = QtWidgets.QDoubleSpinBox()
        self.damping_input.setRange(0.0, 10.0)
        self.damping_input.setValue(1.5)           # <--- Tuned Damping
        
        self.stiffness_input = QtWidgets.QDoubleSpinBox()
        self.stiffness_input.setRange(0.0, 50.0)
        self.stiffness_input.setValue(0.0)
        
        plant_form.addRow("Inertia (J)", self.inertia_input)
        plant_form.addRow("Damping (b)", self.damping_input)
        plant_form.addRow("Stiffness (k)", self.stiffness_input)
        param_layout.addWidget(plant_group)

        param_layout.addStretch()
        param_scroll.setWidget(param_container)
        sidebar_layout.addWidget(param_scroll)

        # C. Console
        log_group = QtWidgets.QGroupBox("System Log")
        log_layout = QtWidgets.QVBoxLayout(log_group)
        self.console = QtWidgets.QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("background:#111; color:#0f0; font-family:monospace; font-size:9pt;")
        self.console.setPlainText("--- WAITING FOR CAMERA ---")
        log_layout.addWidget(self.console)
        sidebar_layout.addWidget(log_group)

        # D. Buttons
        controls = QtWidgets.QHBoxLayout()
        self.start_button = QtWidgets.QPushButton("START TRACKING")
        self.stop_button = QtWidgets.QPushButton("STOP")
        self.stop_button.setEnabled(False)
        
        self.start_button.clicked.connect(self.start_simulation)
        self.stop_button.clicked.connect(self.stop_simulation)
        
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
        sidebar_layout.addLayout(controls)

        self.outer_splitter.addWidget(self.sidebar)

        # ============================
        # 2. RIGHT SIDE
        # ============================
        self.right_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)

        self.view = MyView()
        self.right_splitter.addWidget(self.view)

        # Plots
        bottom_plot_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        
        self.tracking_plot = pg.PlotWidget(title="X-Axis Response (Live)")
        self.tracking_plot.showGrid(x=True, y=True)
        self.tracking_plot.addLegend()
        self.curve_target = self.tracking_plot.plot(pen=pg.mkPen('y', width=2, style=QtCore.Qt.DashLine), name="Vision Target")
        self.curve_actual = self.tracking_plot.plot(pen=pg.mkPen('c', width=2), name="Laser Position")
        
        self.error_plot = pg.PlotWidget(title="Tracking Error")
        self.error_plot.showGrid(x=True, y=True)
        self.curve_error = self.error_plot.plot(pen=pg.mkPen('r', width=2), name="Error")

        bottom_plot_splitter.addWidget(self.tracking_plot)
        bottom_plot_splitter.addWidget(self.error_plot)
        self.right_splitter.addWidget(bottom_plot_splitter)
        self.right_splitter.setSizes([600, 250])

        self.outer_splitter.addWidget(self.right_splitter)
        self.outer_splitter.setSizes([300, 900]) 

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(self.outer_splitter)
        layout.setContentsMargins(0,0,0,0)

    def change_controller(self, text):
        self.active_controller = self.controllers[text]
        self.log(f"Switched to {text}")

    def setup_scene(self):
        # ... (Same as before) ...
        gx = gl.GLGridItem(); gx.setSize(100, 100); gx.setSpacing(10, 10)
        gx.rotate(90, 0, 1, 0); gx.translate(-50, 0, 0)
        self.view.addItem(gx)
        
        gz = gl.GLGridItem(); gz.setSize(100, 100); gz.setSpacing(10, 10)
        gz.translate(0, 0, -50)
        self.view.addItem(gz)

        self.view.addItem(geometry.axis_line([0,0,0], [60,0,0], (1,0,0,1)))
        self.view.addItem(geometry.axis_line([0,0,0], [0,60,0], (0,1,0,1)))
        self.view.addItem(geometry.axis_line([0,0,0], [0,0,60], (0,0,1,1)))

        mesh1 = geometry.create_cuboid(20, 10, 1)
        self.objects["Cuboid 1 (Red)"] = GLMeshItem(meshdata=mesh1, smooth=False, drawEdges=True, color=(1, 0, 0, 0.6), shader='balloon')
        self.view.addItem(self.objects["Cuboid 1 (Red)"])

        mesh2 = geometry.create_cuboid(10, 20, 1)
        self.objects["Cuboid 2 (Blue)"] = GLMeshItem(meshdata=mesh2, smooth=False, drawEdges=True, color=(0, 0, 1, 0.6), shader='balloon')
        self.view.addItem(self.objects["Cuboid 2 (Blue)"])

        self.laser_plot = GLLinePlotItem(pos=np.array([[0,0,0], [0,0,0]]), color=(1, 0, 1, 1), width=3, antialias=True)
        self.view.addItem(self.laser_plot)
        self.laser_source = np.array([50, 0, 0])

        self.screen_grid = gl.GLGridItem(); self.screen_grid.setSize(100, 100); self.screen_grid.setSpacing(5, 5)
        self.screen_grid.translate(0, 0, 100) 
        self.screen_grid.setColor((0, 1, 0, 0.3))
        self.view.addItem(self.screen_grid)

        self.trace_plot = GLLinePlotItem(pos=np.array([[0,0,0]]), color=(0, 1, 0, 1), width=2, antialias=True)
        self.view.addItem(self.trace_plot)
        self.trace_points = []

        md = gl.MeshData.sphere(rows=10, cols=20, radius=2.0)
        self.target_marker = gl.GLMeshItem(meshdata=md, smooth=True, color=(0, 1, 0, 1), shader='balloon')
        self.target_marker.translate(0, 0, 100) 
        self.view.addItem(self.target_marker)
        
        self.update_visuals()

    def log(self, message):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.append(f"[{timestamp}] {message}")
        sb = self.console.verticalScrollBar()
        sb.setValue(sb.maximum())

    # --- VIDEO CALLBACK (NEW) ---
    def update_video_feed(self, frame):
        """Receives RGB frame from VisionWorker and displays it in the sidebar."""
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        
        # Create QImage with .copy()
        qt_img = QtGui.QImage(frame.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888).copy()
        
        # --- FIX: SCALE TO THE FIXED SIZE  ---
        pixmap = QtGui.QPixmap.fromImage(qt_img).scaled(
            640, 480, 
            QtCore.Qt.KeepAspectRatio, 
            QtCore.Qt.SmoothTransformation
        )
        # ----------------------------------------------
        
        self.video_label.setPixmap(pixmap)

    # --- CAMERA TARGET CALLBACK ---

    def update_target_from_camera(self, x, y, z):
        """Called whenever YOLO detects a weed"""
        self.current_target_pos = [x, y, 100.0]
        
        # Update labels
        self.lbl_cam_x.setText(f"Detected X: {x:.2f} cm")
        self.lbl_cam_y.setText(f"Detected Y: {y:.2f} cm")
        
        # Update Visual Marker
        self.target_marker.resetTransform()
        self.target_marker.translate(x, y, 100.0)

    # --- SIMULATION CONTROL ---

    def start_simulation(self):
        self.simulation_active = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.inertia_input.setEnabled(False)
        self.damping_input.setEnabled(False)
        self.apply_parameters()
        self.trace_points = []
        self.time_elapsed = 0.0
        self.timer.start()
        self.log("Tracking Started. Laser is Active.")

    def stop_simulation(self):
        self.simulation_active = False
        self.timer.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.inertia_input.setEnabled(True)
        self.damping_input.setEnabled(True)
        self.log("Tracking Stopped.")

    def apply_parameters(self):
        J = self.inertia_input.value()
        b = self.damping_input.value()
        k = self.stiffness_input.value()
        self.galvo_system.galvo_x.J = J; self.galvo_system.galvo_x.b = b; self.galvo_system.galvo_x.k = k
        self.galvo_system.galvo_y.J = J; self.galvo_system.galvo_y.b = b; self.galvo_system.galvo_y.k = k

    # --- MAIN LOOP ---

    def simulation_step(self):
        if not self.simulation_active: return

        # Visual Frame Time
        visual_dt = 0.016 
        self.time_elapsed += visual_dt

        # 1. GET TARGET
        # self.current_target_pos
        
        # 2. SOLVE IK
        req_theta_x, req_theta_y = self.ik_solver.solve(self.current_target_pos)

        # 3. PHYSICS SUB-STEPPING (The Magic Fix)
        # We run physics 10 times faster than visuals for stability
        sub_steps = 10
        physics_dt = visual_dt / sub_steps
        
        for _ in range(sub_steps):
            # A. Control Loop
            state_x = self.galvo_system.galvo_x.state
            state_y = self.galvo_system.galvo_y.state
            
            vx = self.active_controller.calculate(req_theta_x, state_x, physics_dt)
            vy = self.active_controller.calculate(req_theta_y, state_y, physics_dt)
            
            # B. Apply & Update
            self.galvo_system.apply_voltage(vx, vy)
            self.galvo_system.update(physics_dt) # Pass the small dt
        
        # 4. VISUAL UPDATE (Only once per frame)
        self.update_visuals()

        # 5. PLOTS (Same as before)
        self.data_time = np.roll(self.data_time, -1)
        self.data_target_x = np.roll(self.data_target_x, -1)
        self.data_actual_x = np.roll(self.data_actual_x, -1)
        self.data_error_x = np.roll(self.data_error_x, -1)

        current_angle_x = self.galvo_system.state["Cuboid 1 (Red)"]['current_angle']
        
        self.data_time[-1] = self.time_elapsed
        self.data_target_x[-1] = req_theta_x 
        self.data_actual_x[-1] = current_angle_x
        self.data_error_x[-1] = req_theta_x - current_angle_x

        self.curve_target.setData(self.data_time, self.data_target_x)
        self.curve_actual.setData(self.data_time, self.data_actual_x)
        self.curve_error.setData(self.data_time, self.data_error_x)

    def update_visuals(self):
        # ... (Same as your previously working code) ...
        # Ensure this matches the physics.py logic I gave you earlier!
        red_current = self.galvo_system.state["Cuboid 1 (Red)"]['current_angle']
        blue_current = self.galvo_system.state["Cuboid 2 (Blue)"]['current_angle']
        
        b_pos = self.galvo_system.static_states["Cuboid 2 (Blue)"]['pos']
        b_rest = self.galvo_system.static_states["Cuboid 2 (Blue)"]['rest_rot_z']
        
        m_blue_phys = kinematics.get_model_matrix(b_pos, b_rest + blue_current, [0,0,1])
        m_blue_vis = kinematics.get_model_matrix([0,0,0], 90, [1,0,0]) 
        matrix_blue = m_blue_phys @ m_blue_vis
        self.objects["Cuboid 2 (Blue)"].setTransform(pg.Transform3D(*matrix_blue.flatten()))

        r_pos = self.galvo_system.static_states["Cuboid 1 (Red)"]['pos']
        r_rest = self.galvo_system.static_states["Cuboid 1 (Red)"]['rest_rot_x']
        
        matrix_red = kinematics.get_model_matrix(r_pos, r_rest + red_current, [1,0,0])
        self.objects["Cuboid 1 (Red)"].setTransform(pg.Transform3D(*matrix_red.flatten()))
        
        p1 = np.array(b_pos)
        dir_1 = physics.normalize(p1 - self.laser_source)
        
        n1 = kinematics.apply_transform_to_vector(matrix_blue, [0, 0, 1])
        n1 = physics.normalize(n1)
        r1 = physics.calculate_reflection(dir_1, n1)

        plane_point_red = np.array(r_pos)
        plane_normal_red = np.array([0, -1, 0]) 
        p2, t2 = physics.intersect_line_plane(p1, r1, plane_point_red, plane_normal_red)

        if t2 <= 0 or abs(p2[0]) > 10.0:
            self.laser_plot.setData(pos=np.array([self.laser_source, p1, p1 + r1*20]))
            return

        n2 = kinematics.apply_transform_to_vector(matrix_red, [0, 0, 1])
        n2 = physics.normalize(n2)
        r2 = physics.calculate_reflection(r1, n2)

        plane_point_screen = np.array([0, 0, 100])
        plane_normal_screen = np.array([0, 0, -1])
        p3, t3 = physics.intersect_line_plane(p2, r2, plane_point_screen, plane_normal_screen)

        if t3 <= 0: p3 = p2 + r2 * 20 
        
        self.laser_plot.setData(pos=np.array([self.laser_source, p1, p2, p3]))

        if self.simulation_active and t3 > 0:
            self.trace_points.append(p3)
            if len(self.trace_points) > 30: self.trace_points.pop(0)
            if len(self.trace_points) > 1:
                self.trace_plot.setData(pos=np.array(self.trace_points))