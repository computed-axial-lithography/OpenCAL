import sys
import os
import time


# Add the parent directory of 'gui' to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hardware.hardware_controller import HardwareController

class LCDGui:
    def __init__(self, hardware=HardwareController()):
        self.hardware = hardware
        self.menu_dict = {
            "main": ['Print from USB', 'Manual Control', 'Settings'],
            "Print from USB": ['back'] + self.hardware.usb_device.get_file_names(),
            "Manual Control": ['back','Turn on LEDs', 'Turn off LEDs', 'Move Stepper', 'Display Test Image', 'Kill GUI'],
            "Move Stepper": ['back', 'start rotation', 'stop rotation'],
            "Settings": ['back', 'Set Step RPM', 'Set Some Variable'],  # Added new option for a generic variable

        }
        self.menu_callbacks = {
            'Turn on LEDs': lambda: self.hardware.led_array.set_led((255, 0, 0), set_all=True),
            'Turn off LEDs': self.hardware.led_array.clear_leds,
            'start rotation': lambda: self.hardware.stepper.start_rotation(),
            'stop rotation': lambda: self.hardware.stepper.stop(),
            'Kill GUI': lambda: self.kill_gui(),
            'Set Step RPM': lambda: self.enter_variable_adjustment("RPM", self.hardware.stepper.speed_rpm, self.hardware.stepper.set_speed),  # RPM adjustment
        }
        self.menu_stack = []  # Stack to keep track of menu navigation
        self.current_menu = 'main'  # Currently displayed menu
        self.current_index = 0  # Index of selected menu item
        self.view_start = 0  # Tracks the start of the visible menu slice
        self.view_size = 4  # Number of menu items visible at once
        self.last_rotary_position = self.hardware.rotary.get_position()
        self.last_button_press_time = 0  # For button debouncing
        self.running = True  # Flag to control the execution of the main loop
        
        self.adjusting_variable = False  # Flag to track if a variable is being adjusted
        self.current_value = 0  # The current value of the variable being adjusted
        self.variable_name = ""  # Name of the variable being adjusted
        self.update_function = None  # Function to update the variable being adjusted

    def show_startup_screen(self):
        """Display the startup screen with 'Hello User!'."""
        self.hardware.lcd.clear()
        self.hardware.lcd.write_message("Open   ".center(20), 1, 0)
        time.sleep(2)
        self.hardware.lcd.write_message("OpenCAL".center(20), 1, 0)
        time.sleep(2)  # Display for 2 seconds
        self.hardware.lcd.write_message("FOR THE COMMUNITY".center(20), 2, 0)
        time.sleep(1)

    def show_menu(self, menu):
        """Display a given menu on the LCD."""
        if menu != self.current_menu:
            self.current_index = 0
            self.current_menu = menu
            
            self.hardware.lcd.clear()  # Clear the display before showing a new menu
            menu_list = self.menu_dict.get(menu, [])
            for idx in range(len(menu_list)):
                if idx <4:
                    self.hardware.lcd.write_message(menu_list[idx], idx, 1)
            time.sleep(0.05)

    def navigate(self):
        """Handle menu navigation based on rotary encoder movement with scrolling."""
        position = self.hardware.rotary.get_position()
        menu_list = self.menu_dict[self.current_menu]
        menu_length = len(menu_list)

        # Determine movement direction
        if position > self.last_rotary_position and self.current_index < menu_length - 1:
            self.current_index += 1
        elif position < self.last_rotary_position and self.current_index > 0:
            self.current_index -= 1

        self.last_rotary_position = position  # Update last position

        # Handle scrolling logic
        if self.current_index < self.view_start:  # Scroll up
            self.view_start = self.current_index
        elif self.current_index >= self.view_start + self.view_size:  # Scroll down
            self.view_start = self.current_index - self.view_size +1

        # Display visible menu items
        for i in range(self.view_size):
            menu_idx = self.view_start + i
            if menu_idx < menu_length:
                prefix = ">" if menu_idx == self.current_index else " "
                self.hardware.lcd.write_message(f"{prefix}{menu_list[menu_idx]}".ljust(20), i, 0)

    def select_option(self):
        """Handle menu selection."""
        option = self.menu_dict.get(self.current_menu, [])[self.current_index]

        if option == "back":
            if self.menu_stack:
                self.show_menu(self.menu_stack.pop())
        
        elif option in self.menu_dict:  # If it's a submenu
            self.menu_stack.append(self.current_menu)
            self.show_menu(option)

        elif option in self.menu_callbacks:
            self.menu_callbacks[option]() 
        
        if self.adjusting_variable:
            self.adjust_variable()
        else:
            self.navigate()
        time.sleep(0.05)

    def enter_variable_adjustment(self, variable_name, current_value, update_function=None):
        """Enter variable adjustment mode and allow the user to adjust any variable."""
        self.current_menu = None
        self.variable_name = variable_name
        self.current_value = current_value  # Use the getter function to get the current value
        self.update_function = update_function  # Store the update function for setting the variable
        self.hardware.lcd.clear()
        self.hardware.lcd.write_message(f"Current {self.variable_name}: {self.current_value}", 0, 0)

        self.hardware.lcd.write_message("Use rotary to adjust", 1, 0)
        self.hardware.lcd.write_message("Click to set", 2, 0)
        
        self.adjusting_variable = True  # Set a flag indicating we're in variable adjustment mode

    def adjust_variable(self):
        """Adjust the variable using the rotary encoder."""
        position = self.hardware.rotary.get_position()

        # Increase or decrease the value based on rotary movement
        if position > self.last_rotary_position:
            self.current_value += 1  # Increase the value
        elif position < self.last_rotary_position:
            self.current_value -= 1  # Decrease the value

        # Update the displayed value on the LCD
        self.hardware.lcd.clear()
        self.hardware.lcd.write_message(f"Current {self.variable_name}: {self.current_value}", 0, 0)
        self.hardware.lcd.write_message("Use rotary to adjust", 1, 0)
        self.hardware.lcd.write_message("Click to set", 2, 0)

        self.last_rotary_position = position

    def button_press_handler(self):
        """Handles button press and debouncing."""
        current_time = time.time()
        # Only process the button press if enough time has passed since the last press (debouncing)
        if current_time - self.last_button_press_time > 0.75:  # seconds debounce time
            if self.adjusting_variable:
                # Set the variable and exit adjustment mode
                self.update_function(self.current_value)  # Set the variable using the update function
                self.adjusting_variable = False  # Exit adjustment mode
                self.show_menu('Settings')  # Return to the Settings menu after setting the variable
                self.navigate()
            else:
                self.select_option()  # Regular button press handling for other menu options
            self.last_button_press_time = current_time

    def kill_gui(self):
        """Handles the kill GUI action."""
        self.running = False  # Set running to False to stop the loop

    def run(self):
        """Main method to run the GUI."""
        self.show_startup_screen()
        
        self.show_menu('main')
        self.navigate()

        while self.running:  # Main loop will continue until self.running is False
            if self.adjusting_variable:
                # self.adjust_variable()
                self.hardware.rotary.encoder.when_rotated = self.adjust_variable  # Update the variable adjustment if in that mode
            else:
                self.hardware.rotary.encoder.when_rotated = self.navigate
            time.sleep(0.05)  # Allow time for screen updates
            
            # Button press handler, explicitly called to manage debouncing
            self.hardware.rotary.button.when_pressed = self.button_press_handler

            time.sleep(0.05)  # Prevent excessive CPU usage

        #


        # Clean up code when exiting
        time.sleep(0.5)
        self.hardware.lcd.clear()
        time.sleep(0.5)
        self.hardware.lcd.write_message("Goodbye!".center(20), 1, 0)
        time.sleep(2)  # Show "Goodbye!" for 2 seconds before exiting
        self.hardware.lcd.clear()

if __name__ == "__main__":
    gui = LCDGui()
    gui.run()