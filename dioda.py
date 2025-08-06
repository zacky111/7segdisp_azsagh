import RPi.GPIO as GPIO
import time

# Ustawienie numeracji GPIO według schematu BCM
LED_PIN = 16  # GPIO17 (Pin 11)
LED_PIN2 = 20
LED_PIN3 =  21

GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(LED_PIN2, GPIO.OUT)
GPIO.setup(LED_PIN3, GPIO.OUT)

try:
    while True:
        GPIO.output(LED_PIN, GPIO.HIGH)  # Włączenie diod
        GPIO.output(LED_PIN2, GPIO.HIGH)  # Włączenie diod
        GPIO.output(LED_PIN3, GPIO.HIGH)  # Włączenie diod
        print("Diody ON")
        time.sleep(1)  # Czekaj 1 sek.

        GPIO.output(LED_PIN, GPIO.LOW)   # Wyłączenie diod
        GPIO.output(LED_PIN2, GPIO.LOW)  # Wyłączenie diod
        GPIO.output(LED_PIN3, GPIO.LOW)  # Wyłączenie diod
        print("Diody OFF")
        time.sleep(1)  # Czekaj 1 sek.

except KeyboardInterrupt:
    print("Przerwano działanie")
    GPIO.cleanup()  # Reset ustawień GPIO
