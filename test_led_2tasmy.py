import time
import signal
import sys
from rpi_ws281x import PixelStrip, Color

import src.stripe_config as sc
import src.dot_config as dc

from src.stripe_util import sum_segm, liczbyWysw

# Inicjalizacja dwóch taśm
strip1 = PixelStrip(sc.LED_COUNT, sc.LED_PIN_1, sc.LED_FREQ_HZ, sc.LED_DMA,sc. LED_INVERT, sc.LED_BRIGHTNESS, sc.LED_CHANNEL_0)
strip2 = PixelStrip(sc.LED_COUNT, sc.LED_PIN_2, sc.LED_FREQ_HZ, sc.LED_DMA, sc.LED_INVERT, sc.LED_BRIGHTNESS, sc.LED_CHANNEL_1)
strip1.begin()
strip2.begin()

data_frame_test="11000023"

def clear_strip(strip):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

def signal_handler(sig, frame):
    print("\nWyłączam...")
    clear_strip(strip1)
    clear_strip(strip2)
    sys.exit(0)

def print_strip(data_frame:str, strip1=strip1, strip2=strip2):
    segm_on_strip1=[]
    segm_on_strip2=[]
    num=0
    for num, elem in enumerate(data_frame):
        if num < 4:
            part_segm = liczbyWysw[elem]
            part_segm = [x + num * 7 for x in part_segm]
            segm_on_strip1 += part_segm
        else:
            part_segm = liczbyWysw[elem]
            part_segm = [x + (num - 4) * 7 for x in part_segm]
            segm_on_strip2 += part_segm

    print("segm1: ", segm_on_strip1)
    print("segm2: ", segm_on_strip2)

signal.signal(signal.SIGINT, signal_handler)

print_strip(data_frame=data_frame_test)

while True:
    # Pierwsza połowa (0–13) czerwona
    for i in range(sc.LED_COUNT):
        color = Color(255, 0, 0) if i < 14 else Color(0, 0, 0)
        strip1.setPixelColor(i, color)
        strip2.setPixelColor(i, color)
    strip1.show()
    strip2.show()
    time.sleep(1)

    # Druga połowa (14–27) niebieska
    for i in range(sc.LED_COUNT):
        color = Color(0, 255, 0) if i >= 14 else Color(0, 0, 0)
        strip1.setPixelColor(i, color)
        strip2.setPixelColor(i, color)
    strip1.show()
    strip2.show()
    time.sleep(1)



