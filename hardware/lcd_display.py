try:
    import smbus2
except ImportError:
    smbus2 = None

import time

class LCDDisplay:
    I2C_ADDR = 0x27  # Change if your LCD uses a different I2C address
    BACKLIGHT = 0x08
    ENABLE = 0b00000100
    LINE_ADDRESSES = [0x80, 0xC0, 0x94, 0xD4]  # DDRAM addresses for 20x4 LCD lines

    def __init__(self, bus_num=1):
        try:
            self.bus = smbus2.SMBus(bus_num)
            self.initialize()
            self.healthy = True
        except Exception as e:
            print(f"LCD Initialization Error: {e}")
            self.healthy = False

    def send_command(self, cmd):
        """Send command to LCD."""
        try:
            self.bus.write_byte(self.I2C_ADDR, cmd | self.BACKLIGHT)
            time.sleep(0.0005)
        except Exception as e:
            print(f"LCD Command Error: {e}")

    def initialize(self):
        """Initialize LCD in 4-bit mode (for 20x4 display)."""
        time.sleep(0.05)  # Allow LCD to power up
        self.send_command(0x03)
        self.send_command(0x03)
        self.send_command(0x03)
        self.send_command(0x02)  # Set to 4-bit mode

        # Function Set: 4-bit mode, 2-line mode (also supports 20x4)
        self.send_command(0x28)
        # Display ON, Cursor OFF, Blink OFF
        self.send_command(0x0C)
        # Clear Display
        self.send_command(0x01)
        time.sleep(0.002)

    def clear(self):
        """Clear the display."""
        self.send_command(0x01)
        time.sleep(0.002)

    def set_cursor(self, row, col):
        """Set cursor position (row: 0-3, col: 0-19)."""
        if 0 <= row < 4 and 0 <= col < 20:
            self.send_command(self.LINE_ADDRESSES[row] + col)

    def display_text(self, text, row=0):
        """Write text to a specific row on the LCD."""
        if not self.healthy:
            print("LCD not initialized properly.")
            return

        self.set_cursor(row, 0)  # Move to start of row

        for char in text[:20]:  # Limit to 20 characters per line
            self.bus.write_byte(self.I2C_ADDR, ord(char) | self.BACKLIGHT)
            time.sleep(0.0005)

    def close(self):
        """Cleanup and close SMBus."""
        self.bus.close()
if __name__=="__main__":
    lcd = LCDDisplay()
    try:
        lcd.display_text("Hello, World!", 0)
        time.sleep(2)
        lcd.clear()
        lcd.display_text("3D Printer Ready", 1)
        time.sleep(2)
    finally:
        lcd.close()