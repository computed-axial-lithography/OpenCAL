import sys
import os

# Add the parent directory of 'gui' to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from hardware.hardware_controller import HardwareController
import time

class LCDGui:
    def __init__(self):
        self.hardware = HardwareController()
        self.row = 0

    def show_startup_screen(self):
        """Display the startup screen with 'Hello User!'."""
        self.hardware.lcd.clear()
        self.hardware.lcd.write_message("Hello User!", 0, 0)
        time.sleep(2)  # Display for 2 seconds

    def show_main_menu(self):
        """Display the main menu with 'Manual Control' option."""
        self.hardware.lcd.clear()
        self.hardware.lcd.write_message("Manual Control", 0, 1)

    def show_manual_control(self):
        """Display the manual control menu."""
        self.hardware.lcd.clear()
        self.hardware.lcd.write_message("Turn on LEDs", 0, 1)

    def handle_menu_navigation(self):
        """Navigate through the menu using the rotary encoder."""
        # Get the current position of the rotary encoder
        position = self.hardware.rotary.get_position()
        
        # Update the LCD display with the current selection
        # self.hardware.lcd.clear()
        if 0<=position<=3:
            for idx in range(4):
                if idx == position:

                    self.hardware.lcd.write_message(">",idx,0)  # Highlight the current selection
                else:

                    self.hardware.lcd.write_message(" ",idx,0)  # Highlight the current selection





    def run(self):
        """Main method to run the GUI."""
        # Show startup screen
        self.show_startup_screen()

        # Show the main menu
        self.show_main_menu()

        # Navigate and handle button press for selection
        while True:
            self.handle_menu_navigation()
            #print(self.hardware.rotary.get_position())

            # Simulate rotary rotary interaction
            time.sleep(0.1)  # Sleep for a bit to simulate rotary read cycle

            if self.hardware.rotary.was_button_pressed():  # If button is pressed
                if self.hardware.rotary.get_position() == 0: 
                    while self.hardware.rotary.was_button_pressed():  # Wait for button release
                        time.sleep(0.01) # If "Manual Control" is selected
                    self.show_manual_control()
                    
                    if self.hardware.rotary.was_button_pressed():
                        if self.hardware.rotary.get_position() == 0:
                            self.hardware.led_array.set_led((255, 0, 0), set_all = True)
                    #time.sleep(2)  # Pause for 2 seconds before next interaction

                    # Now let's simulate the LED control option (you will handle this part)
                    # Pseudocode for turning on the LEDs
                    # turn_on_leds()

                    

            # Rotate to simulate user interaction
            #self.hardware.rotary.rotate(1)  # Rotate clockwise
            # If you want to reverse, rotate(-1) for counter-clockwise navigation
            

if __name__ == "__main__":
    gui = LCDGui()
    gui.run()