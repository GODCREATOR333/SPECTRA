import cv2 as cv
import numpy as np
import json

# =============================
# USER CONFIGURATION
# =============================

CHESSBOARD_SIZE = (10, 7)   # internal corners (width, height)
SQUARE_SIZE_MM = 25.0       # checkerboard square size
CAMERA_HEIGHT_CM = 100.0    # camera height above ground

# Camera → Galvo physical offset (cm)
CAMERA_OFFSET_CM = {
    "x": -10.0,   # left  = negative X
    "y":  0.0,    # forward
    "z":  10.0    # up
}

MIN_FRAMES = 15

# =============================
# PREPARE OBJECT POINTS
# =============================

objp = np.zeros((CHESSBOARD_SIZE[0] * CHESSBOARD_SIZE[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:CHESSBOARD_SIZE[0], 0:CHESSBOARD_SIZE[1]].T.reshape(-1, 2)
objp *= SQUARE_SIZE_MM

objpoints = []
imgpoints = []

criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

cap = cv.VideoCapture(0)

print("\nPS3 EYE CALIBRATION")
print("Press 's' to store a frame when corners appear")
print("Press 'q' to finish\n")

count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    found, corners = cv.findChessboardCorners(gray, CHESSBOARD_SIZE)

    display = frame.copy()
    if found:
        cv.drawChessboardCorners(display, CHESSBOARD_SIZE, corners, found)

    cv.imshow("Calibration", display)
    key = cv.waitKey(1) & 0xFF

    if found and key == ord('s'):
        refined = cv.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)
        objpoints.append(objp)
        imgpoints.append(refined)
        count += 1
        print(f"Captured frame {count}")

    if key == ord('q'):
        break

cap.release()
cv.destroyAllWindows()

if count < MIN_FRAMES:
    raise RuntimeError("Not enough calibration frames")

# =============================
# CAMERA CALIBRATION
# =============================

ret, K, D, rvecs, tvecs = cv.calibrateCamera(
    objpoints,
    imgpoints,
    gray.shape[::-1],
    None,
    None
)

# =============================
# FIXED EXTRINSICS (CASE A)
# =============================

R_cam_to_world = np.array([
    [1, 0,  0],
    [0, 1,  0],
    [0, 0, -1]
], dtype=float)

t_cam_to_world = np.array([
    CAMERA_OFFSET_CM["x"],
    CAMERA_OFFSET_CM["y"],
    CAMERA_OFFSET_CM["z"]
], dtype=float)

# =============================
# SAVE FINAL CALIBRATION
# =============================

calibration = {
    "intrinsics": {
        "camera_matrix": K.tolist(),
        "distortion_coefficients": D.tolist(),
        "image_resolution": [frame.shape[1], frame.shape[0]],
        "reprojection_error_px": float(ret)
    },
    "extrinsics": {
        "rotation_matrix": R_cam_to_world.tolist(),
        "translation_cm": t_cam_to_world.tolist()
    },
    "scene_assumptions": {
        "camera_height_cm": CAMERA_HEIGHT_CM,
        "camera_orientation": "perfect_nadir",
        "ground_plane_z": 0
    }
}

with open("ps3eye_calibration.json", "w") as f:
    json.dump(calibration, f, indent=4)

print("\nCALIBRATION COMPLETE")
print(f"Reprojection Error: {ret:.4f} px")
print("Saved to ps3eye_calibration.json")
