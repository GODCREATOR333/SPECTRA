import numpy as np

class GalvoAxis:
    def __init__(self, name, rest_angle, inertia=0.02, damping=0.2, stiffness=0.5):
        self.name = name
        self.state = np.array([0.0, 0.0]) # [theta, omega]
        self.J = inertia
        self.b = damping
        self.k = stiffness
        self.rest_angle = rest_angle
        self.voltage = 0.0      
        self.K_motor = 20.0 

    def update(self, dt):
        theta = self.state[0]
        omega = self.state[1]
        
        torque_motor = self.K_motor * self.voltage
        torque_net = torque_motor - (self.b * omega) - (self.k * (theta - self.rest_angle))
        alpha = torque_net / self.J
        
        new_omega = omega + alpha * dt
        new_theta = theta + new_omega * dt
        
        self.state = np.array([new_theta, new_omega])
        return new_theta

class GalvoModel:
    def __init__(self):
        self.galvo_x = GalvoAxis(name="Red", rest_angle=45.0)
        self.galvo_y = GalvoAxis(name="Blue", rest_angle=-45.0)

        self.static_states = {
            "Cuboid 1 (Red)": {'pos': [0, 20, 0], 'rest_rot_x': 45},
            "Cuboid 2 (Blue)": {'pos': [0, 0, 0], 'rest_rot_z': -45}
        }
        self.state = {
            "Cuboid 1 (Red)": {'current_angle': 0.0},
            "Cuboid 2 (Blue)": {'current_angle': 0.0}
        }

    def apply_voltage(self, v_x, v_y):
        self.galvo_x.voltage = np.clip(v_x, -24, 24) # Increased Voltage Limit
        self.galvo_y.voltage = np.clip(v_y, -24, 24)

    # CHANGED: Added dt parameter
    def update(self, dt):
        angle_x = self.galvo_x.update(dt)
        angle_y = self.galvo_y.update(dt)
        
        self.state["Cuboid 1 (Red)"]['current_angle'] = angle_x
        self.state["Cuboid 2 (Blue)"]['current_angle'] = angle_y