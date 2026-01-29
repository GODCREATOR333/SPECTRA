import os
import cv2 as cv
import numpy as np
import json
from PyQt5 import QtCore
from ultralytics import YOLO

class VisionWorker(QtCore.QThread):
    target_detected = QtCore.pyqtSignal(float, float, float)
    frame_signal = QtCore.pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.running = True
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        self.assets_dir = os.path.join(parent_dir, "Extract_coordintes")
        
        self.model_path = os.path.join(self.assets_dir, "best.pt")
        self.calib_path = os.path.join(self.assets_dir, "ps3eye_calibration.json")

    def run(self):
        # 1. LOAD CALIBRATION
        if not os.path.exists(self.calib_path):
            print(f"ERROR: Cannot find calibration at {self.calib_path}")
            return

        with open(self.calib_path, "r") as f:
            calib = json.load(f)

        K = np.array(calib["intrinsics"]["camera_matrix"], dtype=np.float32)
        D = np.array(calib["intrinsics"]["distortion_coefficients"][0], dtype=np.float32)
        H = calib["scene_assumptions"]["camera_height_cm"]
        R = np.array(calib["extrinsics"]["rotation_matrix"], dtype=np.float32)
        t = np.array(calib["extrinsics"]["translation_cm"], dtype=np.float32)
        
        fx, fy = K[0, 0], K[1, 1]
        cx, cy = K[0, 2], K[1, 2]

        # 2. LOAD YOLO
        if not os.path.exists(self.model_path):
            print(f"ERROR: Cannot find model at {self.model_path}")
            return
            
        print("Loading YOLO Model...")
        model = YOLO(self.model_path)

        # 3. OPEN CAMERA
        cap = cv.VideoCapture(0)
        if not cap.isOpened():
            print("ERROR: Camera not found")
            return

        print("Vision System Started.")

        while self.running:
            ret, frame = cap.read()
            if not ret: break

            # Run Inference
            results = model(frame, verbose=False, conf=0.25)[0]

            # --- SELECTION LOGIC VARIABLES ---
            best_target_world = None # (Xw, Yw, Zw)
            best_box_coords = None   # (x1, y1, x2, y2)
            min_dist_to_center = float('inf') # Find closest to center
            
            detected_count = 0

            for box in results.boxes:
                detected_count += 1
                
                # Bounding box
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                u = (x1 + x2) / 2.0
                v = (y1 + y2) / 2.0

                # --- DRAW CANDIDATE (Yellow) ---
                # Draw all detections in Yellow first
                cv.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 255), 1)

                # --- SELECTION MATH ---
                # Distance from image center (cx, cy)
                dist_sq = (u - cx)**2 + (v - cy)**2
                
                # If this is the closest weed to the center, pick it!
                if dist_sq < min_dist_to_center:
                    min_dist_to_center = dist_sq
                    best_box_coords = (x1, y1, x2, y2)
                    
                    # Calculate Physics Coordinates ONLY for the best one (Optimization)
                    pts = np.array([[[u, v]]], dtype=np.float32)
                    undistorted = cv.undistortPoints(pts, K, D, P=K)
                    u_u, v_u = undistorted[0][0]

                    x = (u_u - cx) / fx
                    y = (v_u - cy) / fy
                    ray = np.array([x, y, 1.0], dtype=np.float32)
                    P_cam = ray * H
                    P_world = R @ P_cam + t
                    
                    best_target_world = (float(P_world[0]), float(P_world[1]), 100.0)

            # --- AFTER LOOP: ACT ON BEST TARGET ---
            if best_target_world is not None:
                # 1. Emit Signal (Only ONCE per frame)
                self.target_detected.emit(*best_target_world)
                
                # 2. Draw LOCKED Box (Red & Thick)
                bx1, by1, bx2, by2 = best_box_coords
                cv.rectangle(frame, (int(bx1), int(by1)), (int(bx2), int(by2)), (0, 0, 255), 3)
                
                # 3. Draw Target Text
                Xw, Yw, _ = best_target_world
                label = f"LOCKED: {Xw:.1f}, {Yw:.1f}"
                cv.putText(frame, label, (int(bx1), int(by1)-10), 
                           cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            elif detected_count == 0:
                cv.putText(frame, "Scanning...", (20, 40), 
                           cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)

            # --- EMIT FRAME ---
            rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            self.frame_signal.emit(rgb_frame)

        cap.release()


    def stop(self):
        self.running = False
        self.wait()