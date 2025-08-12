import time
import signal
import sys
import re
import threading
import serial
from rpi_ws281x import PixelStrip, Color

import src.stripe_config as sc
import src.dot_config as dc
from src.stripe_util import liczbyWysw

# ---------------- LED SETUP ----------------
strip1 = PixelStrip(sc.LED_COUNT, sc.LED_PIN_1, sc.LED_FREQ_HZ, sc.LED_DMA,
                    sc.LED_INVERT, sc.LED_BRIGHTNESS, sc.LED_CHANNEL_0)
strip2 = PixelStrip(sc.LED_COUNT, sc.LED_PIN_2, sc.LED_FREQ_HZ, sc.LED_DMA,
                    sc.LED_INVERT, sc.LED_BRIGHTNESS, sc.LED_CHANNEL_1)
strip1.begin()
strip2.begin()

def clear_strip(strip):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

def segm_from_frame(data_frame: str, strip1=strip1, strip2=strip2):
    segm_on_strip1 = []
    segm_on_strip2 = []
    mapping_strip1 = [2, 3, 0, 1]
    for num, elem in enumerate(data_frame):
        part_segm = liczbyWysw[elem]
        if num < 4:
            mapped_num = mapping_strip1[num]
            part_segm = [x + mapped_num * 7 for x in part_segm]
            segm_on_strip1 += part_segm
        else:
            part_segm = [x + (num - 4) * 7 for x in part_segm]
            segm_on_strip2 += part_segm
    return [segm_on_strip1, segm_on_strip2]

def print_strip(segm_to_print):
    for i in range(sc.LED_COUNT):
        strip1.setPixelColor(i, Color(255, 0, 0) if i in segm_to_print[0] else Color(0, 0, 0))
        strip2.setPixelColor(i, Color(255, 0, 0) if i in segm_to_print[1] else Color(0, 0, 0))
    strip1.show()
    strip2.show()

def format_number_as_8digit_string(n: int) -> str:
    return str(n).zfill(8)[-8:]

# ---------------- COMMUNICATION ----------------
stop_event = threading.Event()
data_lock = threading.Lock()
latest_time = "0"   # współdzielona zmienna

def parse_time_str(tstr):
    try:
        val = float(tstr)
        secs = int(val)
        ms = int(round((val - secs) * 1000))
        return val, secs, ms
    except Exception:
        return None, None, None

def comm_func():
    global latest_time
    PORT = '/dev/ttyUSB0'
    BAUD = 1200
    ser = serial.Serial(PORT, BAUD, parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        bytesize=serial.EIGHTBITS,
                        timeout=1)
    print(f"Otwarty port: {ser.portstr}")
    buffer = ""
    start_time = time.time()

    while not stop_event.is_set():
        if ser.in_waiting > 0:
            raw = ser.read(ser.in_waiting)
            part = raw.decode('latin-1', errors='replace')
            buffer += part

            while '\x03' in buffer:
                start = buffer.find('\x1b')
                if start == -1:
                    idx_etx = buffer.find('\x03')
                    buffer = buffer[idx_etx+1:]
                    continue
                end = buffer.find('\x03', start)
                if end == -1:
                    break
                raw_frame = buffer[start+1:end]
                buffer = buffer[end+1:]
                cleaned = re.sub(r'[^0-9A-Za-z\s\.\-]', '', raw_frame)
                frame_type = cleaned[0].upper() if cleaned else '?'

                m = re.search(r'[Ss](\d{1,6})', cleaned)
                if m:
                    rest = cleaned[m.end():]
                    tmatch = re.search(r'(\d+\.\d+|\d+)', rest)
                else:
                    tmatch = re.search(r'(\d+\.\d+)', cleaned)

                time_str_local = tmatch.group(1) if tmatch else None
                if time_str_local:
                    with data_lock:
                        latest_time = time_str_local

                ts = time.time() - start_time
                if time_str_local:
                    float_time, secs, ms = parse_time_str(time_str_local)
                    print(f"[{ts:8.3f}s] [{frame_type}] czas: {time_str_local} s ({secs} s {ms} ms)")

    ser.close()
    print("Port zamknięty, wątek kończy działanie")

# ---------------- DISPLAY THREAD ----------------
def display_func():
    while not stop_event.is_set():
        with data_lock:
            t_str = latest_time

        try:
            val = float(t_str)
        except:
            val = 0.0

        minutes = int(val // 60)
        seconds = int(val % 60)
        hundredths = int(round((val - int(val)) * 100))  # setne sekundy

        # Składamy w tablicę 8 pozycji: [pusty, pusty, min, min, sec, sec, cent, cent]
        digits = [
            ' ', ' ',                                 # 2 lewe puste
            f"{minutes:02d}"[0], f"{minutes:02d}"[1], # minuty
            f"{seconds:02d}"[0], f"{seconds:02d}"[1], # sekundy
            f"{hundredths:02d}"[0], f"{hundredths:02d}"[1]  # setne
        ]

        # Zamiana zer wiodących na spacje w minutach i sekundach
        if digits[2] == '0':
            digits[2] = ' '
        if digits[4] == '0' and digits[2] == ' ':  # jeśli minuta pusta i sekundy mają zero dziesiątek
            digits[4] = ' '

        # Wyświetlenie
        segm_to_print = segm_from_frame(digits)
        print_strip(segm_to_print)

        time.sleep(0.1)


# ---------------- SIGNAL HANDLER ----------------
def signal_handler(sig, frame):
    print("\nWyłączam...")
    clear_strip(strip1)
    clear_strip(strip2)
    stop_event.set()
    thread_comm.join()
    thread_disp.join()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# ---------------- RUN THREADS ----------------
thread_comm = threading.Thread(target=comm_func)
thread_disp = threading.Thread(target=display_func)

thread_comm.start()
thread_disp.start()

thread_comm.join()
thread_disp.join()
