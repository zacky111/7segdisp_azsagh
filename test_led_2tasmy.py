import time
import signal
import sys
from rpi_ws281x import PixelStrip, Color

# Konfiguracja LED
LED_COUNT = 28
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 128
LED_INVERT = False
LED_CHANNEL_0 = 0
LED_CHANNEL_1 = 1

# GPIO: muszą być zgodne z kanałami PWM (tylko niektóre są obsługiwane!)
LED_PIN_1 = 18  # GPIO18 -> channel 0
LED_PIN_2 = 19  # GPIO19 -> channel 1

# Inicjalizacja dwóch taśm
strip1 = PixelStrip(LED_COUNT, LED_PIN_1, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL_0)
strip2 = PixelStrip(LED_COUNT, LED_PIN_2, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL_1)
strip1.begin()
strip2.begin()

def clear_strip(strip):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

def signal_handler(sig, frame):
    print("\nWyłączam...")
    clear_strip(strip1)
    clear_strip(strip2)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print("Naprzemienne podświetlanie 0–13 i 14–27 LED (Ctrl+C aby zakończyć)")

while True:
    # Pierwsza połowa (0–13) czerwona
    for i in range(LED_COUNT):
        color = Color(255, 0, 0) if i < 14 else Color(0, 0, 0)
        strip1.setPixelColor(i, color)
        strip2.setPixelColor(i, color)
    strip1.show()
    strip2.show()
    time.sleep(1)

    # Druga połowa (14–27) niebieska
    for i in range(LED_COUNT):
        color = Color(0, 255, 0) if i >= 14 else Color(0, 0, 0)
        strip1.setPixelColor(i, color)
        strip2.setPixelColor(i, color)
    strip1.show()
    strip2.show()
    time.sleep(1)
