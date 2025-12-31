import RPi.GPIO as GPIO
import src.shutdown_button.config as sbc
import time
import os

def button_init():
    GPIO.setup(sbc.SHUTDOWN_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    print("[POWER] Shutdown button initialized")


def power_button_callback():
    global power_btn_pressed_at, shutdown_requested

    if GPIO.input(sbc.SHUTDOWN_BUTTON_PIN) == GPIO.LOW:
        # przycisk wciśnięty
        power_btn_pressed_at = time.time()
        print("[POWER] Shutdown button pressed")
    else:
        # przycisk puszczony
        if power_btn_pressed_at is None:
            return

        held = time.time() - power_btn_pressed_at
        power_btn_pressed_at = None

        if held >= sbc.SHUTDOWN_HOLD_TIME and not shutdown_requested:
            shutdown_requested = True
            print("[POWER] Shutdown requested")
            #os.system("sudo shutdown -h now")