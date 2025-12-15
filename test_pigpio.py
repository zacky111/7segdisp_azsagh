import time
from src.stripe.pigpio_strip import WS2812Strip

from src.stripe.config import LED_PIN_1, LED_COUNT

GPIO = LED_PIN_1      # <-- TEN PIN, do którego masz DATA
LEDS = LED_COUNT      # nawet 1 wystarczy

strip = WS2812Strip(GPIO, LEDS, brightness=0.2)

strip.clear()

strip.set_pixel(0, (255, 0, 0))  # pierwsza dioda na czerwono
strip.show()

time.sleep(5)

strip.clear()
