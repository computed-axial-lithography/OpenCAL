from PIL import Image
import numpy as np
import json

class ProjectorController:
    def __init__(self, config_file="utils/config.json"):
                 
        with open(config_file, 'r') as f:
            config = json.load(f)
        self.screen_width = config['projector'].get("screen_width")
        self.screen_height = config['projector'].get("screen_height")
        self.framebuffer_path = config['projector'].get('framebuffer_path')

    def display_image(self, image_path):
        """Loads an image, resizes it to match screen resolution, and writes it to the framebuffer."""
        try:
            # Load and resize the image
            img = Image.open(image_path).convert("RGB")
            img = img.resize((self.screen_width, self.screen_height))
            
            # Convert to raw bytes
            img_array = np.array(img, dtype=np.uint16)
            
            # Write to framebuffer
            with open(self.framebuffer_path, "wb") as f:
                f.write(img_array.tobytes())
            
            print(f"Successfully displayed {image_path}")
        except Exception as e:
            print(f"Error displaying image: {e}")

# Example usage
if __name__ == "__main__":
    projector = ProjectorController()
    projector.display_image("utils/water-lily-2840_4320.jpg")
