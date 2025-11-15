import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from pyqtgraph.opengl import GLLinePlotItem, GLTextItem, GLMeshItem
from PyQt5 import QtGui, QtCore

# Custom GLViewWidget with a fixed, standard "XY Plane" view
class MyView(gl.GLViewWidget):
    def __init__(self):
        super().__init__()

        # --- The New, Fixed "XY Plane" View ---
        self.initial_opts = {
            # Look at the origin, where the action is.
            'center': QtGui.QVector3D(0, 0, 0),

            # Start zoomed out enough to see the 50mm axes.
            'distance': 200,

            # Elevation: 30 degrees puts the camera directly *above* the XY plane.
            'elevation': 10,

            # Azimuth: -90 degrees rotates the camera so that the world's
            # +X axis points to the right of the screen.
            'azimuth': -90
        }

        # Apply the fixed camera position
        self.opts['center'] = self.initial_opts['center']
        self.setCameraPosition(
            distance=self.initial_opts['distance'],
            elevation=self.initial_opts['elevation'],
            azimuth=self.initial_opts['azimuth']
        )

        # Use orthographic projection for a true 2D/CAD-like view
        self.opts['projection'] = 'perspective'

        # --- Dynamic Labels Feature ---
        self.label_visibility_threshold = 120
        self.number_labels = []

        self.setWindowTitle("Coordinate Axes - XY Plane View (mm)")

    def set_number_labels(self, labels):
        self.number_labels = labels
        self.update_labels_visibility()

    def update_labels_visibility(self):
        show_labels = self.opts['distance'] < self.label_visibility_threshold
        for label in self.number_labels:
            label.setVisible(show_labels)

    def keyPressEvent(self, event):
        modifiers = event.modifiers()
        key = event.key()
        view_changed = False

        if modifiers & QtCore.Qt.ControlModifier:
            if key == QtCore.Qt.Key_Plus or key == QtCore.Qt.Key_Equal:
                self.opts['distance'] -= 5
                if self.opts['distance'] < 1: self.opts['distance'] = 1
                view_changed = True
            elif key == QtCore.Qt.Key_Minus:
                self.opts['distance'] += 5
                view_changed = True
            elif key == QtCore.Qt.Key_R:
                self.opts['center'] = self.initial_opts['center']
                self.setCameraPosition(
                    distance=self.initial_opts['distance'],
                    elevation=self.initial_opts['elevation'],
                    azimuth=self.initial_opts['azimuth']
                )
                view_changed = True

        if view_changed:
            self.update()
            self.update_labels_visibility()
        else:
            super().keyPressEvent(event)

# ----- Helper Functions -----
def axis_line(start, end, color):
    """Creates a GLLinePlotItem for a main axis."""
    pts = np.array([start, end])
    return GLLinePlotItem(pos=pts, color=color, width=3, antialias=True)

def create_axis_ticks(axis, length, spacing=1.0, tick_size=0.2):
    """Creates a list of tick mark lines for a single axis."""
    ticks = []
    positions = np.arange(spacing, length + spacing, spacing)
    for pos in positions:
        if axis == 'x':
            start, end = [pos, -tick_size / 2, 0], [pos, tick_size / 2, 0]
        elif axis == 'y':
            start, end = [-tick_size / 2, pos, 0], [tick_size / 2, pos, 0]
        elif axis == 'z':
            start, end = [0, -tick_size/2, pos], [0, tick_size/2, pos] # Ticks on YZ plane
        pts = np.array([start, end])
        ticks.append(GLLinePlotItem(pos=pts, color=(1,1,1,0.5), width=1))
    return ticks

def create_axis_numbers(axis, length, spacing=1.0):
    """Creates a list of number labels (GLTextItem) for a single axis."""
    numbers = []
    positions = np.arange(spacing, length + spacing, spacing)
    for pos in positions:
        text = f'{pos:.0f}'
        if axis == 'x':
            position = [pos, 0.4, 0] # Offset for better visibility
        elif axis == 'y':
            position = [0.4, pos, 0]
        elif axis == 'z':
            position = [0, 0.4, pos]

        label = GLTextItem(text=text, color=(255, 255, 255, 255))
        label.setData(pos=np.array(position))
        numbers.append(label)
    return numbers

def create_cuboid(length, breadth, height):
    """Creates a MeshData object for a cuboid."""
    verts = np.array([
        [0, 0, 0],
        [length, 0, 0],
        [length, breadth, 0],
        [0, breadth, 0],
        [0, 0, height],
        [length, 0, height],
        [length, breadth, height],
        [0, breadth, height]
    ])

    faces = np.array([
        [0, 1, 2], [0, 2, 3],  # bottom
        [4, 5, 6], [4, 6, 7],  # top
        [0, 1, 5], [0, 5, 4],  # front
        [2, 3, 7], [2, 7, 6],  # back
        [1, 2, 6], [1, 6, 5],  # right
        [0, 3, 7], [0, 7, 4]   # left
    ])

    return gl.MeshData(vertexes=verts, faces=faces)


if __name__ == '__main__':
    app = pg.mkQApp()
    view = MyView()

    # --- Configuration ---
    axis_length = 50.0  # Length of each axis in "mm"
    tick_spacing = 1.0  # Place a tick every 1.0 "mm"

    # ----- Create Main Axes (Red, Green, Blue) -----
    view.addItem(axis_line([0, 0, 0], [axis_length, 0, 0], (1, 0, 0, 1)))
    view.addItem(axis_line([0, 0, 0], [0, axis_length, 0], (0, 1, 0, 1)))
    view.addItem(axis_line([0, 0, 0], [0, 0, axis_length], (0, 0, 1, 1)))

    # ----- Create Tick Marks (Always Visible) -----
    all_ticks = (
        create_axis_ticks('x', axis_length, tick_spacing) +
        create_axis_ticks('y', axis_length, tick_spacing) +
        create_axis_ticks('z', axis_length, tick_spacing)
    )
    for tick in all_ticks:
        view.addItem(tick)

    # ----- Create Number Labels (Dynamically Visible) -----
    all_numbers = (
        create_axis_numbers('x', axis_length, tick_spacing) +
        create_axis_numbers('y', axis_length, tick_spacing) +
        create_axis_numbers('z', axis_length, tick_spacing)
    )
    for number in all_numbers:
        view.addItem(number)

    # Register the numbers with the view to control their visibility
    view.set_number_labels(all_numbers)

    # ----- Create Main Axis Name Labels (Always Visible) -----
    origin_label = GLTextItem(text='Origin', color=(255, 255, 255, 255))
    x_label = GLTextItem(text='X (mm)', color=(255, 255, 255, 255))
    y_label = GLTextItem(text='Y (mm)', color=(255, 255, 255, 255))
    z_label = GLTextItem(text='Z (mm)', color=(255, 255, 255, 255))

    origin_label.setData(pos=np.array([-1, -1, 0]))
    x_label.setData(pos=np.array([axis_length, 0, 0]))
    y_label.setData(pos=np.array([0, axis_length, 0]))
    z_label.setData(pos=np.array([0, 0, axis_length]))

    view.addItem(origin_label)
    view.addItem(x_label)
    view.addItem(y_label)
    view.addItem(z_label)

    # ----- Create and Add the First Cuboid (Red, rotating on X-axis) -----
    cuboid1_mesh = create_cuboid(length=20, breadth=8, height=1)
    cuboid1 = GLMeshItem(meshdata=cuboid1_mesh, smooth=False, drawFaces=True,
                         drawEdges=True, edgeColor=(1, 1, 1, 1), color=(1, 0, 0, 0.5))
    # Apply a static 10-degree rotation around the X-axis
    cuboid1.rotate(45, 1, 0, 0) # angle, x, y, z
    view.addItem(cuboid1)


    # ----- Create and Add the Second Cuboid (Blue, rotating on Y-axis) -----
    cuboid2_mesh = create_cuboid(length=20, breadth=8, height=1)
    cuboid2 = GLMeshItem(meshdata=cuboid2_mesh, smooth=False, drawFaces=True,
                         drawEdges=True, edgeColor=(1, 1, 1, 1), color=(0, 0, 1, 0.5))
    # Apply a static 10-degree rotation around the Y-axis
    cuboid2.rotate(45, 0, 1, 0) # angle, x, y, z
    view.addItem(cuboid2)

    # --- Animation code has been removed ---

    view.show()
    pg.exec()