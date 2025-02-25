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

import os
import pygame

pygame.init()

# Get number of displays and select the second one if available
num_displays = pygame.display.get_num_displays()
print('num_displays', num_displays)
if num_displays > 1:
    os.environ["SDL_VIDEO_FULLSCREEN_DISPLAY"] = "1"  # Use second display
else:
    os.environ["SDL_VIDEO_FULLSCREEN_DISPLAY"] = "0"  # Default to first display

# Open a fullscreen window on the chosen display
screen = pygame.display.set_mode((800, 480), pygame.FULLSCREEN)
pygame.display.set_caption("Auto Detect Monitor")

image = pygame.image.load("your_image.jpg")

running = True
while running:
    screen.blit(image, (0, 0))
    pygame.display.flip()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False  # Exit on ESC key

pygame.quit()
