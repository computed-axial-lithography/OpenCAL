import sys
import os
import subprocess
import time


# Add the parent directory of 'gui' to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hardware.hardware_controller import HardwareController

class LCDGui:
    def __init__(self, hardware=HardwareController()):
        from main import PrintController
        pc = PrintController()
        self.hardware = hardware
        self.print_controller = PrintController
        self.menu_dict = {
            "main": ['Print from USB', 'Manual Control', 'Settings', 'Power Options'],
            # The "Print from USB" menu now lists files from the USB device.
            "Print from USB": ['back'] + self.hardware.usb_device.get_file_names(),
            "Manual Control": ['back', 'Turn on LEDs', 'Turn off LEDs', 'Move Stepper', 'Display Test Image', 'Kill GUI'],
            "Move Stepper": ['back', 'start rotation', 'stop rotation'],
            "Settings": ['back', 'Set Step RPM', 'Set Some Variable'],  # Options for adjusting variables
            "Power Options": ['back', 'Restart', 'Power Off'],  # Power options submenu
        }
        self.menu_callbacks = {
            'Turn on LEDs': lambda: self.hardware.led_array.set_led((255, 0, 0), set_all=True),
            'Turn off LEDs': self.hardware.led_array.clear_leds,
            'start rotation': lambda: self.hardware.stepper.start_rotation(),
            'stop rotation': lambda: self.hardware.stepper.stop(),
            'Kill GUI': lambda: self.kill_gui(),
            'Set Step RPM': lambda: self.enter_variable_adjustment("RPM", self.hardware.stepper.speed_rpm, self.hardware.stepper.set_speed),
            'Restart': lambda: self.restart_pi(),
            'Power Off': lambda: self.power_off_pi(),
        }
        self.menu_stack = []  # Stack to keep track of menu navigation
        self.current_menu = 'main'  # Currently displayed menu
        self.current_index = 0  # Index of selected menu item
        self.view_start = 0  # Tracks the start of the visible menu slice
        self.view_size = 4  # Number of menu items visible at once

        # Check if rotary exists before calling its get_position method.
        if self.hardware.rotary is not None:
            self.last_rotary_position = self.hardware.rotary.get_position()
        else:
            self.last_rotary_position = 0

        self.last_button_press_time = 0  # For button debouncing
        self.running = True  # Flag to control the execution of the main loop

        self.adjusting_variable = False  # Flag to track if a variable is being adjusted
        self.current_value = 0  # The current value of the variable being adjusted
        self.variable_name = ""  # Name of the variable being adjusted

        # For our two-stage process:
        self.selected_video_filename = None
        self.adjustment_callback = None  # To call after variable adjustment

    def show_startup_screen(self):
        """Display the startup screen with 'Hello User!'."""
        self.hardware.lcd.clear()
        self.hardware.lcd.write_message("Open   ".center(20), 1, 0)
        time.sleep(1)
        self.hardware.lcd.write_message("    CAL".center(20), 1, 0)
        time.sleep(1)
        self.hardware.lcd.write_message("OpenCAL".center(20), 1, 0)
        time.sleep(2)
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
                if idx < 4:
                    self.hardware.lcd.write_message(menu_list[idx], idx, 1)
            time.sleep(0.05)

    def navigate(self):
        """Handle menu navigation based on rotary encoder movement with scrolling."""
        if self.hardware.rotary is not None:
            position = self.hardware.rotary.get_position()
        else:
            position = self.last_rotary_position

        menu_list = self.menu_dict[self.current_menu]
        menu_length = len(menu_list)

        if position > self.last_rotary_position and self.current_index < menu_length - 1:
            self.current_index += 1
        elif position < self.last_rotary_position and self.current_index > 0:
            self.current_index -= 1

        self.last_rotary_position = position

        if self.current_index < self.view_start:
            self.view_start = self.current_index
        elif self.current_index >= self.view_start + self.view_size:
            self.view_start = self.current_index - self.view_size + 1

        for i in range(self.view_size):
            menu_idx = self.view_start + i
            if menu_idx < menu_length:
                prefix = ">" if menu_idx == self.current_index else " "
                self.hardware.lcd.write_message(f"{prefix}{menu_list[menu_idx]}".ljust(20), i, 0)

    def select_option(self):
        """Handle menu selection."""
        option = self.menu_dict.get(self.current_menu, [])[self.current_index]

        if self.current_menu == "Step RPM Prompt":
            if option == "Manual Step RPM":
                self.enter_variable_adjustment("RPM", self.hardware.stepper.speed_rpm, self.hardware.stepper.set_speed,
                                                callback=self.send_video_after_rpm_adjustment)
            else:  # Covers "Standard RPM"
                self.send_video_after_rpm_adjustment()
            return

        if option == "back":
            if self.menu_stack:
                self.show_menu(self.menu_stack.pop())
            else:
                self.show_menu("main")
        elif option in self.menu_dict:
            self.menu_stack.append(self.current_menu)
            self.show_menu(option)
        elif option in self.menu_callbacks:
            self.menu_callbacks[option]()
        elif self.current_menu == "Print from USB":
            self.selected_video_filename = option
            self.prompt_manual_step_rpm()
            return  # Return immediately so the prompt is shown and waits for user input.

        if self.adjusting_variable:
            self.adjust_variable()
        else:
            self.navigate()
        time.sleep(0.05)

    def prompt_manual_step_rpm(self):
        self.menu_dict["Step RPM Prompt"] = ["Manual Step RPM", "Standard RPM"]
        self.show_menu("Step RPM Prompt")
        self.navigate()
        # Wait briefly before accepting further input
        time.sleep(1)



    def send_video_after_rpm_adjustment(self):
        """
        Called after the user has chosen the RPM option (and finished any adjustment).
        This method sends the video file to the projector.
        """
        self.hardware.lcd.clear()
        self.hardware.lcd.write_message("Sending Video...", 0, 0)
        try:
            self.hardware.projector.play_video(self.selected_video_filename)
            self.hardware.lcd.write_message("Video Playing", 1, 0)
        except Exception as e:
            self.hardware.lcd.write_message("Error Playing Video", 1, 0)
            print("Error sending video to projector:", e)
        time.sleep(2)
        self.show_menu("main")

    def enter_variable_adjustment(self, variable_name, current_value, update_function=None, callback=None):
        """Enter variable adjustment mode and allow the user to adjust any variable.
           A callback (if provided) is stored and called after the adjustment is complete.
        """
        self.current_menu = None
        self.variable_name = variable_name
        self.current_value = current_value
        self.update_function = update_function
        self.adjustment_callback = callback
        self.hardware.lcd.clear()
        self.hardware.lcd.write_message(f"Current {self.variable_name}: {self.current_value}", 0, 0)
        self.hardware.lcd.write_message("Use rotary to adjust", 1, 0)
        self.hardware.lcd.write_message("Click to set", 2, 0)
        self.adjusting_variable = True

    def adjust_variable(self):
        """Adjust the variable using the rotary encoder."""
        if self.hardware.rotary is not None:
            position = self.hardware.rotary.get_position()
        else:
            position = self.last_rotary_position

        if position > self.last_rotary_position:
            self.current_value += 1
        elif position < self.last_rotary_position:
            self.current_value -= 1

        self.hardware.lcd.clear()
        self.hardware.lcd.write_message(f"Current {self.variable_name}: {self.current_value}", 0, 0)
        self.hardware.lcd.write_message("Use rotary to adjust", 1, 0)
        self.hardware.lcd.write_message("Click to set", 2, 0)
        self.last_rotary_position = position

    def button_press_handler(self):
        """Handles button press and debouncing."""
        current_time = time.time()
        if current_time - self.last_button_press_time > 0.75:
            if self.adjusting_variable:
                self.update_function(self.current_value)
                self.adjusting_variable = False
                if self.adjustment_callback:
                    self.adjustment_callback()
                    self.adjustment_callback = None
                else:
                    self.show_menu('Settings')
                    self.navigate()
            else:
                self.select_option()
            self.last_button_press_time = current_time

    def restart_pi(self):
        """Restart the Raspberry Pi."""
        self.hardware.lcd.clear()
        self.hardware.lcd.write_message("Restarting...", 1, 0)
        time.sleep(2)
        os.system("sudo reboot")
        result = subprocess.run(["sudo", "reboot"], capture_output=True)
        if result.returncode != 0:
            print("fail!")

    def power_off_pi(self):
        """Power off the Raspberry Pi."""
        self.hardware.lcd.clear()
        self.hardware.lcd.write_message("Powering Off...", 1, 0)
        time.sleep(2)
        os.system("sudo poweroff")

    def kill_gui(self):
        """Handles the kill GUI action."""
        self.running = False

    def run(self):
        """Main method to run the GUI."""
        self.show_startup_screen()
        self.show_menu('main')
        self.navigate()

        while self.running:
            if self.hardware.rotary is not None:
                if self.adjusting_variable:
                    self.hardware.rotary.encoder.when_rotated = self.adjust_variable
                else:
                    self.hardware.rotary.encoder.when_rotated = self.navigate
                self.hardware.rotary.button.when_pressed = self.button_press_handler
            time.sleep(0.05)

        time.sleep(0.5)
        self.hardware.lcd.clear()
        time.sleep(0.5)
        self.hardware.lcd.write_message("Goodbye!".center(20), 1, 0)
        time.sleep(2)
        self.hardware.lcd.clear()

        
if __name__ == "__main__":
    try:
        gui = LCDGui()
        gui.run()
    except KeyboardInterrupt:
        print("KeyboardInterrupt caught. Exiting gracefully.")
        gui.hardware.lcd.clear()
        sys.exit(0)

