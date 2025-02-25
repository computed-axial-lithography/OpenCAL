# from PIL import Image
# import numpy as np
# import json

# class ProjectorController:
#     def __init__(self, config_file="OpenCAL/utils/config.json"):
#         with open(config_file, 'r') as f:
#             config = json.load(f)
#         self.framebuffer_path = config['projector'].get('framebuffer_path')

#     def display_image(self, image_path):
#         """Loads an image and writes it to the framebuffer without resizing or manipulation."""
#         try:
#             # Load the image (no resizing)
#             img = Image.open(image_path).convert("RGB")
            
#             # Convert the image to raw bytes (8-bit per channel, 24-bit color)
#             img_array = np.array(img, dtype=np.uint8)  # uint8 for 24-bit color (RGB)
            
#             # Write the image data to the framebuffer
#             with open(self.framebuffer_path, "wb") as f:
#                 f.write(img_array.tobytes())
            
#             print(f"Successfully displayed {image_path}")
#         except Exception as e:
#             print(f"Error displaying image: {e}")

# # Example usage
# if __name__ == "__main__":
#     projector = ProjectorController()
#     projector.display_image("/home/opencal/opencal/OpenCAL/hardware/water-lily-2840_4320.jpg")

# import tkinter as tk
# from PIL import Image, ImageTk

# # Get HDMI-2 screen position dynamically
# x_pos, y_pos, width, height = get_hdmi2_position()

# # Load image and resize
# image_path = "your_image.jpg"
# img = Image.open(image_path)
# img = img.resize((width, height))  # Resize to second monitor

# # Create main Tkinter window
# root = tk.Tk()
# root.withdraw()  # Hide root window

# # Create fullscreen window on HDMI-2
# window = tk.Toplevel(root)
# window.overrideredirect(True)  # Hide window borders
# window.geometry(f"{width}x{height}+{x_pos}+{y_pos}")  # Move to HDMI-2

# # Convert image to Tkinter format
# photo = ImageTk.PhotoImage(img)

# # Display image
# label = tk.Label(window, image=photo)
# label.pack()

# # Close on ESC key
# def close(event):
#     root.quit()

# window.bind("<Escape>", close)

# # Run Tkinter loop
# window.mainloop()


import subprocess
import cv2

def get_monitor_info():
    output = subprocess.run(["xrandr", "--listmonitors"], capture_output=True, text=True).stdout
    lines = output.split("\n")[1:]  # Skip first line (header)
    monitors = []
    for line in lines:
        parts = line.split()
        if len(parts) >= 4:
            resolution = parts[2].split("+")[0]  # Extract resolution before '+'
            offset = parts[2].split("+")[1:]  # Extract position
            name = parts[-1]  # Last item is monitor name
            width, height = map(int, resolution.split("/")[0].split("x"))
            x_offset = int(offset[0]) if len(offset) > 0 else 0
            y_offset = int(offset[1]) if len(offset) > 1 else 0
            monitors.append({"name": name, "width": width, "height": height, "x": x_offset, "y": y_offset})
    return monitors

monitors = get_monitor_info()
print(monitors)  # This will show all detected monitors


# Function to get HDMI-2 screen info
def get_hdmi2_position():
    monitors = get_monitor_info()
    for m in monitors:
        if "HDMI-2" in m["name"]:  # Adjust based on `xrandr` output
            return m["x"], m["y"], m["width"], m["height"]
    return 0, 0, 800, 480  # Fallback values

# Get HDMI-2 screen position
x_pos, y_pos, width, height = get_hdmi2_position()

# Load image
image = cv2.imread("your_image.jpg")
image_resized = cv2.resize(image, (width, height))

# Create a fullscreen window and move it to HDMI-2
window_name = "Display Image"
cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Move window to HDMI-2
cv2.moveWindow(window_name, x_pos, y_pos)
cv2.imshow(window_name, image_resized)

# Wait until ESC key is pressed
while True:
    if cv2.waitKey(1) == 27:  # ESC key to exit
        break

cv2.destroyAllWindows()
