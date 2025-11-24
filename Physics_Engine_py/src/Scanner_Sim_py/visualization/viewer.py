# The MyView Class (Camera logic)

import pyqtgraph.opengl as gl
from PyQt5 import QtGui
from PyQt5.QtCore import Qt

# Custom View for Zoom/PAN control 
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