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
            "Print from USB": ['back', 'idk yet'],
            "Manual Control": ['back','Turn on LEDs', 'Turn off LEDs', 'Move Stepper'],
            "Move Stepper": ['back', 'Rotate CW', 'Rotate CCW'],
            "Settings": ['back', 'set opt 1', 'set opt 2'],
        }
        self.menu_callbacks = {
            'Turn on LEDs': lambda: self.hardware.led_array.set_led((255, 0, 0), set_all=True),
            'Turn off LEDs': self.hardware.led_array.clear_leds,
            'Rotate CW': lambda: self.hardware.stepper.rotate_steps(100),
            'Rotate CCW': lambda: self.hardware.stepper.rotate_steps(-100),
        }
        self.menu_stack = []  # Stack to keep track of menu navigation
        self.current_menu = 'main'  # Currently displayed menu
        self.current_index = 0  # Index of selected menu item
        self.view_start = 0  # Tracks the start of the visible menu slice
        self.view_size = 4  # Number of menu items visible at once
        self.last_rotary_position = self.hardware.rotary.get_position()
        self.last_button_press_time = 0  # For button debouncing

    def show_startup_screen(self):
        """Display the startup screen with 'Hello User!'."""
        self.hardware.lcd.clear()
        self.hardware.lcd.write_message("For", 1, 8)
        self.hardware.lcd.write_message("The Community", 2, 3)
        time.sleep(2)  # Display for 5 seconds

    def show_menu(self, menu):
        """Display a given menu on the LCD."""
        if menu != self.current_menu:
            self.current_index = 0
            self.current_menu = menu
            
            self.hardware.lcd.clear()  # Clear the display before showing a new menu
            menu_list = self.menu_dict.get(menu, [])
            for idx in range(len(menu_list)):
                self.hardware.lcd.write_message(menu_list[idx], idx, 1)
            time.sleep(0.1)

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
            self.view_start = self.current_index - self.view_size + 1

        # Display visible menu items
        for i in range(self.view_size):
            menu_idx = self.view_start + i
            if menu_idx < menu_length:
                prefix = ">" if menu_idx == self.current_index else " "
                self.hardware.lcd.write_message(f"{prefix}{menu_list[menu_idx]}", i, 0)

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

        self.navigate()
        time.sleep(0.5)

    def button_press_handler(self):
        """Handles button press and debouncing."""
        current_time = time.time()
        # Only process the button press if enough time has passed since the last press (debouncing)
        if current_time - self.last_button_press_time > 1:  # seconds debounce time
            self.select_option()
            self.last_button_press_time = current_time

    def run(self):
        """Main method to run the GUI."""
        self.show_startup_screen()
        
        self.show_menu('main')
        self.navigate()

        while True:
            self.hardware.rotary.encoder.when_rotated = self.navigate
            #self.navigate()  # Update the screen based on rotary input
            time.sleep(0.1)  # Allow time for screen updates
            
            # Button press handler, explicitly called to manage debouncing
            self.hardware.rotary.button.when_pressed = self.button_press_handler

            time.sleep(0.1)  # Prevent excessive CPU usage

if __name__ == "__main__":
    gui = LCDGui()
    gui.run()