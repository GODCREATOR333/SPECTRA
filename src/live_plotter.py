

import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

# --- YOU MUST CHANGE THIS ---
# Find your port in Arduino IDE (Tools -> Port). Examples: 'COM3' or '/dev/tty.usbserial-0001'
SERIAL_PORT = '/dev/ttyUSB0'  
BAUD_RATE = 115200
MAX_DATA_POINTS = 200 # How many data points to show on the plot at once.

# --- SCRIPT STARTS HERE ---
print(f"Attempting to connect to {SERIAL_PORT}...")
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
except serial.SerialException as e:
    print(f"Error: Could not open serial port. {e}")
    print("Check the port name and make sure the Arduino Serial Monitor is closed.")
    exit()

print("Successfully connected. Starting live plot...")
print("Close the plot window to stop the script.")

data = deque(maxlen=MAX_DATA_POINTS)
fig, ax = plt.subplots(figsize=(12,6))
line, = ax.plot([], [])
ax.set_ylim(0, 4095)
ax.set_xlim(0, MAX_DATA_POINTS)
ax.set_title("Live ESP32 ADC Reading")
ax.set_xlabel("Time (samples)")
ax.set_ylabel("Raw ADC Value (0-4095)")
ax.grid(True)

# This text object will display the range of the current data
range_text = ax.text(0.02, 0.95, '', transform=ax.transAxes, verticalalignment='top')

def update(frame):
    try:
        serial_line = ser.readline().decode('utf-8').strip()
        if serial_line:
            adc_value = int(serial_line)
            data.append(adc_value)
            line.set_data(range(len(data)), data)
            
            if len(data) > 10:
                min_val = min(data)
                max_val = max(data)
                variation = max_val - min_val
                
                # Update the Y-axis to zoom in on the action
                ax.set_ylim(min_val - 20, max_val + 20)
                # Update the text with the current variation
                range_text.set_text(f'Variation (Max-Min): {variation} counts')

    except (ValueError, UnicodeDecodeError):
        pass # Ignore bad data
        
    return line, range_text

ani = animation.FuncAnimation(fig, update, blit=True, interval=10)
plt.show()

ser.close()
print("Serial port closed.")