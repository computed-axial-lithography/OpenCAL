from opencal.hardware.stepper_controller import StepperMotor
from opencal.utils.config import Config
import time


def main():
    conf = Config()
    stepper = StepperMotor(conf.stepper)
    stepper.enable.on()

    T = 0.005

    while True:
        stepper.step.on()
        time.sleep(T)
        stepper.step.off()
        time.sleep(T)


if __name__ == "__main__":
    main()
