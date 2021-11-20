from time import sleep
import RPi.GPIO as GPIO

DIR = 20
STEP =21
CW = 1
CCW = 1 
SPR = 48

GPIO.setmode(GPIO.BCM)
GBIO.setmode(DIR, GPIO.OUT)
GPIO.setup(STEP, GPIO.OUT)
GPIO.output(DIR,CW)

step_count = SPR
delay = .0208

for x in range(step_count):
    GPIO.output(STEP, GPIO.HIGH)
    sleep(delay)
    GPIO.output(STEP, GPIO.LOW)
    sleep(delay)
sleep(0.5)
GPIO.output(DIR,CCW)

https://en.nanotec.com/support/tutorials/stepper-motor-and-bldc-motors-animation/