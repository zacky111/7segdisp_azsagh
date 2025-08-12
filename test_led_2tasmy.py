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

def clear_strip(strip):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

def signal_handler(sig, frame):
    print("\nWyłączam...")
    clear_strip(strip1)
    clear_strip(strip2)
    sys.exit(0)

def segm_from_frame(data_frame: str, strip1=strip1, strip2=strip2):
    segm_on_strip1 = []
    segm_on_strip2 = []

    mapping_strip1 = [2, 3, 0, 1]  # mapowanie logicznego numeru cyfry na fizyczne połączenie

    for num, elem in enumerate(data_frame):
        part_segm = liczbyWysw[elem]

        if num < 4:
            mapped_num = mapping_strip1[num]
            part_segm = [x + mapped_num * 7 for x in part_segm]
            segm_on_strip1 += part_segm
        else:
            part_segm = [x + (num - 4) * 7 for x in part_segm]
            segm_on_strip2 += part_segm

    print("segm1: ", segm_on_strip1)
    print("segm2: ", segm_on_strip2)

    return [segm_on_strip1, segm_on_strip2]

def print_strip(segm_to_print, strip1=strip1, strip2=strip2):
    for i in range(sc.LED_COUNT):
        color = Color(255, 0, 0) if i in segm_to_print[0] else Color(0, 0, 0)
        strip1.setPixelColor(i, color)

        color2 = Color(255, 0, 0) if i in segm_to_print[1] else Color(0, 0, 0)
        strip2.setPixelColor(i, color2)

        strip1.show()
        strip2.show()

#signal.signal(signal.SIGINT, signal_handler)

def format_number_as_8digit_string(n: int) -> str:
    # Ogranicz do 8 cyfr, obetnij nadmiar z lewej
    return str(n).zfill(8)[-8:]



counter=0
while True:
        # Konwertuj licznik do napisu z 8 cyframi
    data_frame = format_number_as_8digit_string(counter)
    
    # Oblicz segmenty i wyświetl
    segm_to_print = segm_from_frame(data_frame=data_frame)
    print_strip(segm_to_print)

    counter += 1
    time.sleep(0.1)




