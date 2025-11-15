import sys
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from PyQt5 import QtWidgets
import numpy as np

app = QtWidgets.QApplication(sys.argv)
w = gl.GLViewWidget()
w.show()
w.setWindowTitle('Visible 3D Boxes')

# Camera
w.setCameraPosition(distance=6.0)

# Axis
axis = gl.GLAxisItem()
axis.setSize(3,3,3)
w.addItem(axis)

# Function to create colored cube mesh
def create_cube(center, size, color=(0.8,0.8,0.8,1)):
    verts = np.array([
        [-1,-1,-1],
        [1,-1,-1],
        [1,1,-1],
        [-1,1,-1],
        [-1,-1,1],
        [1,-1,1],
        [1,1,1],
        [-1,1,1],
    ], dtype=float)
    verts *= size/2
    verts += center
    faces = np.array([
        [0,1,2],[0,2,3],
        [4,5,6],[4,6,7],
        [0,1,5],[0,5,4],
        [2,3,7],[2,7,6],
        [1,2,6],[1,6,5],
        [0,3,7],[0,7,4]
    ])
    mesh = gl.GLMeshItem(vertexes=verts, faces=faces, faceColors=np.array([color]*12), smooth=False, drawEdges=True)
    return mesh

# Create two boxes
M1 = create_cube(np.array([-1.5,0,0]), np.array([1,2,1]))
M2 = create_cube(np.array([1.5,0,0]), np.array([1,2,1]))
w.addItem(M1)
w.addItem(M2)

if __name__ == '__main__':
    QtWidgets.QApplication.instance().exec_()
