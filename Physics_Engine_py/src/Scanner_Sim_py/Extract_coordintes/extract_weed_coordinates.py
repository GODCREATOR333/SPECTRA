import cv2 as cv
import numpy as np
import json
from ultralytics import YOLO

# =============================
# LOAD CALIBRATION
# =============================

with open("ps3eye_calibration.json", "r") as f:
    calib = json.load(f)

K = np.array(calib["intrinsics"]["camera_matrix"], dtype=np.float32)
D = np.array(calib["intrinsics"]["distortion_coefficients"][0], dtype=np.float32)

fx = K[0, 0]
fy = K[1, 1]
cx = K[0, 2]
cy = K[1, 2]

H = calib["scene_assumptions"]["camera_height_cm"]

R = np.array(calib["extrinsics"]["rotation_matrix"], dtype=np.float32)
t = np.array(calib["extrinsics"]["translation_cm"], dtype=np.float32)

# =============================
# LOAD YOLO MODEL
# =============================

model = YOLO("best.pt")

# =============================
# CAMERA
# =============================

cap = cv.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Camera not found")

print("\nRunning YOLO with calibrated geometry")
print("Press 'q' to quit\n")

# =============================
# MAIN LOOP
# =============================

while True:
    ret, frame = cap.read()
    if not ret:
        break



    results = model(frame, verbose=False)[0]

    for box in results.boxes:
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

        # Bounding box center
        u = (x1 + x2) / 2.0
        v = (y1 + y2) / 2.0

        # =============================
        # UNDISTORT PIXEL
        # =============================

        pts = np.array([[[u, v]]], dtype=np.float32)
        undistorted = cv.undistortPoints(pts, K, D, P=K)
        u_u, v_u = undistorted[0][0]

        # =============================
        # PIXEL → CAMERA RAY
        # =============================

        x = (u_u - cx) / fx
        y = (v_u - cy) / fy

        ray = np.array([x, y, 1.0], dtype=np.float32)

        # =============================
        # INTERSECT WITH GROUND
        # =============================

        P_cam = ray * H

        # =============================
        # CAMERA → WORLD (GALVO)
        # =============================

        P_world = R @ P_cam + t

        Xw, Yw, Zw = P_world

        # =============================
        # OUTPUT
        # =============================

        print(f"Detected object at WORLD (cm): X={Xw:.2f}, Y={Yw:.2f}, Z={Zw:.2f}")

        # Visualize for demo
        cv.circle(frame, (int(u), int(v)), 5, (0, 0, 255), -1)

    cv.imshow("YOLO + Calibration Demo", frame)

    if cv.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv.destroyAllWindows()

