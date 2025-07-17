import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

# --- CONFIGURATION ---
SERIAL_PORT = '/dev/ttyUSB0'  # IMPORTANT: Change this to your ESP32's port!
                               # Linux/Mac: /dev/ttyUSB0, /dev/tty.SLAB_USBtoUART, etc.
                               # Windows: COM3, COM4, etc.
SERIAL_BAUD = 115200
MAX_DATA_POINTS = 100 # How many points to display on the x-axis

# --- GLOBAL VARIABLES ---
# A 'deque' is a special list that automatically removes old items
# when new ones are added, keeping the size constant.
data = deque(maxlen=MAX_DATA_POINTS)

# --- PLOT SETUP ---
fig, ax = plt.subplots()
line, = ax.plot([], [])
ax.set_ylim(0, 4100)  # ADC range is 0-4095
ax.set_xlim(0, MAX_DATA_POINTS)
ax.set_xlabel("Time (samples)")
ax.set_ylabel("ADC Reading")
ax.set_title("Real-time Photodiode Sensor Data")
ax.grid()

# --- SERIAL CONNECTION ---
try:
    ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=1)
except serial.SerialException:
    print(f"Error: Could not open port {SERIAL_PORT}.")
    print("Please check the port name and make sure no other program is using it.")
    exit()

# --- ANIMATION FUNCTION ---
# This function is called repeatedly by Matplotlib to update the plot.
def update(frame):
    try:
        # Read a line from the serial port (e.g., "1234\n")
        line_data = ser.readline().decode('utf-8').strip()
        if line_data:
            # Convert the string to a number
            adc_value = int(line_data)
            data.append(adc_value)
            
            # Update the plot data
            line.set_data(range(len(data)), data)
            
            # Optional: dynamically adjust y-axis limits
            # ax.set_ylim(min(data) - 100, max(data) + 100)
            
    except (ValueError, UnicodeDecodeError):
        # Ignore lines that aren't valid numbers
        pass
    except Exception as e:
        print(f"An error occurred: {e}")
        
    return line,

# --- START THE PLOT ---
# Create the animation. It calls the 'update' function every 20ms.
ani = animation.FuncAnimation(fig, update, blit=True, interval=20, save_count=MAX_DATA_POINTS)

print("Starting plot. Close the plot window to stop.")
plt.show()

# Clean up when the plot window is closed
ser.close()
print("Serial port closed.")