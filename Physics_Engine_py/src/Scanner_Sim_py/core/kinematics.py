# Rotations, Matrix utils (get_model_matrix)

import numpy as np

def get_model_matrix(position, rotation_degrees, rotation_axis):
    """
    position: [x, y, z]
    rotation_degrees: float angle
    rotation_axis: [1,0,0] for X, [0,1,0] for Y, etc.
    Returns: 4x4 Numpy Matrix
    """
    # 1. Identity Matrix
    M = np.eye(4)
    
    # 2. Rotation (Rodrigues' Rotation Formula logic or simplified)
    # Since we rotate around primary axes (X, Y, or Z), we can hardcode for speed.
    # C++ Implementation would use a library like GLM or Eigen here.
    rad = np.radians(rotation_degrees)
    c = np.cos(rad)
    s = np.sin(rad)
    
    R = np.eye(4)
    if rotation_axis == [1, 0, 0]: # Rotate X
        R[1,1] = c; R[1,2] = -s
        R[2,1] = s; R[2,2] = c
    elif rotation_axis == [0, 1, 0]: # Rotate Y
        R[0,0] = c; R[0,2] = s
        R[2,0] = -s; R[2,2] = c
    elif rotation_axis == [0, 0, 1]: # Rotate Z
        R[0,0] = c; R[0,1] = -s
        R[1,0] = s; R[1,1] = c
        
    # 3. Translation (Put position in the last column)
    T = np.eye(4)
    T[:3, 3] = position
    
    # 4. Combine: Translate * Rotate (Standard Robotics Order)
    # M = T @ R
    return T @ R


def apply_transform_to_point(matrix, point):
    """
    matrix: 4x4 numpy array
    point: [x, y, z]
    """
    # Convert to Homogeneous [x, y, z, 1]
    p4 = np.array([point[0], point[1], point[2], 1.0])
    
    # Multiply
    result = matrix @ p4
    
    # Return [x, y, z]
    return result[:3]

def apply_transform_to_vector(matrix, vector):
    """
    Applies a transformation to a DIRECTION vector (e.g., Normal, Ray Direction).
    Ignores translation (w=0).
    
    Args:
        matrix: 4x4 numpy array
        vector: [x, y, z]
    """
    # 1. Homogeneous Vector with w=0 (Direction only)
    v4 = np.array([vector[0], vector[1], vector[2], 0.0])
    
    # 2. Multiply
    result = matrix @ v4
    
    # 3. Return [x, y, z]
    return result[:3]