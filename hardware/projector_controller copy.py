import pygame
import sys
import os

# Set the DISPLAY environment variable to target HDMI-2 (adjust :0.1 if needed)
os.environ['DISPLAY'] = ':0.1'  # Assuming HDMI-2 is :0.1, change if necessary

# Initialize Pygame
pygame.init()

# Set up the screen to be full screen
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)  # 0, 0 means full screen
pygame.display.set_caption('Projector Display')

# Load an image
image = pygame.image.load('/home/opencal/opencal/OpenCAL/hardware/water-lily-2840_4320.jpg')

# Main loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Check for key press (e.g., Escape key to quit)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:  # If Esc key is pressed
                pygame.quit()
                sys.exit()

    # Display image
    screen.fill((0, 0, 0))  # Clear screen with black
    screen.blit(image, (0, 0))  # Draw image on screen

    pygame.display.flip()  # Update the screen
