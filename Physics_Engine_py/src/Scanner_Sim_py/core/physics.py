# Ray tracing, Reflection logic, Intersection

import numpy as np
from Scanner_Sim_py.core import kinematics

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


def trace_laser_path(angle_x_deg, angle_y_deg, system_config):
    """
    Calculates the full path of the laser and the final hit point on the screen.
    
    Args:
        angle_x_deg (float): Rotation of Red Mirror (Fast Axis)
        angle_y_deg (float): Rotation of Blue Mirror (Slow Axis)
        system_config (dict): Dictionary containing positions and rest angles.
                              Example:
                              {
                                  "source_pos": [50, 0, 0],
                                  "blue_pos": [0, 0, 0],
                                  "blue_rest_axis": [0, 0, 1], # Z-axis rotation
                                  "blue_rest_angle": -45,
                                  "red_pos": [0, 20, 0],
                                  "red_rest_axis": [1, 0, 0],  # X-axis rotation
                                  "red_rest_angle": 45,
                                  "screen_z": 100
                              }
                              
    Returns:
        hit_point (np.array): [x, y, z] of where it hit the screen.
        path_points (list): List of points [source, blue_hit, red_hit, screen_hit]
    """
    
    # 1. Setup Data
    source_pos = np.array(system_config["source_pos"])
    
    # --- BLUE MIRROR (First Hit) ---
    b_pos = np.array(system_config["blue_pos"])
    b_rest = system_config["blue_rest_angle"]
    
    # Calculate Normal for Blue Mirror
    # Rotate around Z axis (rest + current control)
    # Note: We use the visuals helper, but pure math would be better. 
    # For now, we reuse kinematics to match the visual exactly.
    m_blue = kinematics.get_model_matrix(b_pos, b_rest + angle_y_deg, system_config["blue_rest_axis"])
    n1 = kinematics.apply_transform_to_vector(m_blue, [0, 1, 0]) # Initial Normal of the plate face
    # Wait, in your engine.py visuals, you rotated the plate 90 deg X to stand it up. 
    # Let's assume the normal is [0, 1, 0] in local space if it's a flat plate, 
    # or [0, 0, 1] if it was flat on ground.
    # Looking at engine.py: m_blue_vis = Rotate(90, X). 
    # If the mesh is flat on XY, rotating 90 X makes it face -Y or +Y.
    # Let's stick to the vector logic used in engine.py:
    # n1 = transform([0,0,1]) after applying blue_matrix
    n1 = kinematics.apply_transform_to_vector(m_blue, [0, 0, 1]) # Local Z is normal
    
    # Trace Source -> Blue
    dir_1 = normalize(b_pos - source_pos)
    r1 = calculate_reflection(dir_1, n1) # Reflection Vector 1
    
    # --- RED MIRROR (Second Hit) ---
    r_pos = np.array(system_config["red_pos"])
    
    # Intersect Ray 1 with Red Mirror Plane
    # Red mirror is at [0, 20, 0]. In engine.py you assumed it faces -Y ([0, -1, 0])
    plane_normal_red = np.array([0, -1, 0]) 
    p2, t2 = intersect_line_plane(b_pos, r1, r_pos, plane_normal_red)
    
    if t2 <= 0: return None, [] # Missed Red Mirror

    # Calculate Normal for Red Mirror
    r_rest = system_config["red_rest_angle"]
    m_red = kinematics.get_model_matrix(r_pos, r_rest + angle_x_deg, system_config["red_rest_axis"])
    n2 = kinematics.apply_transform_to_vector(m_red, [0, 0, 1])
    
    r2 = calculate_reflection(r1, n2) # Reflection Vector 2
    
    # --- SCREEN (Final Hit) ---
    screen_z = system_config["screen_z"]
    plane_point_screen = np.array([0, 0, screen_z])
    plane_normal_screen = np.array([0, 0, -1]) # Facing back at origin
    
    p3, t3 = intersect_line_plane(p2, r2, plane_point_screen, plane_normal_screen)
    
    if t3 <= 0: return None, [] # Missed Screen

    return p3, [source_pos, b_pos, p2, p3]