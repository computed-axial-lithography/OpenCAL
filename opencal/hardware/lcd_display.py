import threading
import time
from typing import final

from RPLCD.i2c import CharLCD

from opencal.utils.config import LcdDisplayConfig


@final
class LCDDisplay:
    def __init__(self, config: LcdDisplayConfig):
        self.address = int(config.address, 16)
        self.port = config.port
        self.cols = config.cols
        self.rows = config.rows

        self.lcd = CharLCD(self.port, self.address)
        self.lcd_lock = threading.Lock()
        self.framebuffer = [""] * self.rows

    def clear(self):
        """Clear the LCD display and reset the framebuffer."""
        with self.lcd_lock:
            self.lcd.clear()
        self.framebuffer = [""] * self.rows

    def write_message(self, message: str, row: int = 0, _col: int = 0):
        """Write a message to a row on the LCD, truncating if over 20 characters."""
        self.framebuffer[row] = message[: self.cols]
        self._update_lcd(row)

    def _update_lcd(self, row: int | None = None):
        with self.lcd_lock:
            try:
                if row is None:
                    self.lcd.home()
                    for i in range(self.rows):
                        self.lcd.cursor_pos = (i, 0)
                        self.lcd.write_string(self.framebuffer[i].ljust(self.cols))
                else:
                    self.lcd.cursor_pos = (row, 0)
                    self.lcd.write_string(self.framebuffer[row].ljust(self.cols))
            except IOError:
                print("ERROR: Failed to write to LCD. Retrying.")
                time.sleep(0.1)
                self._update_lcd(row)


if __name__ == "__main__":
    from opencal.utils.config import Config

    cfg = Config()
    lcd = LCDDisplay(cfg.lcd_display)
    lcd.clear()
    lcd.write_message("Static Line 1", row=0)
    lcd.write_message("This is a long line that gets cut", row=1)
    lcd.write_message("Static Line 3", row=2)
    lcd.write_message("Another long line here for row 3", row=3)
    time.sleep(5)
    lcd.clear()
