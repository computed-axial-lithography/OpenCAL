from opencal.hardware.stepper import create_stepper
from opencal.hardware.stepper.step_dir import StepDirStepperMotor
from opencal.utils.config import load_config
import time



def main():
    conf = load_config()
    stepper: StepDirStepperMotor = create_stepper(conf.stepper)

    stepper.enable.on()
    
    for i in range(1000):
        stepper.step.on()
        time.sleep(0.01)
        stepper.step.off()
        time.sleep(0.01)
    



if __name__ == "__main__":
    main()
