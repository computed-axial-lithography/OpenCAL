try:
    import smbus2
except ImportError:
    smbus2 = None

import time
#from this website https://circuitdigest.com/microcontroller-projects/interfacing-lcd-with-raspberry-pi-4-to-create-custom-character-and-scrolling-text
from RPLCD import *
from time import sleep
from RPLCD.i2c import CharLCD
import json


class LCDDisplay:
    def __init__(self, config_file="/home/opencal/opencal/OpenCAL/utils/config.json"):
        """Initialize the LCD display.
        
        Args:
            address (int): I2C address for the LCD (default 0x27).
            port (str): Port name, typically 'PCF8574'.
            cols (int): Number of columns on the LCD.
            rows (int): Number of rows on the LCD.
        """
        # Load config from the JSON file
        with open(config_file, 'r') as f:
            config = json.load(f)
        # Retrieve the address and port from config, or use defaults
        self.address = int(config['lcd_display'].get("address", '0x27'),16)
        self.port = config['lcd_display'].get("port", 'PCF8574')
        self.cols = config['lcd_display'].get("cols", 20)
        self.rows = config['lcd_display'].get("rows", 4)

        # Initialize the LCD display
        self.lcd = CharLCD(self.port, self.address)

        # Framebuffer for display content
        self.framebuffer = ["", ""]

    def clear(self):
        """Clear the display."""
        self.lcd.clear()

    def write_message(self, message, row=0, col=0):
        """Write a message to a specific position on the LCD.
        
        If the message is longer than 20 characters, it will automatically scroll.
        Args:
            message (str): The message to display.
            row (int): The row on the LCD (0-indexed).
            col (int): The column on the LCD (0-indexed).
        """
        if len(message) > self.cols:
            # If the message is too long, scroll it automatically
            self.long_text(message, row)
        else:
            # Otherwise, write normally
            self.lcd.cursor_pos = (row, col)
            self.lcd.write_string(message.ljust(self.cols)[:self.cols])

    def write_to_lcd(self):
        """Write the framebuffer out to the lcd."""
        self.lcd.home()
        for row in self.framebuffer:
            self.lcd.write_string(row.ljust(self.cols)[:self.cols])
            self.lcd.write_string('\r\n')
    def long_text(self, text):
        """Scroll a long text string across the second row of the LCD.
        Args:
            text (str): The text string to display.
        """
        if len(text) < self.cols:
            self.write_message(text, row=1)
        else:
            for i in range(len(text) - self.cols + 1):
                self.framebuffer[1] = text[i:i + self.cols]
                self.write_to_lcd()
                sleep(0.5)  # Adjust scrolling speed


# Test section
if __name__ == "__main__":
    lcd_display = LCDDisplay()
    lcd_display.clear()  # Clear the display before starting the test
    
    # Short message test (normal display)
    lcd_display.write_message("Hello, World!", row=0)

    # Long message test (auto-scroll on row 1)
    time.sleep(2)
    lcd_display.write_message("This is a scrolling message on an LCD display!", row=1)

    time.sleep(5)
    lcd_display.clear()