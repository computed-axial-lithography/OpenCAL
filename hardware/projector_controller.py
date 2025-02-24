from PIL import Image
import numpy as np
import json

class ProjectorController:
    def __init__(self, config_file="OpenCAL/utils/config.json"):
        with open(config_file, 'r') as f:
            config = json.load(f)
        self.framebuffer_path = config['projector'].get('framebuffer_path')

    def display_image(self, image_path):
        """Loads an image and writes it to the framebuffer without resizing or manipulation."""
        try:
            # Load the image (no resizing)
            img = Image.open(image_path).convert("RGB")
            
            # Convert the image to raw bytes (8-bit per channel, 24-bit color)
            img_array = np.array(img, dtype=np.uint8)  # uint8 for 24-bit color (RGB)
            
            # Write the image data to the framebuffer
            with open(self.framebuffer_path, "wb") as f:
                f.write(img_array.tobytes())
            
            print(f"Successfully displayed {image_path}")
        except Exception as e:
            print(f"Error displaying image: {e}")

# Example usage
if __name__ == "__main__":
    projector = ProjectorController()
    projector.display_image("/home/opencal/opencal/OpenCAL/hardware/water-lily-2840_4320.jpg")
