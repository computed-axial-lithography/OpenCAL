import subprocess
import tkinter as tk
from PIL import Image, ImageTk

# Get monitor information using xrandr
def get_monitor_info():
    output = subprocess.run(["xrandr", "--listmonitors"], capture_output=True, text=True).stdout
    lines = output.split("\n")[1:]  # Skip first line (header)
    monitors = []
    
    for line in lines:
        parts = line.split()
        
        # Ensure there are enough parts in the line (should have at least 4 parts)
        if len(parts) >= 4:
            resolution = parts[2].split("+")[0]  # Extract resolution before '+'
            
            # Remove any scaling factor (if present)
            width_height = resolution.split("x")
            if len(width_height) == 2:
                width = int(width_height[0].split("/")[0])  # Remove scaling factor if present
                height = int(width_height[1].split("/")[0])  # Remove scaling factor if present
            else:
                print(f"Warning: Resolution format not recognized for monitor: {line}")
                continue  # Skip this monitor if resolution is not recognized
            
            # Extract position offset (if present)
            offset = parts[2].split("+")[1:]  # Extract position
            x_offset = int(offset[0]) if len(offset) > 0 else 0
            y_offset = int(offset[1]) if len(offset) > 1 else 0
            
            # Last item is the monitor name
            name = parts[-1]
            
            # Append monitor info to the list
            monitors.append({"name": name, "width": width, "height": height, "x": x_offset, "y": y_offset})
    
    return monitors

# Function to get HDMI-2 screen info
def get_hdmi2_position():
    monitors = get_monitor_info()
    for m in monitors:
        if "XWAYLAND2" in m["name"]:  # Adjust based on `xrandr` output
            print(f"HDMI-2 Position: x={m['x']}, y={m['y']}, width={m['width']}, height={m['height']}")
            return m["x"], m["y"], m["width"], m["height"]
    return 0, 0, 800, 480  # Fallback values

# Get HDMI-2 screen position
x_pos, y_pos, width, height = get_hdmi2_position()
print(f'x_pos: {x_pos}, y_pos: {y_pos}')

# Load the image
image_path = "/home/opencal/opencal/OpenCAL/hardware/water-lily-2840_4320.jpg"
image = Image.open(image_path)

# Resize the image to fit the screen (to the detected resolution)
#image_resized = image.resize((width, height))

# Initialize tkinter window
root = tk.Tk()

# Set the window title
root.title("Display Image")

# Set the window size to the image's size
root.geometry(f"{width}x{height}+{x_pos}+{y_pos}")  # Position window at x_pos, y_pos

# Create a PhotoImage object from the resized image for displaying in tkinter
photo = ImageTk.PhotoImage(image)

# Create a label widget to display the image
label = tk.Label(root, image=photo)
label.pack()
# Define a function to stop the tkinter mainloop when ESC is pressed
def on_escape(event):
    print("Escape pressed, closing window.")
    root.quit()  # This will stop the mainloop

# Bind the ESC key to the on_escape function
root.bind("<Escape>", on_escape)

# Run the tkinter main loop to display the window
root.mainloop()