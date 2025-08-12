import time
import signal
import sys
import re
import threading
import serial
import RPi.GPIO as GPIO
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

def segm_from_frame(data_frame: list, strip1=strip1, strip2=strip2):
    segm_on_strip1 = []
    segm_on_strip2 = []
    mapping_strip1 = [2, 3, 0, 1]

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

def print_strip(segm_to_print):
    for i in range(sc.LED_COUNT):
        strip1.setPixelColor(i, Color(255, 0, 0) if i in segm_to_print[0] else Color(0, 0, 0))
        strip2.setPixelColor(i, Color(255, 0, 0) if i in segm_to_print[1] else Color(0, 0, 0))
    strip1.show()
    strip2.show()

# ---------------- DOTS -------------------------
GPIO.setmode(GPIO.BCM)
GPIO.setup(dc.LED_PIN, GPIO.OUT)
GPIO.setup(dc.LED_PIN2, GPIO.OUT)
GPIO.setup(dc.LED_PIN3, GPIO.OUT)

def dots_on(LED_PIN=dc.LED_PIN, LED_PIN2=dc.LED_PIN2,LED_PIN3=dc.LED_PIN3):
    GPIO.output(LED_PIN, GPIO.HIGH)
    GPIO.output(LED_PIN2, GPIO.HIGH)
    GPIO.output(LED_PIN3, GPIO.HIGH)

def dots_off(LED_PIN=dc.LED_PIN, LED_PIN2=dc.LED_PIN2,LED_PIN3=dc.LED_PIN3):
    GPIO.output(LED_PIN, GPIO.LOW)
    GPIO.output(LED_PIN2, GPIO.LOW)
    GPIO.output(LED_PIN3, GPIO.LOW)

# ---------------- COMMUNICATION ----------------
stop_event = threading.Event()
data_lock = threading.Lock()

# Wspólne zmienne
start_time_local = None
display_time = 0.0
running = False

def parse_time_str(tstr):
    try:
        val = float(tstr)
        secs = int(val)
        ms = int(round((val - secs) * 1000))
        return val, secs, ms
    except Exception:
        return None, None, None

def comm_func():
    global start_time_local, display_time, running
    PORT = '/dev/ttyUSB0'
    BAUD = 1200
    ser = serial.Serial(PORT, BAUD, parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        bytesize=serial.EIGHTBITS,
                        timeout=1)
    print(f"Otwarty port: {ser.portstr}")
    buffer = ""

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
                    val, secs, ms = parse_time_str(time_str_local)

                    with data_lock:
                        if frame_type == 'A' and not running:  # Start
                            start_time_local = time.time() - val
                            running = True
                            display_time = val
                        elif running:
                            if '.' in time_str_local:  # META – czas z milisekundami
                                running = False
                                display_time = val
                                # korekta start_time_local jeśli chcesz, żeby był spójny
                                start_time_local = time.time() - val
                            else:
                                # zwykła ramka z pełnymi sekundami → ewentualna korekta dryfu
                                measured_now = time.time() - start_time_local
                                drift = val - measured_now
                                if abs(drift) > 0.05:
                                    start_time_local += drift
                                display_time = measured_now

                # debug print
                print(f"[{frame_type}] czas: {time_str_local}")

    ser.close()
    print("Port zamknięty, wątek kończy działanie")

# ---------------- DISPLAY THREAD ----------------
def display_func():
    global start_time_local, display_time, running
    while not stop_event.is_set():
        with data_lock:
            if running and start_time_local is not None:
                t_val = time.time() - start_time_local
            else:
                t_val = display_time

        minutes = int(t_val // 60)
        seconds = int(t_val % 60)
        hundredths = int((t_val - int(t_val)) * 100)

        digits = [
            ' ', ' ',                                 # 2 lewe puste
            f"{minutes:02d}"[0], f"{minutes:02d}"[1],
            f"{seconds:02d}"[0], f"{seconds:02d}"[1],
            f"{hundredths:02d}"[0], f"{hundredths:02d}"[1]
        ]

        # Zera wiodące → spacje
        if digits[2] == '0':
            digits[2] = ' '
        if digits[4] == '0' and digits[2] == ' ':
            digits[4] = ' '

        segm_to_print = segm_from_frame(digits)
        print_strip(segm_to_print)
        time.sleep(0.01)  # 10 ms

# ---------------- SIGNAL HANDLER ----------------
def signal_handler(sig, frame):
    print("\nWyłączam...")
    clear_strip(strip1)
    clear_strip(strip2)
    stop_event.set()
    thread_comm.join()
    thread_disp.join()
    GPIO.cleanup()  # wyłączenie kropek
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# ---------------- RUN THREADS ----------------
thread_comm = threading.Thread(target=comm_func)
thread_disp = threading.Thread(target=display_func)

dots_on()

thread_comm.start()
thread_disp.start()

thread_comm.join()
thread_disp.join()

