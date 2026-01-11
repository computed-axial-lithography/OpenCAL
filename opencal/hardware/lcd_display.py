
import time
import threading
from typing import final
from RPLCD.i2c import CharLCD
from time import sleep

from opencal.utils.config import LcdDisplayConfig


@final
class LCDDisplay:
    def __init__(self, config: LcdDisplayConfig):
        """Initialize the LCD display.
        
        Args:
            config_file (str): Path to JSON configuration file.
        """
        # Retrieve LCD settings from config
        self.address = int(config.address, 16)
        self.port = config.port
        self.cols = config.cols
        self.rows = config.rows

        # Initialize the LCD
        self.lcd = CharLCD(self.port, self.address)
        
        # Create a lock for synchronized LCD access
        self.lcd_lock = threading.Lock()

        # Framebuffer stores messages for each row
        self.framebuffer = [""] * self.rows

        # Dictionary to store scrolling text (row -> text)
        # TODO: should this be list[str]? 
        self.scrolling_text: dict[int, str] = {}

        # Flag to control scrolling thread
        self.scrolling_active = True
        self.scroll_thread = threading.Thread(target=self._scrolling_loop, daemon=True)
        self.scroll_thread.start()  # Start the scrolling thread

    def clear(self):
        """Clear the LCD display and reset buffers."""
        with self.lcd_lock:
            self.lcd.clear()  # Clear the LCD display
        self.framebuffer = [""] * self.rows  # Reset the framebuffer
        self.scrolling_text = {}  # Clear any scrolling text

    def write_message(self, message: str, row: int = 0, _col: int = 0):
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
            _ = self.scrolling_text.pop(row, None)
            self.framebuffer[row] = message  # Update the framebuffer with the new message
            self._update_lcd(row)  # Only update the changed row

    def _update_lcd(self, row: int | None = None):
        """Update the LCD display.

        Args:
            row (int, optional): If provided, only update this row.
                                 If None, update all rows.
        """
        with self.lcd_lock:
            if row is None:
                self.lcd.home()  # Move cursor to home position
                for i in range(self.rows):
                    self.lcd.cursor_pos = (i, 0)  # Set cursor position for each row
                    self.lcd.write_string(self.framebuffer[i].ljust(self.cols)[:self.cols])  # Write the message  # pyright: ignore[reportUnknownMemberType]
            else:
                self.lcd.cursor_pos = (row, 0)  # Set cursor position for the specified row
                self.lcd.write_string(self.framebuffer[row].ljust(self.cols)[:self.cols])  # Write the message  # pyright: ignore[reportUnknownMemberType]

    def _scrolling_loop(self):
        """Continuously scroll long text while keeping other rows fixed."""
        # TODO: sleeping in this function is suspicious
        while self.scrolling_active:
            # Iterate over a copy of the scrolling dictionary to avoid modification errors
            scrolling_items = list(self.scrolling_text.items())
            for row, text in scrolling_items:
                # Scroll the text across the row
                for i in range(len(text) - self.cols + 1):
                    self.framebuffer[row] = text[i:i + self.cols]  # Update the framebuffer with the scrolling text
                    self._update_lcd(row)  # Only update the scrolling row
                    sleep(0.5)  # Adjust the speed of scrolling
            sleep(0.1)  # Small delay to prevent excessive looping

    def stop_scrolling(self):
        """Stop the scrolling thread."""
        self.scrolling_active = False  # Set the flag to stop scrolling
        self.scroll_thread.join()  # Wait for the scrolling thread to finish


# Test section
if __name__ == "__main__":
    from opencal.utils.config import Config
    cfg = Config()
    lcd_display = LCDDisplay(cfg.lcd_display)  # Create an instance of the LCDDisplay class
    lcd_display.clear()  # Clear display before starting

    # Display multiple lines (some static, some scrolling)
    lcd_display.write_message("Static Line 1", row=0)  # Write a static message
    lcd_display.write_message("This is a long scrolling message on row 1!", row=1)  # Write a long message for scrolling
    lcd_display.write_message("Static Line 3", row=2)  # Write another static message
    lcd_display.write_message("This is another long scrolling text for row 3.", row=3)  # Another long message for scrolling

    # Keep running while scrolling occurs
    try:
        time.sleep(10)  # Allow scrolling for 10 seconds
    finally:
        lcd_display.stop_scrolling()  # Stop the scrolling thread
        lcd_display.clear()  # Clear the display after the test
