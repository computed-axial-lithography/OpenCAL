from time import sleep

from gpiozero import OutputDevice


# TODO: move to tests folder
def main():
    step_pin = 18  # Replace with your step pin number
    dir_pin = 23  # Replace with your direction pin number
    enable_pin = 27

    step = OutputDevice(step_pin)
    direction = OutputDevice(dir_pin)
    enable = OutputDevice(enable_pin)
    enable.on()

    # Set direction (CW or CCW)
    direction.on()  # CW direction
    # direction.off()  # CCW direction
    print("starting test")
    # Test motor by rotating 200 steps
    for _ in range(200):  # Adjust step count as needed
        step.on()
        sleep(0.01)  # Adjust delay to control speed
        step.off()
        sleep(0.01)
    enable.off()
    print("Test complete")


if __name__ == "__main__":
    main()
