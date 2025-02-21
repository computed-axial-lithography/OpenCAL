try:
    import smbus2
except ImportError:
    smbus2 = None

import time
#from this website https://circuitdigest.com/microcontroller-projects/interfacing-lcd-with-raspberry-pi-4-to-create-custom-character-and-scrolling-text
from RPLCD import *
from time import sleep
from RPLCD.i2c import CharLCD
# lcd = CharLCD('PCF8574', 0x27)
# for i in range(4):

#     lcd.cursor_pos = (i, 0)
#     lcd.write_string('Hello World')

class LCDDisplay:
    def __init__(self, address=0x27, port='PCF8574', cols=20, rows=4):
        """Initialize the LCD display.
        
        Args:
            address (int): I2C address for the LCD (default 0x27).
            port (str): Port name, typically 'PCF8574'.
            cols (int): Number of columns on the LCD.
            rows (int): Number of rows on the LCD.
        """
        self.lcd = CharLCD(port, address, cols=cols, rows=rows)

    def clear(self):
        """Clear the display."""
        self.lcd.clear()

    def write_message(self, message, row=0, col=0):
        """Write a message to a specific position on the LCD.
        
        Args:
            message (str): The message to display.
            row (int): The row on the LCD (0-indexed).
            col (int): The column on the LCD (0-indexed).
        """
        self.lcd.cursor_pos = (row, col)
        self.lcd.write_string(message)

# Test section
if __name__ == "__main__":
    lcd_display = LCDDisplay(address=0x27, port='PCF8574')
    lcd_display.clear()  # Clear the display before starting the test
    for i in range(4):
            lcd_display.lcd.cursor_pos = (i, 0)
            lcd_display.lcd.write_string('Hello World')
            sleep(1)  # Pause for 1 second between each iteration

    time.sleep(5)
    lcd_display.clear()
