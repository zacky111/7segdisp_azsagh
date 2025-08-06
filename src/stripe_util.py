"""				  3						 10
			.-----------.			.-----------.
			|			|			|			|
		   4|			|2		  11|			|9
			|			|			|			|
			|	  1		|			|	  8		|
GPIO--------.-----------.-----------.-----------.
			|			|			|			|
			|			|			|			|
		   5|			|7		  12|			|14
			|			|			|			|
			.-----------.			.-----------.
				  6						  13
"""

liczbyWysw = {
	"0": [2,3,4,5,6,7],
	"1": [2,7],
	"2": [1,2,3,5,6],
	"3": [1,2,3,6,7],
	"4": [1,2,4,7],
	"5": [1,3,4,6,7],
	"6": [1,3,4,5,6,7],
	"7": [2,3,7],
	"8": [1,2,3,4,5,6,7],
	"9": [1,2,3,4,6,7]
}

def sum_segm(liczby_do_wysw: int) -> list:

	# funkcja przyjmuje dwie liczby, które mają odpowiadać za jedną taśmę (np. minuty, sekundy itd.)
	# przekształca w dwie liczby i sumuje w jedną zbiorczą listę numerów segm_on, której mają zostać wyświetlone

    liczby_str = str(liczby_do_wysw).zfill(2)  # zawsze 2 znaki
    liczba_1 = liczby_str[0]
    liczba_2 = liczby_str[1]

    return liczbyWysw[liczba_1] + liczbyWysw[liczba_2]

"""kolory = {
"bialy":(0,0,0),
"czerwony":(255,0,0),
"zielony":(0,255,0),
"niebieski":(0,0,255),
}"""