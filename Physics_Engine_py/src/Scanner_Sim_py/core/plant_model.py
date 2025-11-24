import numpy as np

class GalvoAxis:
    """
    Represents a SINGLE axis galvanometer (e.g., just X or just Y).
    Simulates a 2nd order Mass-Spring-Damper system.
    """
    def __init__(self, name, rest_angle, inertia=1.0, damping=0.5, stiffness=10.0):
        self.name = name
        
        # --- State Vector [Angle (theta), Velocity (omega)] ---
        # theta: degrees
        # omega: degrees per second
        self.state = np.array([0.0, 0.0]) 
        
        # --- Physical Parameters ---
        self.J = inertia       # Moment of Inertia (kg*m^2 ish) - generic units for now
        self.b = damping       # Damping coefficient
        self.k = stiffness     # Spring constant (restoring force)
        
        self.rest_angle = rest_angle # Where the spring wants to go (Neutral)
        self.target_angle = 0.0      # Where the motor wants to go (Set by controller)
        
        # Voltage-to-Torque gain (How strong is the magnet?)
        self.K_motor = 5.0 

    def update(self, dt):
        """
        Euler Integration Step (The simplest physics solver).
        Calculates new State based on Forces.
        """
        theta = self.state[0]
        omega = self.state[1]
        
        # 1. Calculate Error (Difference between current angle and rest)
        # The spring pulls back towards rest_angle + (target caused by voltage)
        # For this step, let's assume 'target_angle' applies a torque to move us away from rest.
        
        # Torque from Motor = Gain * (Target - Current)  <-- Proportional Controller (Simplest)
        # In real HIL, 'target_angle' would be input voltage.
        torque_motor = self.K_motor * (self.target_angle - theta)
        
        # Torque from Spring = -k * (displacement from rest)
        # Actually, let's simplify: The motor fights the spring.
        # But for this POC, let's just make the motor drive the position directly via torque.
        
        # 2. Sum of Forces (Torques)
        # Sum = Motor_Torque - Damping - Spring_Restoring
        # T_net = T_motor - (b * omega) - (k * (theta - rest))
        
        # Note: We divide torque by J (Inertia) to get Acceleration (alpha)
        # alpha = F / m
        alpha = (torque_motor - (self.b * omega)) / self.J
        
        # 3. Integrate (Euler Method)
        # New Velocity = Old Velocity + Accel * dt
        new_omega = omega + alpha * dt
        
        # New Position = Old Position + Velocity * dt
        new_theta = theta + new_omega * dt
        
        # 4. Update State
        self.state = np.array([new_theta, new_omega])
        
        return new_theta


class GalvoModel:
    """
    The System Container. Holds two GalvoAxis instances (X and Y).
    """
    def __init__(self):
        # We replace the dictionary configuration with Objects.
        
        # --- Axis 1: Red Mirror (X-Axis) ---
        # Positioned at Y=20, Rest Angle 45
        self.galvo_x = GalvoAxis(name="Red", rest_angle=45.0, inertia=0.5, damping=2.0, stiffness=0.0)
        self.galvo_x_pos_offset = [0, 20, 0] # Where it is in 3D space
        
        # --- Axis 2: Blue Mirror (Z-Axis) ---
        # Positioned at Origin, Rest Angle -45
        self.galvo_y = GalvoAxis(name="Blue", rest_angle=-45.0, inertia=0.5, damping=2.0, stiffness=0.0)
        self.galvo_y_pos_offset = [0, 0, 0]

        # Compatibility dictionary so we don't break the GUI yet
        self.static_states = {
            "Cuboid 1 (Red)": {'pos': self.galvo_x_pos_offset, 'rest_rot_x': 45, 'range': 15},
            "Cuboid 2 (Blue)": {'pos': self.galvo_y_pos_offset, 'rest_rot_z': -45, 'range': 15}
        }
        
        # We create a fake state dict so the GUI update_transforms() doesn't crash
        # This is a temporary bridge until we refactor the GUI to use objects directly.
        self.state = {
            "Cuboid 1 (Red)": {'current_angle': 0.0},
            "Cuboid 2 (Blue)": {'current_angle': 0.0}
        }

    def set_target(self, x_degrees, y_degrees):
        """Sets the Desired Angle (Input Signal)."""
        self.galvo_x.target_angle = x_degrees
        self.galvo_y.target_angle = y_degrees

    def update(self):
        """
        Advances physics by one time step (dt).
        """
        dt = 0.01 # 10ms step (Assuming 100Hz loop for now)
        
        # 1. Update Physics
        angle_x = self.galvo_x.update(dt)
        angle_y = self.galvo_y.update(dt)
        
        # 2. Sync to the "Compatibility State" for the GUI
        self.state["Cuboid 1 (Red)"]['current_angle'] = angle_x
        self.state["Cuboid 2 (Blue)"]['current_angle'] = angle_y