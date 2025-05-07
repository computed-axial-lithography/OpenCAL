try:
    import smbus2
except ImportError:
    smbus2 = None

import time
import json
import threading
from RPLCD.i2c import CharLCD
from time import sleep


class LCDDisplay:
    def __init__(self, config_file="OpenCAL/utils/config.json"):
        """Initialize the LCD display.
        
        Args:
            config_file (str): Path to JSON configuration file.
        """
        # Load config from the JSON file
        with open(config_file, 'r') as f:
            config = json.load(f)
            
        # Retrieve LCD settings from config
        self.address = int(config['lcd_display'].get("address", '0x27'), 16)
        self.port = config['lcd_display'].get("port", 'PCF8574')
        self.cols = config['lcd_display'].get("cols", 20)
        self.rows = config['lcd_display'].get("rows", 4)

        # Initialize the LCD
        self.lcd = CharLCD(self.port, self.address)
        
        # Create a lock for synchronized LCD access
        self.lcd_lock = threading.Lock()

        # Framebuffer stores messages for each row
        self.framebuffer = [""] * self.rows

        # Dictionary to store scrolling text (row -> text)
        self.scrolling_text = {}

        # Flag to control scrolling thread
        self.scrolling_active = True
        self.scroll_thread = threading.Thread(target=self._scrolling_loop, daemon=True)
        self.scroll_thread.start()

    def clear(self):
        """Clear the LCD display and reset buffers."""
        with self.lcd_lock:
            self.lcd.clear()
        self.framebuffer = [""] * self.rows
        self.scrolling_text = {}

    def write_message(self, message, row=0, col=0):
        """Write a message to a specific row on the LCD.
        
        - If the message is <= 20 characters, it remains static.
        - If the message is > 20 characters, it will scroll automatically.

        Args:
            message (str): The message to display.
            row (int): The row on the LCD (0-indexed).
        """
        if len(message) > self.cols:
            # Store the long message for scrolling
            self.scrolling_text[row] = message
        else:
            # Remove any old scrolling data for this row
            self.scrolling_text.pop(row, None)
            self.framebuffer[row] = message
            self._update_lcd(row)  # Only update the changed row

    def _update_lcd(self, row=None):
        """Update the LCD display.

        Args:
            row (int, optional): If provided, only update this row.
                                 If None, update all rows.
        """
        with self.lcd_lock:
            if row is None:
                self.lcd.home()
                for i in range(self.rows):
                    self.lcd.cursor_pos = (i, 0)
                    self.lcd.write_string(self.framebuffer[i].ljust(self.cols)[:self.cols])
            else:
                self.lcd.cursor_pos = (row, 0)
                self.lcd.write_string(self.framebuffer[row].ljust(self.cols)[:self.cols])

    def _scrolling_loop(self):
        """Continuously scroll long text while keeping other rows fixed."""
        while self.scrolling_active:
            # Iterate over a copy of the scrolling dictionary to avoid modification errors
            scrolling_items = list(self.scrolling_text.items())
            for row, text in scrolling_items:
                # Scroll the text across the row
                for i in range(len(text) - self.cols + 1):
                    self.framebuffer[row] = text[i:i + self.cols]
                    self._update_lcd(row)  # Only update the scrolling row
                    sleep(0.5)  # Adjust the speed of scrolling
            sleep(0.1)  # Small delay to prevent excessive looping

    def stop_scrolling(self):
        """Stop the scrolling thread."""
        self.scrolling_active = False
        self.scroll_thread.join()


# Test section
if __name__ == "__main__":
    lcd_display = LCDDisplay()
    lcd_display.clear()  # Clear display before starting

    # Display multiple lines (some static, some scrolling)
    lcd_display.write_message("Static Line 1", row=0)
    lcd_display.write_message("This is a long scrolling message on row 1!", row=1)
    lcd_display.write_message("Static Line 3", row=2)
    lcd_display.write_message("This is another long scrolling text for row 3.", row=3)

    # Keep running while scrolling occurs
    try:
        time.sleep(10)  # Allow scrolling for 10 seconds
    finally:
        lcd_display.stop_scrolling()
        lcd_display.clear()
