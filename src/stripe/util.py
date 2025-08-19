from rpi_ws281x import PixelStrip, Color

import src.stripe.config as sc

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


def strip_init():
	strip1 = PixelStrip(sc.LED_COUNT, sc.LED_PIN_1, sc.LED_FREQ_HZ, sc.LED_DMA,
					 sc.LED_INVERT, sc.LED_BRIGHTNESS, sc.LED_CHANNEL_0)
	strip2 = PixelStrip(sc.LED_COUNT, sc.LED_PIN_2, sc.LED_FREQ_HZ, sc.LED_DMA,
					 sc.LED_INVERT, sc.LED_BRIGHTNESS, sc.LED_CHANNEL_1)
	strip1.begin()
	strip2.begin()
	return strip1, strip2

def clear_strip(strip):
	for i in range(strip.numPixels()):
		strip.setPixelColor(i, Color(0, 0, 0))
	strip.show()