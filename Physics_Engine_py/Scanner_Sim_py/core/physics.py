# Ray tracing, Reflection logic, Intersection

import numpy as np


def normalize(vec):
    """
    Helper to normalize a vector (make length = 1).
    """
    norm = np.linalg.norm(vec)
    if norm == 0: 
        return vec
    return vec / norm


def calculate_reflection(incident_vec, normal_vec):
    """
    Calculates the reflection vector using R = I - 2(I . N)N
    
    Args:
        incident_vec: The incoming direction vector (numpy array).
        normal_vec: The surface normal vector (numpy array).
        
    Returns:
        The reflection vector (numpy array).
    """
    # 1. Normalize inputs to be safe
    i = incident_vec / np.linalg.norm(incident_vec)
    n = normal_vec / np.linalg.norm(normal_vec)
    
    # 2. The Math
    # dot(i, n)
    dot_prod = np.dot(i, n)
    
    # r = i - 2 * dot * n
    reflection = i - 2 * dot_prod * n
    
    return reflection

def intersect_line_plane(ray_origin, ray_dir, plane_point, plane_normal):
    """
    Calculates where a line hits a plane.
    
    Returns:
        hit_point (np.array): The XYZ coordinates of the hit.
        t (float): The distance from origin to hit.
    """
    # denom = dot(dir, normal)
    denom = np.dot(ray_dir, plane_normal)
    
    # Avoid divide by zero (parallel lines)
    if abs(denom) < 1e-6:
        # Return current position and 0 distance (Miss)
        return ray_origin, 0.0 
        
    # t = dot(plane_point - origin, normal) / denom
    vector_to_plane = plane_point - ray_origin
    t = np.dot(vector_to_plane, plane_normal) / denom
    
    # Calculate the actual point in 3D space
    hit_point = ray_origin + (ray_dir * t)
    
    # CRITICAL: Return BOTH values as a tuple
    return hit_point, t