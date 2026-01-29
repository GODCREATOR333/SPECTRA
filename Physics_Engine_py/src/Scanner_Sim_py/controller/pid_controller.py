import numpy as np

class BaseController:
    def calculate(self, target, current, dt):
        return 0.0

class PController(BaseController):
    # Pure P is always a bit loose, but we make it stiffer now
    def __init__(self, Kp=5.0): 
        self.Kp = Kp

    def calculate(self, target, current_state, dt):
        error = target - current_state[0]
        return self.Kp * error

class PIDController(BaseController):
    # Tuned for SNAP response.
    # No Integral (I) to prevent wobble. High Derivative (D) to brake hard.
    def __init__(self, Kp=15.0, Ki=0.0, Kd=0.5):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.prev_error = 0.0
        self.integral = 0.0

    def calculate(self, target, current_state, dt):
        current_angle = current_state[0]
        error = target - current_angle
        
        self.integral += error * dt
        
        if dt > 0:
            derivative = (error - self.prev_error) / dt
        else:
            derivative = 0
        self.prev_error = error
        
        return (self.Kp * error) + (self.Ki * self.integral) + (self.Kd * derivative)

class LQRController(BaseController):
    # The "Perfect" Controller.
    # High Stiffness (k1) + High Damping (k2)
    def __init__(self):
        self.k1 = 18.0   # Stiffness (Speed)
        self.k2 = 1.2    # Damping (Braking)

    def calculate(self, target, current_state, dt):
        current_angle = current_state[0]
        current_velocity = current_state[1]
        
        error_pos = current_angle - target
        error_vel = current_velocity - 0
        
        return -(self.k1 * error_pos) - (self.k2 * error_vel)