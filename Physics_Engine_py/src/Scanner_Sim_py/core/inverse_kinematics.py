import numpy as np
from Scanner_Sim_py.core import physics

class IKSolver:
    def __init__(self):
        # Configuration matching your Engine.py setup
        # IF YOU CHANGE ENGINE.PY, UPDATE THIS!
        self.config = {
            "source_pos": [50, 0, 0],
            "blue_pos": [0, 0, 0],
            "blue_rest_axis": [0, 0, 1],   # Z-axis rotation
            "blue_rest_angle": -45,
            "red_pos": [0, 20, 0],         # Red mirror is at Y=20
            "red_rest_axis": [1, 0, 0],    # X-axis rotation
            "red_rest_angle": 45,
            "screen_z": 100.0              # Target Plane Distance
        }

    def solve(self, target_pos, start_guess=(0, 0)):
        """
        Finds the angles (theta_x, theta_y) required to hit 'target_pos'.
        
        Args:
            target_pos (list/array): [x, y, z] target in world coordinates.
            start_guess (tuple): (angle_x, angle_y) starting point to speed up search.
            
        Returns:
            (float, float): Best (theta_x, theta_y) in degrees.
        """
        
        # 1. Setup
        target = np.array(target_pos)
        theta_x, theta_y = start_guess
        
        # Gradient Descent Parameters
        learning_rate = 0.5   # How big of a jump to make
        epsilon = 0.01        # Small angle nudge to measure sensitivity
        max_iterations = 50   # Don't loop forever
        tolerance = 0.1       # Stop if error is less than 0.1mm
        
        for i in range(max_iterations):
            # A. Where are we now?
            current_hit, _ = physics.trace_laser_path(theta_x, theta_y, self.config)
            
            if current_hit is None:
                # If we miss the mirror entirely, reset to center
                theta_x, theta_y = 0, 0
                continue
                
            # B. Calculate Error (Distance squared)
            # We only care about X and Y error on the screen plane
            error_vec = current_hit[:2] - target[:2]
            error_mag = np.linalg.norm(error_vec)
            
            # Stop if we are close enough
            if error_mag < tolerance:
                break
                
            # C. Estimate Gradients (The "Jacobian")
            # "If I move X by 0.01 deg, how much does the laser move?"
            
            # Nudge X
            hit_dx, _ = physics.trace_laser_path(theta_x + epsilon, theta_y, self.config)
            if hit_dx is None: dx_grad = np.array([0.0, 0.0])
            else: dx_grad = (hit_dx[:2] - current_hit[:2]) / epsilon
            
            # Nudge Y
            hit_dy, _ = physics.trace_laser_path(theta_x, theta_y + epsilon, self.config)
            if hit_dy is None: dy_grad = np.array([0.0, 0.0])
            else: dy_grad = (hit_dy[:2] - current_hit[:2]) / epsilon
            
            # D. Update Angles (Simple Gradient Descent)
            # This is a simplified Newton-step approximation
            # We want to reduce error_vec.
            
            # How much of the error is caused by X? 
            # (Dot product of error direction vs gradient direction)
            # Note: This is a rough approximation but works well for smooth mirrors.
            
            # A more robust update:
            # New_Angle = Old_Angle - Learning_Rate * (Gradient * Error)
            
            # We project the error onto the gradient directions
            # To fix X:
            correction_x = np.dot(error_vec, dx_grad) * learning_rate
            # To fix Y:
            correction_y = np.dot(error_vec, dy_grad) * learning_rate
            
            # Apply (Subtract correction because we want to reduce error)
            # We normalize by the gradient magnitude to avoid huge jumps
            norm_x = np.linalg.norm(dx_grad)**2 + 1e-6
            norm_y = np.linalg.norm(dy_grad)**2 + 1e-6
            
            theta_x -= (correction_x / norm_x)
            theta_y -= (correction_y / norm_y)
            
        return theta_x, theta_y