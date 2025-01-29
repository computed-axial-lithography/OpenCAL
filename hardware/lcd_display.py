import serial
import time
import json

class LCDDisplay:
    def __init__(self, config_file="utils/config.json"): 
        """
        Initialize the LCDController with UART communication.
        :param port: UART port for communication (e.g., '/dev/serial0' for RPi).
        :param baudrate: Communication speed.
        :param timeout: Timeout for UART reads.
        """
        with open(config_file, 'r') as f:
            config = json.load(f)

        self.port = config['lcd_display'].get('port')
        self.baudrate = config['lcd_display'].get('baudrate')
        self.timeout = config['lcd_display'].get('timeout')
        self.serial_conn = None

    def start_uart(self):
        """Initialize the UART communication."""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            if self.serial_conn.isOpen():
                print("UART connection established.")
        except Exception as e:
            raise IOError(f"Failed to initialize UART: {e}")

    def send_command(self, command):
        """
        Send a raw command to the LCD.
        :param command: A byte string containing the command.
        """
        if self.serial_conn and self.serial_conn.isOpen():
            self.serial_conn.write(command)
            print(f"Sent: {command}")
        else:
            raise IOError("UART connection is not open.")

    def clear_screen(self):
        """Clear the LCD screen."""
        # Assuming 0x01 is the 'clear screen' command for your LCD.
        self.send_command(b'\x01')
        time.sleep(0.1)  # Allow the screen to clear.

    def display_image(self, image_data):
        """
        Display an image on the LCD screen.
        :param image_data: A byte string representing the image.
        """
        # For demonstration purposes, we're sending raw image data.
        # Actual implementation depends on your LCD's command set.
        self.send_command(image_data)

    def display_text(self, text):
        """
        Display text on the LCD screen.
        :param text: The text to display.
        """
        # Assuming ASCII text can be sent directly.
        self.send_command(text.encode())

    def stop_uart(self):
        """Close the UART connection."""
        if self.serial_conn and self.serial_conn.isOpen():
            self.serial_conn.close()
            print("UART connection closed.")

    def startup_sequence(self):
        """Run a startup sequence with an image or message."""
        self.clear_screen()
        self.display_text("Starting Up...")
        time.sleep(2)
        # Display a simple startup logo (replace with your image data).
        self.display_image(b'\x00\x00\xFF\xFF\x00\x00')

if __name__ == "__main__":
    lcd = LCDDisplay()
    try:
        lcd.start_uart()
        lcd.startup_sequence()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        lcd.stop_uart()
