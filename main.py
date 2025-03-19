from hardware.hardware_controller import HardwareController
from gui.lcd_gui import LCDGui

def startup_sequence(): 
    """Run system checks before enabling the GUI."""
    print("System Starting Up...")
    hardware = HardwareController()

    #hardware.communication_check()  # Verify hardware comms
    return hardware

def main():
    """Main execution loop handling hardware & GUI interactions."""
    hardware = startup_sequence()  # Run startup checks
    
    gui = LCDGui()  # Pass hardware to GUI
    gui.run()  # Start GUI loop

    

if __name__ == "__main__":
    main()

