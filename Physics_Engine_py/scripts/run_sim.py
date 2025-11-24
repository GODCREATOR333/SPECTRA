# Run Final Script

import sys
import os
from PyQt5 import QtWidgets

# --- 1. PATH SETUP ---
current_dir = os.path.dirname(os.path.abspath(__file__)) # .../scripts
project_root = os.path.dirname(current_dir)              # .../Physics_Engine_py/
src_path = os.path.join(project_root, 'src')             # .../Physics_Engine_py/src


# NOW Python sees 'Scanner_Sim_py' as a top-level folder.
if src_path not in sys.path:
    sys.path.append(src_path)

# --- 2. IMPORT THE ENGINE ---
# Now Python can find the package
try:
    from Scanner_Sim_py.simulation.engine import MainWindow
except ImportError as e:
    print("CRITICAL IMPORT ERROR: Could not find the modules.")
    print(f"Make sure you are running this script. Error details:\n{e}")
    sys.exit(1)

# --- 3. RUN THE APP ---
if __name__ == '__main__':
    # Create the Qt Application
    app = QtWidgets.QApplication(sys.argv)
    
    # Create the Physics Engine Window
    win = MainWindow()
    win.show()
    
    # Start the Event Loop
    print("Simulation Started successfully.")
    sys.exit(app.exec_())