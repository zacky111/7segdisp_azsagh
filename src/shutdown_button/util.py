import RPi.GPIO as GPIO
import src.shutdown_button.config as sbc
import time
import os
import subprocess
import signal

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
    - po przytrzymaniu >= SHUTDOWN_HOLD_TIME wypisze '[POWER] Shutdown requested' i wyłączy RPi.
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
                    # sprawdzaj czy już wystarczająco długo trzymamy
                    held = time.time() - power_btn_pressed_at
                    if held >= sbc.SHUTDOWN_HOLD_TIME and not shutdown_requested:
                        shutdown_requested = True
                        print("[POWER] Shutdown requested — initiating graceful shutdown")
                        try:
                            # Wywołaj handler w main (sygnał obsługiwany w głównym wątku)
                            signal.raise_signal(signal.SIGINT)
                        except Exception as e:
                            print(f"[POWER] Nie udało się wysłać SIGINT: {e}; próba bezpośredniego wyłączenia")
                            try:
                                subprocess.Popen(['/usr/sbin/shutdown', '-h', 'now'])
                            except Exception as e2:
                                print(f"[POWER] Failed to execute shutdown: {e2}")
                        return
            else:
                # przycisk puszczony — sprawdź długość przytrzymania i anuluj jeśli krócej niż próg
                if power_btn_pressed_at is not None:
                    held = time.time() - power_btn_pressed_at
                    power_btn_pressed_at = None
                    if held < sbc.SHUTDOWN_HOLD_TIME:
                        print(f"[POWER] Shutdown canceled (held {held:.2f}s)")
            time.sleep(poll_interval)
    except Exception as e:
        print(f"[POWER] Monitor stopped: {e}")