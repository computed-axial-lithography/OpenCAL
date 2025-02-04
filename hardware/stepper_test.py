from gpiozero import OutputDevice
from time import sleep

step_pin = 18  # Replace with your step pin number
dir_pin = 23   # Replace with your direction pin number

step = OutputDevice(step_pin)
direction = OutputDevice(dir_pin)

# Set direction (CW or CCW)
direction.on()  # CW direction
# direction.off()  # CCW direction

# Test motor by rotating 200 steps
for _ in range(200):  # Adjust step count as needed
    step.on()
    sleep(0.01)  # Adjust delay to control speed
    step.off()
    sleep(0.01)

print("Test complete")
