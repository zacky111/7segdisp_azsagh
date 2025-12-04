import board
from neopixel import NeoPixel, neopixel


import src.stripe.config as sc

import RPi.GPIO as GPIO
GPIO.setwarnings(False)

"""				  2						  9
			.-----------.			.-----------.
			|			|			|			|
		   3|			|1		  10|			|8
			|			|			|			|
			|	  0		|			|	  7		|
GPIO--------.-----------.-----------.-----------.
			|			|			|			|
			|			|			|			|
		   4|			|6		  11|			|13
			|			|			|			|
			.-----------.			.-----------.
				  5						  12
"""

liczbyWysw = {
    "0": [1, 2, 3, 4, 5, 6],
    "1": [1, 6],
    "2": [0, 1, 2, 4, 5],
    "3": [0, 1, 2, 5, 6],
    "4": [0, 1, 3, 6],
    "5": [0, 2, 3, 5, 6],
    "6": [0, 2, 3, 4, 5, 6],
    "7": [1, 2, 6],
    "8": [0, 1, 2, 3, 4, 5, 6],
    "9": [0, 1, 2, 3, 5, 6],
    " ": []
}

# NeoPixel uses (R,G,B) tuples
colorMapping = {
    "red": (255, 0, 0),
    "blue": (0, 0, 255),
}


def _board_pin_from_bcm(bcm_number):
    """Spróbuj zwrócić board.D{n} dla podanego numeru BCM, fallback na D18."""
    try:
        return getattr(board, f"D{bcm_number}")
    except Exception:
        return board.D18


def strip_init():
    """Zwraca dwa obiekty NeoPixel (strip1, strip2)."""
    pin1 = _board_pin_from_bcm(sc.LED_PIN_1)
    pin2 = _board_pin_from_bcm(sc.LED_PIN_2)
    # NeoPixel brightness przyjmuje 0.0-1.0
    brightness = max(0.0, min(1.0, sc.LED_BRIGHTNESS / 255.0))
    strip1 = NeoPixel(pin1, sc.LED_COUNT, brightness=brightness, auto_write=False, pixel_order=neopixel.GRB)
    strip2 = NeoPixel(pin2, sc.LED_COUNT, brightness=brightness, auto_write=False, pixel_order=neopixel.GRB)
    # wyzeruj od razu
    clear_strip(strip1)
    clear_strip(strip2)
    return strip1, strip2

def clear_strip(strip):
    for i in range(len(strip)):
        strip[i] = (0, 0, 0)
    strip.show()

def print_strip(segm_to_print, strip1, strip2, color="red"):
    col = colorMapping.get(color, (255, 0, 0))
    for i in range(sc.LED_COUNT):
        strip1[i] = col if i in segm_to_print[0] else (0, 0, 0)
        strip2[i] = col if i in segm_to_print[1] else (0, 0, 0)
    strip1.show()
    strip2.show()


def segm_from_frame(data_frame: list):
    segm_on_strip1 = []
    segm_on_strip2 = []
    mapping_strip1 = [2, 3, 0, 1]  # map logic->physical for first 4 digits

    for num, elem in enumerate(data_frame):
        part_segm = liczbyWysw.get(elem, [])
        if num < 4:
            mapped_num = mapping_strip1[num]
            part_segm = [x + mapped_num * 7 for x in part_segm]
            segm_on_strip1 += part_segm
        else:
            part_segm = [x + (num - 4) * 7 for x in part_segm]
            segm_on_strip2 += part_segm
    return [segm_on_strip1, segm_on_strip2]