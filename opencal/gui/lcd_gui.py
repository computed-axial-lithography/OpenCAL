import json
import os
import subprocess
import sys
import time

import cv2

from opencal.hardware import PrintController

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../utils/config.json")


# Add the parent directory of 'gui' to sys.path
# TODO: This is probably unnecessary
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# from hardware import HardwareController


class LCDGui:
    def __init__(self, pc=None):
        if pc is None:
            pc = PrintController()
        self.pc = pc
        self.print_start_time = None

        self.menu_dict = {
            "main": ["Print from USB", "Manual Control", "Settings", "Power Options"],
            "Print from USB": ["back"] + self.pc.hardware.usb_device.get_file_names(),
            "Manual Control": [
                "back",
                "Turn on LEDs",
                "Turn off LEDs",
                "start stepper",
                "stop stepper",
            ],
            "Settings": [
                "back",
                "save as default",
                "Resize Print",
                "Set Step RPM",
                "Calibration img",
                "change camera",
            ],  # Options for adjusting variables
            "Power Options": [
                "back",
                "Kill GUI",
            ],  #'Restart', 'Power Off'],  # Power options submenu
            "Print menu": ["stop"],
            "calibration": ["stop"],
            "change camera": ["back", "rpi", "usb"],
        }
        self.menu_callbacks = {
            "Turn on LEDs": lambda: self.pc.hardware.led_array.set_led(
                (255, 0, 0), set_all=True
            ),
            "Turn off LEDs": self.pc.hardware.led_array.clear_leds,
            "start stepper": lambda: self.pc.hardware.stepper.start_rotation(),
            "stop stepper": lambda: self.pc.hardware.stepper.stop(),
            "Kill GUI": lambda: self.kill_gui(),
            "Set Step RPM": lambda: self.enter_variable_adjustment(
                "RPM",
                self.pc.hardware.stepper.speed_rpm,
                self.pc.hardware.stepper.set_speed,
            ),
            "Restart": lambda: self.restart_pi(),
            "Power Off": lambda: self.power_off_pi(),
            "print": lambda arg: self.pc.start_print_job(
                arg
            ),  # Start print job, camera handling is now in PrintController
            "stop": lambda: (
                self.pc.stop(),
                self.clear_timer(),
                self.show_menu("main"),
            ),
            "Resize Print": lambda: self.enter_variable_adjustment(
                "size %",
                self.pc.hardware.projector.size,
                self.pc.hardware.projector.resize,
            ),  # Resize Print option callback
            "Calibration img": lambda: (
                self.pc.hardware.projector.display_image(),
                self.show_menu("calibration"),
            ),
            "usb": lambda: (
                self.pc.hardware.camera.set_type("usb"),
                self.splash("usb camera", self.current_menu),
            ),
            "rpi": lambda: (
                self.pc.hardware.camera.set_type("rpi"),
                self.splash("rpi camera", self.current_menu),
            ),
            "save to default": lambda: (self.save_defaults()),
        }

        self.menu_stack = []  # Stack to keep track of menu navigation
        self.current_menu = "main"  # Currently displayed menu
        self.return_menu = "main"
        self.current_index = 0  # Index of selected menu item
        self.view_start = 0  # Tracks the start of the visible menu slice
        self.view_size = 4  # Number of menu items visible at once

        # Check if rotary exists before calling its get_position method.
        if self.pc.hardware.rotary is not None:
            self.last_rotary_position = self.pc.hardware.rotary.get_position()
        else:
            self.last_rotary_position = 0

        self.last_button_press_time = 0  # For button debouncing
        self.running = True  # Flag to control the execution of the main loop

        self.adjusting_variable = False  # Flag to track if a variable is being adjusted
        self.current_value = 0  # The current value of the variable being adjusted
        self.variable_name = ""  # Name of the variable being adjusted

        # For our two-stage process:
        self.selected_video_filename = None
        self.video_filename_short = None

    def clear_timer(self):
        # Reset the timer attribute
        self.print_start_time = None
        # Clear the line used for displaying elapsed time (line 3)
        self.pc.hardware.lcd.write_message(" " * 20, 3, 0)

    def show_startup_screen(self):
        """Display the startup screen with 'Hello User!'."""
        self.pc.hardware.lcd.clear()
        self.pc.hardware.lcd.write_message("Open   ".center(20), 1, 0)
        time.sleep(1)
        self.pc.hardware.lcd.write_message("OpenCAL".center(20), 1, 0)
        time.sleep(2)
        self.pc.hardware.lcd.write_message("FOR THE COMMUNITY".center(20), 2, 0)
        time.sleep(1)

    def show_menu(self, menu):
        """Display a given menu on the LCD."""
        if menu != self.current_menu:
            self.current_index = 0
            self.current_menu = menu
            self.pc.hardware.lcd.clear()  # Clear the display before showing a new menu
            menu_list = self.menu_dict.get(menu, [])
            for idx in range(len(menu_list)):
                if idx < 4:
                    self.pc.hardware.lcd.write_message(menu_list[idx], idx, 1)
            time.sleep(0.05)

    def save_defaults(self):
        """
        Read the existing config.json (or start with an empty one),
        overwrite the three keys we care about, and write it back out.
        """
        # 1) load whatever’s there already (or start fresh)
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                cfg = json.load(f)
        else:
            cfg = {}

        cfg["stepper_motor"]["default_speed"] = self.pc.hardware.stepper.speed_rpm

        cfg["projector"]["default_print_size"] = self.pc.hardware.projector.size

        cfg["camera"]["type"] = self.pc.hardware.camera.cam_type

        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(cfg, f, indent=2)
        except Exception as e:
            print(f"Error saving defaults: {e}")
            return

        self.splash("Defaults saved!", self.current_menu, 1.2)

    def splash(self, message="Saved", next_menu="main", duration=1.0):
        """
        Show a one-off message centered on the LCD, wait 'duration' seconds,
        then display 'next_menu'.
        """
        # 1) clear the display
        self.pc.hardware.lcd.clear()
        # 2) write the message centered on line 1 (you can tweak line/col if you want)
        centered = message.center(20)
        self.pc.hardware.lcd.write_message(centered, 1, 0)
        # 3) hold for a bit
        time.sleep(duration)

    def navigate(self):
        """Handle menu navigation based on rotary encoder movement with scrolling."""
        if self.pc.hardware.rotary is not None:
            position = self.pc.hardware.rotary.get_position()
        else:
            position = self.last_rotary_position

        menu_list = self.menu_dict[self.current_menu]
        menu_length = len(menu_list)

        if (
            position > self.last_rotary_position
            and self.current_index < menu_length - 1
        ):
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
                self.pc.hardware.lcd.write_message(
                    f"{prefix}{menu_list[menu_idx]}".ljust(20), i, 0
                )

    def select_option(self):
        """Handle menu selection."""
        option = self.menu_dict.get(self.current_menu, [])[self.current_index]

        if option == "back":
            if self.menu_stack:
                self.show_menu(self.menu_stack.pop())
            else:
                self.show_menu("main")
        elif option in self.menu_dict:
            self.menu_dict["Print from USB"] = [
                "back"
            ] + self.pc.hardware.usb_device.get_file_names()
            self.menu_stack.append(self.current_menu)
            self.show_menu(option)
        elif option in self.menu_callbacks:
            self.menu_callbacks[option]()
        elif self.current_menu == "Print from USB":
            self.video_filename_short = option
            self.selected_video_filename = self.pc.hardware.usb_device.get_full_path(
                option
            )
            self.enter_variable_adjustment(
                "RPM",
                self.pc.hardware.stepper.speed_rpm,
                self.pc.hardware.stepper.set_speed,
            )

        if self.adjusting_variable:
            self.adjust_variable()
        else:
            self.navigate()
        time.sleep(0.05)

    def enter_variable_adjustment(
        self, variable_name, current_value, update_function=None
    ):
        """Enter variable adjustment mode and allow the user to adjust any variable.
        A callback (if provided) is stored and called after the adjustment is complete.
        """
        self.return_menu = self.current_menu
        self.current_menu = None
        self.variable_name = variable_name
        self.current_value = current_value
        self.update_function = update_function
        self.pc.hardware.lcd.clear()
        self.pc.hardware.lcd.write_message(
            f"Current {self.variable_name}: {self.current_value}".ljust(20), 0, 0
        )
        self.pc.hardware.lcd.write_message("Use rotary to adjust", 1, 0)
        self.pc.hardware.lcd.write_message("Click to set", 2, 0)
        self.adjusting_variable = True

    def adjust_variable(self):
        """Adjust the variable using the rotary encoder."""
        position = self.pc.hardware.rotary.get_position()

        if position > self.last_rotary_position:
            self.current_value += 1
            print(self.current_value)
        elif position < self.last_rotary_position:
            print(self.current_value)
            if self.variable_name == "size %" and self.current_value <= 100:
                self.pc.hardware.lcd.write_message("Cannot go below 100", 3, 0)
                self.last_rotary_position = position
                return
            else:
                self.current_value -= 1

        # self.pc.hardware.lcd.clear()
        self.pc.hardware.lcd.write_message(
            f"Current {self.variable_name}: {self.current_value}".ljust(20), 0, 0
        )
        # self.pc.hardware.lcd.write_message("Use rotary to adjust", 1, 0)
        # self.pc.hardware.lcd.write_message("Click to set", 2, 0)
        if self.selected_video_filename is not None:
            self.pc.hardware.lcd.write_message(self.video_filename_short, 3, 0)
        self.last_rotary_position = position

    def button_press_handler(self):
        """Handles button press and debouncing."""
        current_time = time.time()
        if current_time - self.last_button_press_time > 1:
            if self.adjusting_variable and self.selected_video_filename is None:
                self.update_function(self.current_value)
                self.adjusting_variable = False
                self.show_menu(self.return_menu)
                self.navigate()

            elif self.selected_video_filename is not None:
                self.update_function(self.current_value)
                self.adjusting_variable = False
                self.print_start_time = time.time()
                self.menu_callbacks["print"](self.selected_video_filename)
                self.selected_video_filename = None
                self.video_filename_short = None
                self.show_menu(
                    "Print menu"
                )  # Switch to print menu after starting the print job\
                self.navigate()
            else:
                self.select_option()
            self.last_button_press_time = current_time

    def restart_pi(self):
        """Restart the Raspberry Pi."""
        self.pc.hardware.lcd.clear()
        self.pc.hardware.lcd.write_message("Restarting...", 1, 0)
        time.sleep(2)
        os.system("sudo reboot")
        result = subprocess.run(["sudo", "reboot"], capture_output=True)
        if result.returncode != 0:
            print("fail!")

    def power_off_pi(self):
        """Power off the Raspberry Pi."""
        self.pc.hardware.lcd.clear()
        self.pc.hardware.lcd.write_message("Powering Off...", 1, 0)
        time.sleep(2)
        os.system("sudo poweroff")

    def kill_gui(self):
        """Handles the kill GUI action."""
        # self.camera.stop_camera()
        cv2.destroyAllWindows()
        self.running = False

    def run(self):
        """Main method to run the GUI."""
        self.show_startup_screen()
        self.show_menu("main")
        self.navigate()

        while self.running:
            if self.print_start_time is not None:
                elapsed = time.time() - self.print_start_time
                # Format the elapsed time (e.g., minutes and seconds)
                minutes, seconds = divmod(int(elapsed), 60)
                elapsed_formatted = f"{minutes:02d}:{seconds:02d}"
                # Write the elapsed time to a fixed line on the LCD (line 3)
                self.pc.hardware.lcd.write_message(
                    f"Elapsed: {elapsed_formatted}", 3, 0
                )
            if self.adjusting_variable:
                self.pc.hardware.rotary.encoder.when_rotated = self.adjust_variable
            else:
                self.pc.hardware.rotary.encoder.when_rotated = self.navigate
            self.pc.hardware.rotary.button.when_pressed = self.button_press_handler
            time.sleep(0.05)

        time.sleep(0.5)
        self.pc.hardware.lcd.clear()
        time.sleep(0.5)
        self.pc.hardware.lcd.write_message("Goodbye!".center(20), 1, 0)
        time.sleep(2)
        self.pc.hardware.lcd.clear()


if __name__ == "__main__":
    gui = LCDGui()
    gui.run()
