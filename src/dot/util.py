import RPi.GPIO as GPIO
import src.dot.config as dc

GPIO.setmode(GPIO.BCM)
GPIO.setup(dc.LED_PIN1, GPIO.OUT)
GPIO.setup(dc.LED_PIN2, GPIO.OUT)
GPIO.setup(dc.LED_PIN3, GPIO.OUT)

def dots_on(LED_PIN1=dc.LED_PIN1, LED_PIN2=dc.LED_PIN2, LED_PIN3=dc.LED_PIN3):
    GPIO.output(LED_PIN1, GPIO.HIGH)
    GPIO.output(LED_PIN2, GPIO.HIGH)
    GPIO.output(LED_PIN3, GPIO.HIGH)

def dots_off(LED_PIN1=dc.LED_PIN1, LED_PIN2=dc.LED_PIN2, LED_PIN3=dc.LED_PIN3):
    GPIO.output(LED_PIN1, GPIO.LOW)
    GPIO.output(LED_PIN2, GPIO.LOW)
    GPIO.output(LED_PIN3, GPIO.LOW)


def dot_init():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(dc.LED_PIN1, GPIO.OUT)
    GPIO.setup(dc.LED_PIN2, GPIO.OUT)
    GPIO.setup(dc.LED_PIN3, GPIO.OUT)