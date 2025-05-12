import threading
from hardware.hardware_controller import HardwareController
from gui import LCDGui
from print_controller import PrintController

def main():
    print_controller = PrintController()
    
    # Pass print_controller to the GUI
    gui = LCDGui(print_controller)

    # Start GUI in separate thread
    gui_thread = threading.Thread(target=gui.run, daemon=True)
    gui_thread.start()

    gui_thread.join()

if __name__ == "__main__":
    main()
