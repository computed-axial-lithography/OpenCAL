# from opencal.hardware.stepper_controller import StepperMotor
from opencal.hardware.stepper import create_stepper
from opencal.utils.config import load_config
# from opencal.utils.config import Config
import time

from TMC2209_PY import UART, TMC2209Configure
from TMC2209_PY.registers import GCONF_adr


def main():
    uart = UART("/dev/ttyAMA0", 115200)
    tmc = TMC2209Configure(uart, MS1=None, MS2=None, EN=23, node_address=0)
    time.sleep(0.5)

    old_gconf = tmc.read_register(GCONF_adr)
    tmc.gconf.reg = old_gconf
    print(f"{tmc.gconf!r}")
    old_chopconf = tmc.read_CHOPCONF()
    print(f"{tmc.chopconf!r}")
    old_pwmconf = tmc.read_PWMCONF()
    print(f"{tmc.pwmconf!r}")

    tmc.chopconf.toff = 5
    tmc.chopconf.hstrt = 5
    tmc.chopconf.vsense = 1
    tmc.chopconf.intpol = 1
    tmc.chopconf.mres = 3
    tmc.write_CHOPCONF()

    tmc.ihold_irun.IHOLD = 0
    tmc.ihold_irun.IRUN = 15
    tmc.ihold_irun.IHOLDDELAY = 1
    tmc.write_IHOLD_IRUN()

    tmc.gconf.I_scale_analog = 1
    tmc.gconf.mstep_reg_select = 1
    tmc.gconf.multistep_filt = 1
    tmc.gconf.pdn_disable = 1
    tmc.gconf.shaft = 0
    tmc.write_GCONF()

    tmc.nodeconf.SENDDELAY = 7
    tmc.write_NODECONF()

    tmc.pwmconf.PWM_OFS = 36
    tmc.pwmconf.PWM_FREQ = 1
    tmc.pwmconf.PWM_autoscale = 1
    tmc.pwmconf.PWM_autograd = 1
    tmc.pwmconf.PWM_REG = 1
    tmc.pwmconf.PWM_LIM = 12
    tmc.write_PWMCONF()

    while True:
        cmd = input("Command: ")
        parts = cmd.split(" ")
        
        
        if len(parts) == 2:
            if parts[0] == "read":
                reg = parts[1]
                getattr(tmc, f"read_{reg.upper()}")()
                print(f"{getattr(tmc, reg)!r}")
        if len(parts) == 3:
            reg, part, value = parts
            reg_obj = getattr(tmc, reg)
            setattr(reg_obj, part, int(value))
            getattr(tmc, f"write_{reg.upper()}")()

        
        elif parts[0] == 'reset':
            tmc.chopconf = old_chopconf
            tmc.write_CHOPCONF()
            tmc.pwmconf = old_pwmconf
            tmc.write_PWMCONF()




if __name__ == "__main__":
    main()
