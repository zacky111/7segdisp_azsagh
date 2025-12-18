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

colorMapping={
    "red": Color(255, 0, 0),
    "blue": Color(0,0, 255),
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

def print_strip(segm_to_print,strip1, strip2, color="red"):

    for i in range(sc.LED_COUNT):
        strip1.setPixelColor(i, colorMapping[color] if i in segm_to_print[0] else Color(0, 0, 0))
        strip2.setPixelColor(i, colorMapping[color] if i in segm_to_print[1] else Color(0, 0, 0))
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