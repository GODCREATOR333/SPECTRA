import sys
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from pyqtgraph.opengl import GLMeshItem,GLTextItem,GLLinePlotItem
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import Qt


class MyView(gl.GLViewWidget):
    def __init__(self): #Construtor
        super().__init__() # Inheritance: Augment the actualy gl.GLViewWidget with my extra code without overwriting

        self.zoomFactor = 0.9  # smaller = stronger zoom
        self.currentDist = 200
        self.panStep = 5
        self.default_pos = self.cameraPosition()

        # Sets the "Look At" point to the world origin (0,0,0)
        self.opts['center'] = QtGui.QVector3D(0, 0, 0) 

        # Sets the Camera position using Spherical Coordinates
        # Distance: How far back the camera is
        # Elevation: Angle up from the ground
        # Azimuth: Angle around the Z-axis
        self.setCameraPosition(distance=self.currentDist, elevation=20, azimuth=-90)

        # Makes things look smaller when further away
        self.opts['projection'] = 'perspective' 
        self.setWindowTitle("Scanner Sim")
        
        
        #For key event triggering 
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        
    #Custom key binding to zoom-in and zoom-out and Pan
    def keyPressEvent(self, ev):
        key = ev.key()
        c = self.opts['center']

        # --- ZOOM ---
        if key == Qt.Key_I:
            self.currentDist *= self.zoomFactor
            self.setCameraPosition(distance=self.currentDist)
            return

        if key == Qt.Key_O:
            self.currentDist /= self.zoomFactor
            self.setCameraPosition(distance=self.currentDist)
            return

        # --- PAN (WASD) ---
        if key == Qt.Key_W:
            c.setY(c.y() - self.panStep)
            self.opts['center'] = c
            self.update()
            return

        if key == Qt.Key_S:
            c.setY(c.y() + self.panStep)
            self.opts['center'] = c
            self.update()
            return

        if key == Qt.Key_A:
            c.setX(c.x() + self.panStep)
            self.opts['center'] = c
            self.update()
            return

        if key == Qt.Key_D:
            c.setX(c.x() - self.panStep)
            self.opts['center'] = c
            self.update()
            return
        
        if key == Qt.Key_R:
            self.setCameraPosition(pos=self.default_pos)
            self.opts['center'] = self.default_center.copy()
            self.update()

        super().keyPressEvent(ev)


# ----- Helper Functions -----
def axis_line(start, end, color):

    # Creates a simple line to visualize X, Y, Z axes
    pts = np.array([start, end])
    return gl.GLLinePlotItem(pos=pts, color=color, width=3, antialias=True)

def create_cuboid(length, breadth, height):
    """Creates a MeshData object for a cuboid centered at the origin."""
    # 1. Calculate half-dimensions to center the cube at (0,0,0)
    l, b, h = length / 2., breadth / 2., height / 2.  #l=length/2.0 we need float 

    # 2. Define the 8 corners (Vertices) of the cube
    # This defines the "Body Frame" or "Local Frame" of the mirror.
    # No matter where the mirror moves in the world, these numbers NEVER change.
    verts = np.array([
        [-l, -b, -h], [ l, -b, -h], [ l,  b, -h], [-l,  b, -h],
        [-l, -b,  h], [ l, -b,  h], [ l,  b,  h], [-l,  b,  h]
    ])

    # 3. Define the triangles (Faces) connecting those vertices
    faces = np.array([
        [0, 1, 2], [0, 2, 3], [4, 5, 6], [4, 6, 7], [0, 1, 5], [0, 5, 4],
        [2, 3, 7], [2, 7, 6], [1, 2, 6], [1, 6, 5], [0, 3, 7], [0, 7, 4]
    ])


    # Returns a data structure containing the geometry
    return gl.MeshData(vertexes=verts, faces=faces)

def create_axis_ticks(axis, length, spacing=10.0, tick_size=2.0):
    # Draws small tick marks along the axis
    ticks = []
    positions = np.arange(spacing, length + spacing, spacing)
    for pos in positions:
        if axis == 'x': start, end = [pos, -tick_size / 2, 0], [pos, tick_size / 2, 0]
        elif axis == 'y': start, end = [-tick_size / 2, pos, 0], [tick_size / 2, pos, 0]
        elif axis == 'z': start, end = [0, -tick_size/2, pos], [0, tick_size/2, pos]
        
        # Color is white with some transparency
        ticks.append(GLLinePlotItem(pos=np.array([start, end]), color=(1,1,1,0.5), width=1))
    return ticks

# def create_axis_numbers(axis, length, spacing=10.0):
    # Draws the numbers (10, 20, 30...)
    numbers = []
    positions = np.arange(spacing, length + spacing, spacing)
    for pos in positions:
        text = f'{pos:.0f}'
        # Position the text slightly offset from the axis
        if axis == 'x': position = [pos, -5, 0]
        elif axis == 'y': position = [-5, pos, 0]
        elif axis == 'z': position = [-5, 0, pos]
        
        label = GLTextItem(text=text, color=(255, 255, 255, 255)) # White text
        label.setData(pos=np.array(position))
        label.setGLOptions('translucent') # Fix for Linux transparency issues
        numbers.append(label)
    return numbers



# --- Main Application Window ---
class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scanner Physics Engine")
        self.setGeometry(100, 100, 1200, 800)

        # --- Data and State ---

        # This dictionary acts like a "datasheet" for the physical parts.
        self.static_states = {
            "Cuboid 1 (Red)": {
                'pos': [0, 20, 0], # Where is the joint located on the board?
                'rest_rot_x': 45, # The "Home" position (Offset)
                'range': 15  # Physical Hard Stop (+/- 15 degrees)
            },
            "Cuboid 2 (Blue)": {
                'pos': [0, 0, 0],
                'rest_rot_z': 45,
                'range': 15
            }
        }
        
        self.objects = {}
        
        #This represents the Variables (the things changing every millisecond).
        self.animation_state = {
            "Cuboid 1 (Red)": {'current_angle': 45, # The actual value q(t)
                                'direction': 1, # Velocity vector (sign)
                                'step': 15}, # Velocity magnitude (speed)
                "Cuboid 2 (Blue)": {'current_angle': 45, 'direction': 1, 'step': 15}
        }
        
        # --- Timer for Animation ---
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._animate_step)

        # --- Layout & Widgets ---
        self.main_layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.main_layout)
        self.view = MyView()
        self.setup_scene()
        self.controls_widget = self._create_controls()
        
        self.main_layout.addWidget(self.controls_widget)
        self.main_layout.addWidget(self.view, 1)

        # --- Finalize ---
        self.update_transforms()

    def setup_scene(self):
        """Adds the axes and cuboids to the 3D view."""
        axis_length = 60.0
        tick_spacing = 10.0 # Changed to 10mm so numbers aren't too crowded
        
        # 1. Main Axis Lines (RGB)
        self.view.addItem(axis_line([0, 0, 0], [axis_length, 0, 0], (1, 0, 0, 1))) # X - Red
        self.view.addItem(axis_line([0, 0, 0], [0, axis_length, 0], (0, 1, 0, 1))) # Y - Green
        self.view.addItem(axis_line([0, 0, 0], [0, 0, axis_length], (0, 0, 1, 1))) # Z - Blue

        # 2. Add Ticks (White lines)
        all_ticks = (create_axis_ticks('x', axis_length, tick_spacing) + 
                     create_axis_ticks('y', axis_length, tick_spacing) + 
                     create_axis_ticks('z', axis_length, tick_spacing))
        for tick in all_ticks: 
            self.view.addItem(tick)

        # 3. Add Numbers (10, 20, 30...)  <-- THIS BLOCK WAS MISSING
        # all_numbers = (create_axis_numbers('x', axis_length, tick_spacing) + 
        #                create_axis_numbers('y', axis_length, tick_spacing) + 
        #                create_axis_numbers('z', axis_length, tick_spacing))
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

        mesh1 = create_cuboid(length=20, breadth=10, height=1)
        cuboid1 = GLMeshItem(meshdata=mesh1, smooth=False, drawFaces=True,
                             drawEdges=True, edgeColor=(1, 1, 1, 1), color=(1, 0, 0, 0.7))
        self.objects["Cuboid 1 (Red)"] = cuboid1
        self.view.addItem(cuboid1)

        mesh2 = create_cuboid(length=10, breadth=20, height=1)
        cuboid2 = GLMeshItem(meshdata=mesh2, smooth=False, drawFaces=True,
                             drawEdges=True, edgeColor=(1, 1, 1, 1), color=(0, 0, 1, 0.7))
        self.objects["Cuboid 2 (Blue)"] = cuboid2
        self.view.addItem(cuboid2)

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
        self.animation_button = QtWidgets.QPushButton("Start Animation")
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
            self.timer.start(50) # Update every 50 ms
            self.animation_button.setText("Stop Animation")

    def _animate_step(self):
        """Calculates the new angle for both objects in each animation frame."""
        # Animate Red Cuboid
        red_static = self.static_states["Cuboid 1 (Red)"]
        red_anim = self.animation_state["Cuboid 1 (Red)"]

        # Integration: New_Pos = Old_Pos + Velocity * dt
        # Collision Detection / Hard Stops
        # Checks if current_angle exceeds the limits defined in static_states
        red_anim['current_angle'] += red_anim['step'] * red_anim['direction']
        if not (red_static['rest_rot_x'] - red_static['range'] <= red_anim['current_angle'] <= red_static['rest_rot_x'] + red_static['range']):
            red_anim['direction'] *= -1

        # Animate Blue Cuboid
        blue_static = self.static_states["Cuboid 2 (Blue)"]
        blue_anim = self.animation_state["Cuboid 2 (Blue)"]
        blue_anim['current_angle'] += blue_anim['step'] * blue_anim['direction']
        if not (blue_static['rest_rot_z'] - blue_static['range'] <= blue_anim['current_angle'] <= blue_static['rest_rot_z'] + blue_static['range']):
            blue_anim['direction'] *= -1
            
        self.update_transforms()

    def update_transforms(self):
        """Applies the current transformation to both objects and updates labels."""
        # --- Get current angles ---
        red_rot_x = self.animation_state["Cuboid 1 (Red)"]['current_angle']
        blue_rot_z = self.animation_state["Cuboid 2 (Blue)"]['current_angle']

        # Update label text ---
        self.red_angle_label.setText(f"Red (X-Rot): {red_rot_x:.1f}°")
        self.blue_angle_label.setText(f"Blue (Z-Rot): {blue_rot_z:.1f}°")

        # --- Update Red Cuboid 3D Object ---
        red_obj = self.objects["Cuboid 1 (Red)"]

        # 1. Get the Translation Vector from the static dictionary
        # red_pos is [0, 20, 0]
        red_pos = self.static_states["Cuboid 1 (Red)"]['pos']
        
        # 2. Create an Identity Matrix (4x4)
        tr_red = pg.Transform3D()
        
        # 3. Apply Translation (Displacement)
        # Matrix becomes: [ 1 0 0 0 ]
        #                 [ 0 1 0 20]  <-- The 20 moves it up Y-axis
        #                 ...
        
        tr_red.translate(*red_pos)
        
        # 4. Apply Rotation (The Dynamic Part)
        # red_rot_x is the animating angle (e.g., 45.5 degrees)
        # (1, 0, 0) is the Axis of Rotation (X-axis)
        tr_red.rotate(red_rot_x, 1, 0, 0)

        # 5. Send Matrix to GPU
        red_obj.setTransform(tr_red)


        # """The Physics Logic:
        # Notice the order: Translate first, then Rotate.
        # We move the generic cube from
        # (0,0,0)(0,0,0)
        # to its mounting point
        # (0,20,0)(0,20,0)
        # Now the coordinate system is sitting at
        # (0,20,0)(0,20,0)
        # We rotate it around that new point.
        # If you swapped these lines (Rotate then Translate), the cube would rotate around the World Origin
        # (0,0,0)(0,0,0)
        # down below, swinging in a huge arc."""

        # --- Update Blue Cuboid 3D Object ---
        blue_obj = self.objects["Cuboid 2 (Blue)"]
        blue_pos = self.static_states["Cuboid 2 (Blue)"]['pos']
        tr_blue = pg.Transform3D()
        tr_blue.translate(*blue_pos)
        tr_blue.rotate(blue_rot_z, 0, 0, 1)
        tr_blue.rotate(90, 0, 1, 0)
        tr_blue.rotate(90, 0, 0, 1)
        blue_obj.setTransform(tr_blue)


        # # --- LASER PHYSICS ---
        # hit_point = np.array(red_pos) 
        # incident = hit_point - self.laser_source
        # incident_dir = incident / np.linalg.norm(incident)

        # local_normal = np.array([0, 0, 1, 1]) 
        # matrix_4x4 = tr_red.matrix()
        # world_normal_4d = matrix_4x4 @ local_normal 
        # world_normal = world_normal_4d[:3] 
        # world_normal = world_normal / np.linalg.norm(world_normal)

        # dot_prod = np.dot(incident_dir, world_normal)
        # reflection_dir = incident_dir - 2 * dot_prod * world_normal
        # reflection_end = hit_point + (reflection_dir * 100)
        
        # pts = np.array([self.laser_source, hit_point, reflection_end])
        # self.laser_plot.setData(pos=pts)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())