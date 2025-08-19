import time
import board
import neopixel
import signal
import sys

# Parametry taśmy
LED_COUNT = 14       # liczba LEDów na taśmie
LED_PIN = board.D12   # GPIO 18 (pin 12)
LED_BRIGHTNESS = 0.5  # jasność (0.0 do 1.0)
LED_ORDER = neopixel.GRB  # kolejność kolorów – WS2811 zwykle GRB

# Inicjalizacja paska LED
pixels = neopixel.NeoPixel(
    LED_PIN,
    LED_COUNT,
    brightness=LED_BRIGHTNESS,
    auto_write=False,
    pixel_order=LED_ORDER
)

def clear_strip():
    pixels.fill((0, 0, 0))
    pixels.show()

# Obsługa Ctrl+C – gasi taśmę
def signal_handler(sig, frame):
    print("\nWyłączam diody...")
    clear_strip()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Podświetlenie – kolor czerwony
pixels.fill((255, 0, 0))  # R, G, B
pixels.show()

print("Wciśnij Ctrl+C aby wyłączyć...")

# Czekamy nieskończoność – aż użytkownik przerwie
while True:
    time.sleep(1)
