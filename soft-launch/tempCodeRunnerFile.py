import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import time
from pyqtgraph.opengl import GLLinePlotItem, GLTextItem, GLMeshItem, GLGridItem
from PyQt5.QtGui import QVector3D, QMatrix4x4
from PyQt5 import QtWidgets, QtGui, QtCore

# ===================================================================
#  STYLING (QSS - Similar to CSS)
# ===================================================================
DARK_STYLESHEET = """
QMainWindow {
    background-color: #2c313c;
}
QToolBar {
    background-color: #353b48;
    border: none;
    padding: 2px;
    spacing: 3px;
}
QToolBar::separator {
    background-color: #4a5160;
    width: 1px;
    margin-left: 3px;
    margin-right: 3px;
}
QToolButton {
    color: #eff0f1;
    background-color: #353b48;
    border: 1px solid #4a5160;
    padding: 5px;
    margin: 1px;
    min-width: 50px;
}
QToolButton:hover {
    background-color: #4a5160;
}
QToolButton:pressed {
    background-color: #2c313c;
}
QStatusBar {
    color: #eff0f1;
}
QLabel {
    color: #eff0f1;
}
QComboBox {
    color: #eff0f1;
    background-color: #353b48;
    border: 1px solid #4a5160;
    padding: 3px;
}
QComboBox::drop-down {
    border: none;
}
"""

# ===================================================================
#  3D VIEW WIDGET (The "Engine")
# ===================================================================
class MyView(gl.GLViewWidget):
    def __init__(self, fps_label):
        super().__init__()
        self.fps_label = fps_label
        self.frame_count, self.start_time = 0, time.time()
        
        self.initial_opts = {'center': QtGui.QVector3D(0, 0, 25), 'distance': 200, 'elevation': 20, 'azimuth': -45}
        self.set_camera_view(self.initial_opts)
        
        self.opts['projection'] = 'perspective'
        self.number_labels = []

    def set_camera_view(self, view_opts):
        self.opts.update(view_opts)
        self.update()

    def paintGL(self, *args, **kwargs):
        super().paintGL(*args, **kwargs)
        self.frame_count += 1
        now = time.time()
        if (now - self.start_time) >= 0.5:
            fps = self.frame_count / (now - self.start_time)
            self.fps_label.setText(f"FPS: {fps:.2f}")
            self.start_time, self.frame_count = now, 0
    
    def mousePressEvent(self, ev):
        self.mousePos = ev.pos()

    def mouseMoveEvent(self, ev):
        if ev.buttons() == QtCore.Qt.LeftButton:
            diff = ev.pos() - self.mousePos
            self.mousePos = ev.pos()
            angle_y, angle_x = -diff.x() * 0.3, diff.y() * 0.3
            cam_vec = self.cameraPosition() - self.opts['center']
            forward_vec = (self.opts['center'] - self.cameraPosition()).normalized()
            right_vec = QVector3D.crossProduct(forward_vec, QVector3D(0, 1, 0)).normalized()
            transform = QMatrix4x4()
            transform.rotate(angle_y, 0, 1, 0)
            transform.rotate(angle_x, right_vec)
            new_cam_vec = transform.map(cam_vec)
            distance = new_cam_vec.length()
            if distance == 0: return
            self.opts['azimuth'] = np.degrees(np.arctan2(new_cam_vec.y(), new_cam_vec.x()))
            self.opts['elevation'] = np.degrees(np.arcsin(new_cam_vec.z() / distance))
            self.opts['distance'] = distance
            self.update()
        else: super().mouseMoveEvent(ev)
        
    def set_number_labels(self, labels):
        self.number_labels = labels
        self.update_labels_visibility()

    def update_labels_visibility(self):
        show_labels = self.opts['distance'] < 150 # Custom threshold
        for label in self.number_labels:
            label.setVisible(show_labels)

# ===================================================================
#  MAIN WINDOW (Feature Complete with Advanced Controls)
# ===================================================================
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Galvo Local Frame Kinematics Viewer")
        self.resize(1000, 700)

        self.fps_label = QtWidgets.QLabel("FPS: --")
        self.main_view = MyView(self.fps_label)
        self.setCentralWidget(self.main_view)

        # --- Comprehensive camera view targets ---
        iso_dist = 200
        iso_center = QVector3D(0,0,25)
        self.view_targets = {
            'TOP': {'azimuth': -90, 'elevation': 90, 'center': iso_center, 'distance': iso_dist},
            'BOTTOM': {'azimuth': -90, 'elevation': -90, 'center': iso_center, 'distance': iso_dist},
            'FRONT': {'azimuth': -90, 'elevation': 0, 'center': iso_center, 'distance': iso_dist},
            'BACK': {'azimuth': 90, 'elevation': 0, 'center': iso_center, 'distance': iso_dist},
            'RIGHT': {'azimuth': 0, 'elevation': 0, 'center': iso_center, 'distance': iso_dist},
            'LEFT': {'azimuth': 180, 'elevation': 0, 'center': iso_center, 'distance': iso_dist},
            'Top ISO 1': {'azimuth': 45, 'elevation': 35.264, 'center': iso_center, 'distance': iso_dist},
            'Top ISO 2': {'azimuth': 135, 'elevation': 35.264, 'center': iso_center, 'distance': iso_dist},
            'Top ISO 3': {'azimuth': -45, 'elevation': 30, 'center': iso_center, 'distance': iso_dist},
            'Top ISO 4': {'azimuth': -135, 'elevation': 30, 'center': iso_center, 'distance': iso_dist},
            'Bot ISO 1': {'azimuth': 45, 'elevation': -35.264, 'center': iso_center, 'distance': iso_dist},
            'Bot ISO 2': {'azimuth': 135, 'elevation': -35.264, 'center': iso_center, 'distance': iso_dist},
            'Bot ISO 3': {'azimuth': -45, 'elevation': -30, 'center': iso_center, 'distance': iso_dist},
            'Bot ISO 4': {'azimuth': -135, 'elevation': -30, 'center': iso_center, 'distance': iso_dist},
            'Di 1': {'azimuth': 25, 'elevation': 25, 'center': iso_center, 'distance': iso_dist},
            'Di 2': {'azimuth': 155, 'elevation': 25, 'center': iso_center, 'distance': iso_dist},
            'Tri 1': {'azimuth': 50, 'elevation': 20, 'center': iso_center, 'distance': iso_dist},
            'Tri 2': {'azimuth': 120, 'elevation': 40, 'center': iso_center, 'distance': iso_dist},
        }
        
        self.look_at_targets = {
            "Default": iso_center,
            "Origin (Galvo Center)": QVector3D(0, 0, 0),
            "Laser End Point": QVector3D(0, 0, 50),
        }

        self._create_actions()
        self._create_toolbars()
        self._create_statusbar()

    def _create_actions(self):
        self.actions = {}
        for view_name in self.view_targets.keys():
            short_name = view_name.replace("Top ", "").replace("Bot ", "").replace("ISO", " I")
            action = QtWidgets.QAction(short_name, self)
            action.triggered.connect(lambda _, name=view_name: self.main_view.set_camera_view(self.view_targets[name]))
            self.actions[view_name] = action

        self.reset_view_action = QtWidgets.QAction("Reset", self)
        self.reset_view_action.setShortcut(QtGui.QKeySequence("Ctrl+R"))
        self.reset_view_action.triggered.connect(lambda: self.main_view.set_camera_view(self.main_view.initial_opts))

        self.projection_action = QtWidgets.QAction("Perspective", self)
        self.projection_action.setCheckable(True)
        self.projection_action.setChecked(self.main_view.opts['projection'] == 'perspective')
        self.projection_action.triggered.connect(self._toggle_projection)

    def _toggle_projection(self):
        if self.projection_action.isChecked():
            self.main_view.opts['projection'] = 'perspective'
            self.projection_action.setText("Perspective")
        else:
            self.main_view.opts['projection'] = 'ortho'
            self.projection_action.setText("Orthographic")
        self.main_view.update()

    def _create_toolbars(self):
        ortho_toolbar = self.addToolBar("Orthographic Views")
        ortho_toolbar.addAction(self.actions['TOP']); ortho_toolbar.addAction(self.actions['BOTTOM']); ortho_toolbar.addSeparator()
        ortho_toolbar.addAction(self.actions['FRONT']); ortho_toolbar.addAction(self.actions['BACK']); ortho_toolbar.addSeparator()
        ortho_toolbar.addAction(self.actions['LEFT']); ortho_toolbar.addAction(self.actions['RIGHT'])
        self.addToolBarBreak()
        top_iso_toolbar = self.addToolBar("Top Isometric Views")
        top_iso_toolbar.addAction(self.actions['Top ISO 1']); top_iso_toolbar.addAction(self.actions['Top ISO 2'])
        top_iso_toolbar.addAction(self.actions['Top ISO 3']); top_iso_toolbar.addAction(self.actions['Top ISO 4'])
        bot_iso_toolbar = self.addToolBar("Bottom Isometric Views")
        bot_iso_toolbar.addAction(self.actions['Bot ISO 1']); bot_iso_toolbar.addAction(self.actions['Bot ISO 2'])
        bot_iso_toolbar.addAction(self.actions['Bot ISO 3']); bot_iso_toolbar.addAction(self.actions['Bot ISO 4'])
        adv_toolbar = self.addToolBar("Advanced Axonometric Views")
        adv_toolbar.addAction(self.actions['Di 1']); adv_toolbar.addAction(self.actions['Di 2']); adv_toolbar.addSeparator()
        adv_toolbar.addAction(self.actions['Tri 1']); adv_toolbar.addAction(self.actions['Tri 2'])
        self.addToolBarBreak()
        control_toolbar = self.addToolBar("Controls")
        control_toolbar.addWidget(QtWidgets.QLabel("  Look At: "))
        self.look_at_combo = QtWidgets.QComboBox()
        self.look_at_combo.addItems(self.look_at_targets.keys())
        self.look_at_combo.activated[str].connect(self._set_look_at_target)
        control_toolbar.addWidget(self.look_at_combo)
        control_toolbar.addSeparator()
        control_toolbar.addAction(self.projection_action)
        control_toolbar.addSeparator()
        control_toolbar.addAction(self.reset_view_action)

    def _set_look_at_target(self, target_name):
        target_center = self.look_at_targets.get(target_name)
        if target_center:
            self.main_view.opts['center'] = target_center
            self.main_view.update()

    def _create_statusbar(self):
        self.setStatusBar(QtWidgets.QStatusBar(self))
        self.statusBar().addPermanentWidget(self.fps_label)

# ===================================================================
#  HELPER FUNCTIONS
# ===================================================================
def axis_line(start, end, color):
    return GLLinePlotItem(pos=np.array([start, end]), color=color, width=3, antialias=True)

def create_axis_ticks(axis, length, spacing=1.0, tick_size=0.2):
    ticks = []
    positions = np.arange(-length, length + spacing, spacing)
    for pos in positions:
        if abs(pos) < 1e-5: continue
        if axis == 'x': start, end = [pos, -tick_size / 2, 0], [pos, tick_size / 2, 0]
        elif axis == 'y': start, end = [-tick_size / 2, pos, 0], [tick_size / 2, pos, 0]
        elif axis == 'z': start, end = [0, -tick_size/2, pos], [0, tick_size/2, pos]
        ticks.append(GLLinePlotItem(pos=np.array([start, end]), color=(1,1,1,0.5), width=1))
    return ticks

def create_axis_numbers(axis, length, spacing=1.0):
    numbers = []
    positions = np.arange(-length, length + spacing, spacing)
    for pos in positions:
        if abs(pos) < 1e-5: continue
        text = f'{pos:.0f}'
        if axis == 'x': position = [pos, 0.4, 0]
        elif axis == 'y': position = [0.4, pos, 0]
        elif axis == 'z': position = [0, 0.4, pos]
        label = GLTextItem(text=text, color=(255, 255, 255, 255))
        label.setData(pos=np.array(position))
        numbers.append(label)
    return numbers

# ===================================================================
#  MAIN EXECUTION BLOCK
# ===================================================================
if __name__ == '__main__':
    app = pg.mkQApp("3D Viewer")
    app.setStyleSheet(DARK_STYLESHEET)
    
    window = MainWindow()
    window.show()

    main_view = window.main_view
    axis_length = 50.0
    tick_spacing = 10.0
    
    # --- Add Coordinate System Axes ---
    main_view.addItem(axis_line([-axis_length, 0, 0], [axis_length, 0, 0], (1, 0, 0, 1))) # X
    main_view.addItem(axis_line([0, -axis_length, 0], [0, axis_length, 0], (0, 1, 0, 1))) # Y
    main_view.addItem(axis_line([0, 0, -axis_length], [0, 0, axis_length], (0, 0, 1, 1))) # Z
    x_label = GLTextItem(text='X+', color='w'); x_label.setData(pos=np.array([axis_length, 0, 0]))
    y_label = GLTextItem(text='Y+', color='w'); y_label.setData(pos=np.array([0, axis_length, 0]))
    z_label = GLTextItem(text='Z+', color='w'); z_label.setData(pos=np.array([0, 0, axis_length]))
    neg_x_label = GLTextItem(text='-X', color='w'); neg_x_label.setData(pos=np.array([-axis_length, 0, 0]))
    neg_y_label = GLTextItem(text='-Y', color='w'); neg_y_label.setData(pos=np.array([0, -axis_length, 0]))
    neg_z_label = GLTextItem(text='-Z', color='w'); neg_z_label.setData(pos=np.array([0, 0, -axis_length]))
    main_view.addItem(x_label); main_view.addItem(y_label); main_view.addItem(z_label)
    main_view.addItem(neg_x_label); main_view.addItem(neg_y_label); main_view.addItem(neg_z_label)
    
    # --- Add Numbered Ticks to Axes ---
    all_ticks = (create_axis_ticks('x', axis_length, tick_spacing) + create_axis_ticks('y', axis_length, tick_spacing) + create_axis_ticks('z', axis_length, tick_spacing))
    for tick in all_ticks: main_view.addItem(tick)
    all_numbers = (create_axis_numbers('x', axis_length, tick_spacing) + create_axis_numbers('y', axis_length, tick_spacing) + create_axis_numbers('z', axis_length, tick_spacing))
    for number in all_numbers: main_view.addItem(number)
    main_view.set_number_labels(all_numbers)

    # --- 1. The Device: Galvo as a cube at the origin (0,0,0) ---
    galvo_size = 5.0
    half_size = galvo_size / 2.0
    galvo_faces = gl.GLBoxItem(size=QtGui.QVector3D(galvo_size, galvo_size, galvo_size), color=(0.8, 0.7, 0.2, 0.9))
    main_view.addItem(galvo_faces)
    verts = np.array([[-half_size,-half_size,-half_size], [half_size,-half_size,-half_size], [half_size,half_size,-half_size], [-half_size,half_size,-half_size],
                      [-half_size,-half_size,half_size], [half_size,-half_size,half_size], [half_size,half_size,half_size], [-half_size,half_size,half_size]])
    lines = np.array([[verts[0],verts[1]], [verts[1],verts[2]], [verts[2],verts[3]], [verts[3],verts[0]], [verts[4],verts[5]], [verts[5],verts[6]],
                      [verts[6],verts[7]], [verts[7],verts[4]], [verts[0],verts[4]], [verts[1],verts[5]], [verts[2],verts[6]], [verts[3],verts[7]]])
    galvo_wireframe = gl.GLLinePlotItem(pos=lines, color='w', width=1, mode='lines', antialias=True)
    main_view.addItem(galvo_wireframe)

    # --- 2. The Action: Laser shoots OUT from the origin along +Z ---
    laser_start_point = np.array([0, 0, 0])
    laser_end_point = np.array([0, 0, 50])
    laser_beam = gl.GLLinePlotItem(pos=np.array([laser_start_point, laser_end_point]), color=(1,0,0,0.8), width=2, antialias=True)
    main_view.addItem(laser_beam)
    
    # --- 3. The Target: A screen/grid that intercepts the laser beam ---
    target_plane = gl.GLGridItem()
    target_plane.setSize(x=60, y=60)
    target_plane.setSpacing(x=5, y=5)
    target_plane.translate(0, 0, 50)
    main_view.addItem(target_plane)

    pg.exec()