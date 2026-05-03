# from opencal.hardware.stepper_controller import StepperMotor
from opencal.hardware.stepper import create_stepper
from opencal.utils.config import load_config
# from opencal.utils.config import Config
import time

from TMC2209_PY import UART, TMC2209Configure


def main():
    # conf = Config()
    # stepper = StepperMotor(conf.stepper)
    # stepper.enable.on()
    #
    # T = 0.005
    #
    # while True:
    #     stepper.step.on()
    #     time.sleep(T)
    #     stepper.step.off()
    #     time.sleep(T)
    #
    conf = load_config()
    stepper = create_stepper(conf.stepper)
    stepper.enable.on()

    uart = UART("/dev/ttyAMA0", 115200)
    tmc = TMC2209Configure(uart, MS1=None, MS2=None, EN=23, node_address=0)
    tmc.initialize()
    time.sleep(0.01)

    while True:
        cmd = input("Command: ")

        tmc.vactual.VACTUAL = 200
        tmc.write_VACTUAL()



if __name__ == "__main__":
    main()
