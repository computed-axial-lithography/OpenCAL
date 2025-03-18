import os
# Set the ffmpeg log level to error to suppress verbose output
os.environ["IMAGEIO_FFMPEG_LOG_LEVEL"] = "error"

import pygame
import time
import sys
from moviepy.editor import VideoFileClip

# Force Pygame to open the window on the projector at (1920,0)
os.environ["SDL_VIDEO_WINDOW_POS"] = "1920,0"

# Initialize Pygame
pygame.init()

# Define projector dimensions (1920x1080)
screen_width = 1920
screen_height = 1080

# Create a borderless window on the projector
screen = pygame.display.set_mode((screen_width, screen_height), pygame.NOFRAME)
pygame.display.set_caption('Projector Video Display')

# Load the video using MoviePy with ffmpeg logging suppressed
video_path = '/home/opencal/opencal/OpenCAL/development/simulations/PEGDA700_starship_rebinned_36degps_intensity11x.mp4'
clip = VideoFileClip(video_path, ffmpeg_params=['-loglevel', 'error'])

clock = pygame.time.Clock()
start_time = time.time()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            clip.close()
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            clip.close()
            pygame.quit()
            sys.exit()

    # Calculate current playback time
    current_time = time.time() - start_time
    # Loop the video if playback is complete
    if current_time > clip.duration:
        start_time = time.time()
        current_time = 0

    # Get the current video frame (a numpy array with shape (height, width, 3))
    frame = clip.get_frame(current_time)
    # Convert the frame to a Pygame surface (swap axes because pygame.surfarray.make_surface expects (width, height, 3))
    frame_surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))

    # Blit the frame onto the screen and update the display
    screen.blit(frame_surface, (0, 0))
    pygame.display.flip()

    # Tick the clock to match the video's FPS
    clock.tick(clip.fps)
