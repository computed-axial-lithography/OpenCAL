from opencal.hardware.lcd_display import LCDDisplay
from opencal.utils.config import Config
import time

def main():
    conf = Config()
    lcd = LCDDisplay(conf.lcd_display)

    i = 0
    while True:
        i += 1
        try:
            lcd.write_message(f"{i}".rjust(20), 0)
        except OSError:
            print(f"FAILED {i}")
        time.sleep(0.2)



if __name__ == "__main__":
    main()
