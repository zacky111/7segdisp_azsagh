import RPi.GPIO as GPIO
import src.shutdown_button.config as sbc
import time
import os

GPIO.setmode(GPIO.BCM)

# stan globalny przycisku
power_btn_pressed_at = None
shutdown_requested = False

def button_init():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(sbc.SHUTDOWN_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    print("[POWER] Shutdown button initialized")


def power_button_callback(poll_interval=0.05):
    """
    Monitoruje stan przycisku w pętli (uruchamiane w wątku).
    - raz wypisze '[POWER] Shutdown button pressed' przy przyciśnięciu,
    - wypisze '[POWER] Shutdown requested' gdy przytrzymanie >= SHUTDOWN_HOLD_TIME.
    """
    global power_btn_pressed_at, shutdown_requested

    print("[POWER] Shutdown button monitor started")
    power_btn_pressed_at = None
    shutdown_requested = False

    try:
        while True:
            if GPIO.input(sbc.SHUTDOWN_BUTTON_PIN) == GPIO.LOW:
                # przycisk właśnie został wciśnięty
                if power_btn_pressed_at is None:
                    power_btn_pressed_at = time.time()
                    print("[POWER] Shutdown button pressed")
            else:
                # przycisk puszczony — sprawdź długość przytrzymania
                if power_btn_pressed_at is not None:
                    held = time.time() - power_btn_pressed_at
                    power_btn_pressed_at = None
                    if held >= sbc.SHUTDOWN_HOLD_TIME and not shutdown_requested:
                        shutdown_requested = True
                        print("[POWER] Shutdown requested")
                        # os.system("sudo shutdown -h now")
            time.sleep(poll_interval)
    except Exception as e:
        print(f"[POWER] Monitor stopped: {e}")