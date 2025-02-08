import tkinter as tk
from threading import Thread


class GUIHandler:
    def __init__(self, hardware):
        self.hardware = hardware
        self.root = tk.Tk()
        self.root.title("3D Printer Control")

        # Status Label
        self.status_label = tk.Label(self.root, text="Waiting for command...", font=("Arial", 14))
        self.status_label.pack()

        # Show errors (if any)
        if self.hardware.errors:
            self.error_label = tk.Label(
                self.root, 
                text="⚠️ Errors Detected:\n" + "\n".join(self.hardware.errors), 
                fg="red"
            )
            self.error_label.pack()

        # Stepper Control Button (Enable if stepper is OK)
        self.stepper_button = tk.Button(self.root, text="Move Stepper", command=self.hardware.stepper.rotate_steps)
        self.stepper_button.pack()
        if any("Stepper" in error for error in self.hardware.errors):
            self.stepper_button.config(state=tk.DISABLED)

        # LED Toggle Button
        self.led_button = tk.Button(self.root, text="Toggle LEDs", command=self.toggle_leds)
        self.led_button.pack()
        if any("LED" in error for error in self.hardware.errors):
            self.led_button.config(state=tk.DISABLED)

        # Track LED state
        self.led_on = False

    def toggle_leds(self):
        """Toggle LEDs on/off"""
        if self.led_on:
            self.hardware.led_array.clear_leds()  # Turn off LEDs
            self.status_label.config(text="LEDs Off")
        else:
            self.hardware.led_array.set_led((255, 0, 0), [7], by_ring = True)  # Turn on LEDs
            self.status_label.config(text="LEDs On")
        
        self.led_on = not self.led_on  # Toggle state

    def run(self):
        self.root.mainloop()
