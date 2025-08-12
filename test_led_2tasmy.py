import time
import signal
import sys
from rpi_ws281x import PixelStrip, Color

import src.stripe_config as sc
import src.dot_config as dc

from src.stripe_util import liczbyWysw

import serial
import re
import threading

### stripes - functions, variables etc.

# Inicjalizacja dwóch taśm
strip1 = PixelStrip(sc.LED_COUNT, sc.LED_PIN_1, sc.LED_FREQ_HZ, sc.LED_DMA,sc. LED_INVERT, sc.LED_BRIGHTNESS, sc.LED_CHANNEL_0)
strip2 = PixelStrip(sc.LED_COUNT, sc.LED_PIN_2, sc.LED_FREQ_HZ, sc.LED_DMA, sc.LED_INVERT, sc.LED_BRIGHTNESS, sc.LED_CHANNEL_1)
strip1.begin()
strip2.begin()



###### functions for usage of stripes:
def clear_strip(strip):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

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



def format_number_as_8digit_string(n: int) -> str:
    # Ogranicz do 8 cyfr, obetnij nadmiar z lewej
    return str(n).zfill(8)[-8:]


#### communcation - functions, variables etc.

stop_event = threading.Event()

def parse_time_str(tstr):
    """Zwraca (float_seconds, secs_int, ms_int) lub (None, None, None) jeśli brak."""
    try:
        val = float(tstr)
        secs = int(val)
        ms = int(round((val - secs) * 1000))
        return val, secs, ms
    except Exception:
        return None, None, None

def comm_func():
    PORT = '/dev/ttyUSB0'
    BAUD = 1200

    global ser, time_str, float_time, secs, ms

    ser = serial.Serial(
        port=PORT,
        baudrate=BAUD,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=1
    )
    print(f"Otwarty port: {ser.portstr}")

    start_time = time.time()

    buffer = ""

    while stop_event.is_set():
        if ser.in_waiting > 0:
            raw = ser.read(ser.in_waiting)
            # latin-1 żeby nie tracić bajtów; później usuniemy sterujące
            part = raw.decode('latin-1', errors='replace')
            buffer += part

            # obsługa pełnych ramek: od ESC (\x1b) do ETX (\x03)
            while '\x03' in buffer:
                start = buffer.find('\x1b')
                if start == -1:
                    # jeśli brak \x1b zanim ETX, wyrzucamy początek do kolejnego ETX
                    idx_etx = buffer.find('\x03')
                    buffer = buffer[idx_etx+1:]
                    continue

                end = buffer.find('\x03', start)
                if end == -1:
                    break  # czekamy na dokończenie ramki

                raw_frame = buffer[start+1:end]  # bez ESC i ETX
                buffer = buffer[end+1:]

                # usuwamy nietekstowe znaki (pozostawiamy spacje, cyfry, litery, kropkę)
                cleaned = re.sub(r'[^0-9A-Za-z\s\.\-]', '', raw_frame)

                # pierwszy znak po ESC to zwykle typ ramki (A/B/C/itd.)
                frame_type = cleaned[0].upper() if cleaned else '?'
                payload = cleaned[1:].strip() if len(cleaned) > 1 else ''

                # szukamy numeru zawodnika w formacie Sxx
                bib = None
                m = re.search(r'[Ss](\d{1,6})', cleaned)
                if m:
                    bib = m.group(1)
                    rest = cleaned[m.end():]
                    tmatch = re.search(r'(\d+\.\d+|\d+)', rest)
                else:
                    m2 = re.search(r'\b(\d{1,6})\b(?!\.)', cleaned)
                    if m2:
                        bib = m2.group(1)
                        rest = cleaned[m2.end():]
                        tmatch = re.search(r'(\d+\.\d+|\d+)', rest)
                    else:
                        tmatch = re.search(r'(\d+\.\d+)', cleaned)

                time_str = tmatch.group(1) if tmatch else None
                float_time, secs, ms = parse_time_str(time_str) if time_str else (None, None, None)

                # znacznik czasu (sekundy od startu programu)
                ts = time.time() - start_time

                # Wyświetlanie wyników
                if bib:
                    bib_disp = bib
                else:
                    bib_disp = '-'

                if time_str:
                    print(f"[{ts:8.3f}s] [{frame_type}] Zawodnik: {bib_disp} — czas: {time_str} s ({secs} s {ms} ms)")
                else:
                    print(f"[{ts:8.3f}s] [{frame_type}] Zawodnik: {bib_disp} — czas: -")

    ser.close()
    print("Port zamknięty, wątek kończy działanie")

def signal_handler(sig, frame):
    print("\nWyłączam...")
    clear_strip(strip1)
    clear_strip(strip2)
    stop_event.set()  # sygnał zakończenia wątku
    thread_comm.join()  # czekaj na zakończenie wątku

    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler) ## konieczne, aby wyłączać ctrl+c


counter=0
#threads=[]
thread_comm=threading.Thread(target=comm_func)
thread_comm.start()

float_time=0


while True:
    # Konwertuj licznik do napisu z 8 cyframi
    
    #data_frame = format_number_as_8digit_string(counter) # wersja automatyczna - licznik
    data_frame = format_number_as_8digit_string(float_time)
    
    # Oblicz segmenty i wyświetl
    segm_to_print = segm_from_frame(data_frame=data_frame)
    print_strip(segm_to_print)

    counter += 1
    time.sleep(0.1)

    
    




