import cv2

# Load an image (replace with your actual image file path)
class Projector:
    def __init__(self, image_path = '/home/opencal/opencal/OpenCAL/hardware/water-lily-2840_4320.jpg'):
        self.image_path = image_path

        self.frame = cv2.imread(image_path)
    
    def display(self):
        # Check if the image was successfully loaded
        if self.frame is None:
            print("Error: Unable to load image.")
        else:
            # Window name
            window_name = "ImageWindow"
            
            # Create the window and display the image
            cv2.imshow(window_name, self.frame)

            # Move the window to the specified position (1920, 0)
            cv2.moveWindow(window_name, 1920, 0)

            # Wait for any key to close the window
            cv2.waitKey(0)

            # Close the window
            cv2.destroyAllWindows()

if __name__ == "__main__":
    projector = Projector()
    projector.display()
