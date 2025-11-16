import sys
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from pyqtgraph.opengl import GLMeshItem
from PyQt5 import QtGui, QtCore, QtWidgets

# Custom GLViewWidget with a fixed, standard "XY Plane" view
class MyView(gl.GLViewWidget):
    def __init__(self):
        super().__init__()
        self.opts['center'] = QtGui.QVector3D(0, 0, 0)
        self.setCameraPosition(distance=200, elevation=20, azimuth=-90)
        self.opts['projection'] = 'perspective'
        self.setWindowTitle("Coordinate Axes - Automated Animation")

# ----- Helper Functions -----
def axis_line(start, end, color):
    pts = np.array([start, end])
    return gl.GLLinePlotItem(pos=pts, color=color, width=3, antialias=True)

def create_cuboid(length, breadth, height):
    """Creates a MeshData object for a cuboid centered at the origin."""
    l, b, h = length / 2., breadth / 2., height / 2.
    verts = np.array([
        [-l, -b, -h], [ l, -b, -h], [ l,  b, -h], [-l,  b, -h],
        [-l, -b,  h], [ l, -b,  h], [ l,  b,  h], [-l,  b,  h]
    ])
    faces = np.array([
        [0, 1, 2], [0, 2, 3], [4, 5, 6], [4, 6, 7], [0, 1, 5], [0, 5, 4],
        [2, 3, 7], [2, 7, 6], [1, 2, 6], [1, 6, 5], [0, 3, 7], [0, 7, 4]
    ])
    return gl.MeshData(vertexes=verts, faces=faces)


# --- Main Application Window ---
class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQtGraph Animation")
        self.setGeometry(100, 100, 1200, 800)

        # --- Data and State ---
        self.static_states = {
            "Cuboid 1 (Red)": {
                'pos': [0, 20, 0],
                'rest_rot_x': 45,
                'range': 15
            },
            "Cuboid 2 (Blue)": {
                'pos': [0, 0, 0],
                'rest_rot_z': 45,
                'range': 15
            }
        }
        
        self.objects = {}
        
        self.animation_state = {
            "Cuboid 1 (Red)": {'current_angle': 45, 'direction': 1, 'step': 0.5},
            "Cuboid 2 (Blue)": {'current_angle': 45, 'direction': 1, 'step': 0.5}
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
        axis_length = 50.0
        self.view.addItem(axis_line([0, 0, 0], [axis_length, 0, 0], (1, 0, 0, 1)))
        self.view.addItem(axis_line([0, 0, 0], [0, axis_length, 0], (0, 1, 0, 1)))
        self.view.addItem(axis_line([0, 0, 0], [0, 0, axis_length], (0, 0, 1, 1)))

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

        # --- CHANGE 2: UPDATE LABEL TEXT ---
        self.red_angle_label.setText(f"Red (X-Rot): {red_rot_x:.1f}°")
        self.blue_angle_label.setText(f"Blue (Z-Rot): {blue_rot_z:.1f}°")

        # --- Update Red Cuboid 3D Object ---
        red_obj = self.objects["Cuboid 1 (Red)"]
        red_pos = self.static_states["Cuboid 1 (Red)"]['pos']
        tr_red = pg.Transform3D()
        tr_red.translate(*red_pos)
        tr_red.rotate(red_rot_x, 1, 0, 0)
        red_obj.setTransform(tr_red)

        # --- Update Blue Cuboid 3D Object ---
        blue_obj = self.objects["Cuboid 2 (Blue)"]
        blue_pos = self.static_states["Cuboid 2 (Blue)"]['pos']
        tr_blue = pg.Transform3D()
        tr_blue.translate(*blue_pos)
        tr_blue.rotate(blue_rot_z, 0, 0, 1)
        tr_blue.rotate(90, 0, 1, 0)
        tr_blue.rotate(90, 0, 0, 1)
        blue_obj.setTransform(tr_blue)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())