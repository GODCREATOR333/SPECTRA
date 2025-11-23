# The MainWindow Class (The loop that connects Core + Vis)

import sys
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from pyqtgraph.opengl import GLMeshItem, GLTextItem, GLLinePlotItem
from PyQt5 import QtGui, QtCore, QtWidgets

# --- IMPORTS FROM YOUR NEW MODULES ---
from Scanner_Sim_py.visualization.viewer import MyView
from Scanner_Sim_py.visualization import geometry
from Scanner_Sim_py.core import kinematics
from Scanner_Sim_py.core import physics

# --- Main Application Window ---
class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scanner Physics Engine")
        self.setGeometry(100, 100, 1200, 800)

        # --- Data and State ---

        # This dictionary acts like a "datasheet" for the physical parts.
        # --- A. DATASHEET (Static Configuration) ---
        self.static_states = {
            "Cuboid 1 (Red)": {
                'pos': [0, 20, 0], # Where is the joint located on the board?
                'rest_rot_x': 45, # The "Home" position (Offset)
                'range': 5  # Physical Hard Stop (+/- 15 degrees)
            },

            ## BLUE MIRROR (First Hit): Located at Origin (0,0,0)
            "Cuboid 2 (Blue)": {
                'pos': [0, 0, 0],
                'rest_rot_z': -45,
                'range': 5
            }
        }
        
        self.objects = {}
        
        # --- B. SIMULATION STATE (Dynamic Variables) ---
        #This represents the Variables (the things changing every millisecond).
        self.animation_state = {
            "Cuboid 1 (Red)": {'current_angle': 0, # The actual value q(t)
                                'direction': 1, # Velocity vector (sign)
                                'step': 1}, # Velocity magnitude (speed)
                "Cuboid 2 (Blue)": {'current_angle': 0,
                                    'direction': 1,
                                    'step': 1}
        }
        

        # --- C. SETUP UI ---
        # --- Timer for Animation ---
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._animate_step)

        # --- Layout & Widgets ---
        self.main_layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.main_layout)
        self.view = MyView()
        self.setup_scene() # <--- CALLS THE FUNCTION BELOW
        self.controls_widget = self._create_controls()
        
        self.main_layout.addWidget(self.controls_widget)
        self.main_layout.addWidget(self.view, 1)

        # --- Finalize ---
        self.update_transforms()

    def setup_scene(self):
        """Initializes the 3D world: Grids, Frames, Mirrors, Laser."""

        # --- 0. Background Grids (The "World Frame") ---

        # X-Plane Grid
        gx = gl.GLGridItem()
        gx.setSize(x=100, y=100) # Adjust Size
        gx.setSpacing(x=10, y=10)
        gx.rotate(90, 0, 1, 0)
        gx.translate(-50, 0, 0) # Adjust Position
        self.view.addItem(gx)

        # Y-Plane Grid
        gy = gl.GLGridItem()
        gy.setSize(x=100, y=100)
        gy.setSpacing(x=10, y=10)
        gy.rotate(90, 1, 0, 0)
        gy.translate(0, -50, 0)
        self.view.addItem(gy)

        # Z-Plane Grid (Floor)
        # gz = gl.GLGridItem()
        # gz.setSize(x=100, y=100)
        # gz.setSpacing(x=10, y=10)
        # gz.translate(0, 0, -50)
        # self.view.addItem(gz)

        """Adds the axes and cuboids to the 3D view."""
        axis_length = 60.0
        tick_spacing = 10.0 # Changed to 10mm so numbers aren't too crowded
        
        # 1. Scanner Axis Lines (RGB)
        # UPDATED: Calling geometry.axis_line
        self.view.addItem(geometry.axis_line([0, 0, 0], [axis_length, 0, 0], (1, 0, 0, 1))) # X - Red
        self.view.addItem(geometry.axis_line([0, 0, 0], [0, axis_length, 0], (0, 1, 0, 1))) # Y - Green
        self.view.addItem(geometry.axis_line([0, 0, 0], [0, 0, axis_length], (0, 0, 1, 1))) # Z - Blue

        # 2. Add Ticks (White lines)
        # UPDATED: Calling geometry.create_axis_ticks
        all_ticks = (geometry.create_axis_ticks('x', axis_length, tick_spacing) + 
                     geometry.create_axis_ticks('y', axis_length, tick_spacing) + 
                     geometry.create_axis_ticks('z', axis_length, tick_spacing))
        for tick in all_ticks: 
            self.view.addItem(tick)

        # 3. Add Numbers (10, 20, 30...)  <-- THIS BLOCK WAS MISSING
        # all_numbers = (geometry.create_axis_numbers('x', axis_length, tick_spacing) + 
        #                geometry.create_axis_numbers('y', axis_length, tick_spacing) + 
        #                geometry.create_axis_numbers('z', axis_length, tick_spacing))
        # for number in all_numbers: 
        #     self.view.addItem(number)

        # 4. Add Main Labels (X, Y, Z) at the tips
        # CHANGE HERE: Use 255 for Red/Green/Blue
        x_label = GLTextItem(text='X', color=(255, 0, 0, 255)) 
        x_label.setData(pos=np.array([axis_length + 2, 0, 0]))
        x_label.setGLOptions('translucent')
        self.view.addItem(x_label)
        
        y_label = GLTextItem(text='Y', color=(0, 255, 0, 255))
        y_label.setData(pos=np.array([0, axis_length + 2, 0]))
        y_label.setGLOptions('translucent')
        self.view.addItem(y_label)
        
        z_label = GLTextItem(text='Z', color=(0, 0, 255, 255))
        z_label.setData(pos=np.array([0, 0, axis_length + 2]))
        z_label.setGLOptions('translucent')
        self.view.addItem(z_label)

        # UPDATED: Calling geometry.create_cuboid
        mesh1 = geometry.create_cuboid(length=20, breadth=10, height=1)
        cuboid1 = GLMeshItem(meshdata=mesh1, smooth=False, drawFaces=True,
                             drawEdges=True, edgeColor=(1, 1, 1, 1), color=(1, 0, 0, 0.7))
        self.objects["Cuboid 1 (Red)"] = cuboid1
        self.view.addItem(cuboid1)

        mesh2 = geometry.create_cuboid(length=10, breadth=20, height=1)
        cuboid2 = GLMeshItem(meshdata=mesh2, smooth=False, drawFaces=True,
                             drawEdges=True, edgeColor=(1, 1, 1, 1), color=(0, 0, 1, 0.7))
        self.objects["Cuboid 2 (Blue)"] = cuboid2
        self.view.addItem(cuboid2)


        # Laser Line 
        self.laser_plot = GLLinePlotItem(pos=np.array([[0,0,0], [0,0,0]]), color=(1, 0, 1, 1), width=3, antialias=True)
        self.view.addItem(self.laser_plot)

        # 2. Source (Shooting from Left -X towards Origin)
        self.laser_source = np.array([50, 0, 0])

        # 3. The Screen at Z=50 (A Green Grid)
        self.screen_grid = gl.GLGridItem()
        self.screen_grid.setSize(x=70, y=70)
        self.screen_grid.setSpacing(x=3, y=3)
        # Rotate to face the beam (Standard grid is on XY plane, we assume screen is flat on XY at Z=50)
        self.screen_grid.translate(0, 20, 50) 
        self.view.addItem(self.screen_grid)

        # --- NEW: TRACE PLOT ---
        # A green line that remembers where the laser hit
        self.trace_plot = GLLinePlotItem(pos=np.array([[0,0,0]]), color=(0, 1, 0, 1), width=2, antialias=True)
        self.view.addItem(self.trace_plot)
        
        # List to store history
        self.trace_points = []

    def _create_controls(self):
        """Creates the simplified control panel with an animation button and angle displays."""
        control_container = QtWidgets.QWidget()
        control_container.setMaximumWidth(250)
        control_layout = QtWidgets.QVBoxLayout()
        control_container.setLayout(control_layout)

        # --- CHANGE 1: ADD LABELS FOR ANGLE DISPLAY ---
        title_font = QtGui.QFont()
        title_font.setBold(True)
        title_label = QtWidgets.QLabel("Real-time Angles")
        title_label.setFont(title_font)
        
        self.red_angle_label = QtWidgets.QLabel("Red (X-Rot): 0.0°")
        self.blue_angle_label = QtWidgets.QLabel("Blue (Z-Rot): 0.0°")
        
        control_layout.addWidget(title_label)
        control_layout.addWidget(self.red_angle_label)
        control_layout.addWidget(self.blue_angle_label)
        control_layout.addSpacing(20)

        # Animation Button
        self.animation_button = QtWidgets.QPushButton("Start Plotting")
        self.animation_button.clicked.connect(self._toggle_animation)
        control_layout.addWidget(self.animation_button)
        
        control_layout.addStretch()
        return control_container

    def _toggle_animation(self):
        """Starts or stops the animation timer."""
        if self.timer.isActive():
            self.timer.stop()
            self.animation_button.setText("Start Animation")
        else:
            self.timer.start(10) # Update every 50 ms
            self.animation_button.setText("Stop Animation")

    def _animate_step(self):
        """Physics Time Step."""
        # Update Red Mirror
        r_st = self.static_states["Cuboid 1 (Red)"]
        r_an = self.animation_state["Cuboid 1 (Red)"]
        
        r_an['current_angle'] += r_an['step'] * r_an['direction']
        
        # If we swing past +/- 15 degrees, flip direction
        if abs(r_an['current_angle']) >= r_st['range']:
            r_an['direction'] *= -1

        # Update Blue Mirror
        b_st = self.static_states["Cuboid 2 (Blue)"]
        b_an = self.animation_state["Cuboid 2 (Blue)"]
        
        b_an['current_angle'] += b_an['step'] * b_an['direction']
        
        if abs(b_an['current_angle']) >= b_st['range']:
            b_an['direction'] *= -1
            
        self.update_transforms()

    def update_transforms(self):
        # 1. Get Angles
        red_current = self.animation_state["Cuboid 1 (Red)"]['current_angle']
        blue_current = self.animation_state["Cuboid 2 (Blue)"]['current_angle']
        
        self.red_angle_label.setText(f"Red: {red_current:.1f}°")
        self.blue_angle_label.setText(f"Blue: {blue_current:.1f}°")

        # =========================================================
        # 2. UPDATE BLUE MIRROR (Origin)
        # =========================================================
        b_pos = self.static_states["Cuboid 2 (Blue)"]['pos']
        b_rest = self.static_states["Cuboid 2 (Blue)"]['rest_rot_z']
        
        # Physics: Translate -> Rotate Z (Rest + Current)
        m_blue_phys = kinematics.get_model_matrix(b_pos, b_rest + blue_current, [0,0,1])
        # Visual: Rotate 90 X to make the plate stand up
        m_blue_vis = kinematics.get_model_matrix([0,0,0], 90, [1,0,0])
        
        matrix_blue = m_blue_phys @ m_blue_vis
        self.objects["Cuboid 2 (Blue)"].setTransform(pg.Transform3D(*matrix_blue.flatten()))

        # =========================================================
        # 3. UPDATE RED MIRROR (Y=20)
        # =========================================================
        r_pos = self.static_states["Cuboid 1 (Red)"]['pos']
        r_rest = self.static_states["Cuboid 1 (Red)"]['rest_rot_x']
        
        # Physics: Translate -> Rotate X (Rest + Current)
        # Red mirror naturally tilts correctly with X rotation
        matrix_red = kinematics.get_model_matrix(r_pos, r_rest + red_current, [1,0,0])
        
        self.objects["Cuboid 1 (Red)"].setTransform(pg.Transform3D(*matrix_red.flatten()))

        # =========================================================
        # 4. RAY TRACING
        # =========================================================
        
        # --- Path 1: Source -> Blue ---
        p1 = np.array(b_pos) 
        dir_1 = physics.normalize(p1 - self.laser_source)
        
        # Normal 1 (Blue)
        # Transform local Z [0,0,1] using the Full Blue Matrix
        n1 = kinematics.apply_transform_to_vector(matrix_blue, [0, 0, 1])
        n1 = physics.normalize(n1)
        r1 = physics.calculate_reflection(dir_1, n1)

        # --- Path 2: Blue -> Red ---
        plane_point_red = np.array(r_pos)
        # Red mirror is a wall facing -Y
        plane_normal_red = np.array([0, -1, 0]) 
        
        p2, t2 = physics.intersect_line_plane(p1, r1, plane_point_red, plane_normal_red)
        
        # Miss Checks
        if t2 <= 0: # Beam went backward or parallel
             self.laser_plot.setData(pos=np.array([self.laser_source, p1, p1 + r1*20]))
             return
        
        if abs(p2[0]) > 10.0: # Width Check (Mirror Size 20)
            self.laser_plot.setData(pos=np.array([self.laser_source, p1, p2, p2 + r1*20]))
            return

        # --- Path 3: Red -> Screen ---
        # Normal 2 (Red)
        n2 = kinematics.apply_transform_to_vector(matrix_red, [0, 0, 1])
        n2 = physics.normalize(n2)
        r2 = physics.calculate_reflection(r1, n2)
        
        # Screen Intersection (Z=50)
        plane_point_screen = np.array([0, 0, 50])
        plane_normal_screen = np.array([0, 0, -1])
        
        p3, t3 = physics.intersect_line_plane(p2, r2, plane_point_screen, plane_normal_screen)

        if t3 <= 0: p3 = p2 + r2 * 20
        
        # --- DRAW LASER ---
        self.laser_plot.setData(pos=np.array([self.laser_source, p1, p2, p3]))

        # --- NEW: DRAW TRACE ON SCREEN ---
        # Only add point if we actually hit the screen area (Z approx 50)
        if t3 > 0:
            # Store the point
            self.trace_points.append(p3)
            
            # Optimization: Keep only last 500 points so memory doesn't explode
            if len(self.trace_points) > 500:
                self.trace_points.pop(0)
            
            # Update the visual line
            if len(self.trace_points) > 1:
                pts_array = np.array(self.trace_points)
                self.trace_plot.setData(pos=pts_array)