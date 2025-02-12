import time
from threading import Thread
import RPi.GPIO as GPIO
from lcd_driver import LCD
from rotary_encoder import RotaryEncoder

class LCDGUI:
    def __init__(self, lcd, encoder):
        self.lcd = lcd
        self.encoder = encoder
        
        self.menu = {
            "Print from USB": self.print_from_usb,
            "Settings": {"Rotation Speed": None, "LED Brightness": None},
            "Setup": {"Control Devices": None}
        }
        self.menu_stack = [list(self.menu.keys())]
        self.selected_index = 0
        
        self.encoder.set_callback(self.handle_encoder)
        self.encoder.set_select_callback(self.handle_select)
        
        self.running = True
        Thread(target=self.update_display, daemon=True).start()
    
    def update_display(self):
        while self.running:
            menu_items = self.menu_stack[-1]
            self.lcd.write(menu_items[self.selected_index], 1)
            time.sleep(0.1)
    
    def handle_encoder(self, direction):
        if direction == "CW":
            self.selected_index = (self.selected_index + 1) % len(self.menu_stack[-1])
        else:
            self.selected_index = (self.selected_index - 1) % len(self.menu_stack[-1])
    
    def handle_select(self):
        selected_item = self.menu_stack[-1][self.selected_index]
        
        if isinstance(self.menu[selected_item], dict):
            self.menu_stack.append(list(self.menu[selected_item].keys()))
            self.selected_index = 0
        elif callable(self.menu[selected_item]):
            self.menu[selected_item]()
        
    def print_from_usb(self):
        self.lcd.write("Printing from USB...", 1)
        time.sleep(2)
        self.lcd.write("Done!", 1)
    
    def cleanup(self):
        self.running = False
        self.encoder.cleanup()

if __name__ == "__main__":
    lcd = LCD()
    encoder = RotaryEncoder()
    gui = LCDGUI(lcd, encoder)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        gui.cleanup()
