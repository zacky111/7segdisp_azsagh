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

def dots_on(LED_PIN=dc.LED_PIN, LED_PIN2=dc.LED_PIN2, LED_PIN3=dc.LED_PIN3):
    GPIO.output(LED_PIN, GPIO.HIGH)
    GPIO.output(LED_PIN2, GPIO.HIGH)
    GPIO.output(LED_PIN3, GPIO.HIGH)

def dots_off(LED_PIN=dc.LED_PIN, LED_PIN2=dc.LED_PIN2, LED_PIN3=dc.LED_PIN3):
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
finished = False
finish_time_shown_until = 0.0
blink_state = True
blink_last_toggle = 0.0

def parse_time_str(tstr):
    try:
        val = float(tstr)
        secs = int(val)
        ms = int(round((val - secs) * 1000))
        return val, secs, ms
    except Exception:
        return None, None, None

def comm_func():
    global start_time_local, display_time, running, finished
    global finish_time_shown_until, blink_state, blink_last_toggle

    # Tuning
    DRIFT_CORR_THRESHOLD = 0.05      # powyżej tego korygujemy start_time_local
    SECONDS_ACCEPT_WINDOW = 1.0      # sekundy akceptujemy tylko, gdy są blisko naszego t
    META_ACCEPT_WINDOW = 0.7         # meta akceptujemy, gdy |val - t| <= 0.7 s

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

                # Obsługa ramek typu "Sxxxx..." też z czasem po ID
                m = re.search(r'[Ss](\d{1,6})', cleaned)
                if m:
                    rest = cleaned[m.end():]
                    tmatch = re.search(r'(\d+\.\d+|\d+)', rest)
                else:
                    tmatch = re.search(r'(\d+\.\d+|\d+)', cleaned)

                time_str_local = tmatch.group(1) if tmatch else None

                action = "IGN"  # do debugów
                if time_str_local:
                    val, secs, ms = parse_time_str(time_str_local)
                    now = time.time()

                    with data_lock:
                        if running:
                            measured_now = now - start_time_local

                            if '.' in time_str_local:
                                # META: akceptuj tylko jeśli pasuje do aktualnego biegu
                                if abs(val - measured_now) <= META_ACCEPT_WINDOW:
                                    running = False
                                    finished = True
                                    display_time = val
                                    finish_time_shown_until = now + 7   # Twój czas migania
                                    blink_state = True
                                    blink_last_toggle = now
                                    action = "META_OK"
                                else:
                                    # spóźniona meta z poprzedniego zawodnika → ignoruj
                                    action = "META_IGN"
                            else:
                                # Ramka sekundowa → koryguj tylko jeśli blisko naszego czasu
                                drift = val - measured_now
                                if abs(drift) <= SECONDS_ACCEPT_WINDOW:
                                    if abs(drift) > DRIFT_CORR_THRESHOLD:
                                        start_time_local += drift
                                    display_time = measured_now
                                    action = "SEC_OK"
                                else:
                                    action = "SEC_IGN"

                        else:
                            if finished:
                                # W trakcie migania – dowolna ramka z CZASEM BEZ KROPKI
                                # oznacza, że kolejny zawodnik już jedzie → przełącz na running
                                if '.' not in time_str_local:
                                    start_time_local = now - val
                                    running = True
                                    finished = False
                                    display_time = val
                                    finish_time_shown_until = 0.0
                                    blink_state = True
                                    blink_last_toggle = now
                                    action = "START_FROM_FINISHED"
                                else:
                                    action = "FIN_BLINK_IGN"
                            else:
                                # IDLE: jeśli przyjdzie liczba całkowita → start
                                if '.' not in time_str_local:
                                    start_time_local = now - val
                                    running = True
                                    finished = False
                                    display_time = val
                                    finish_time_shown_until = 0.0
                                    blink_state = True
                                    blink_last_toggle = now
                                    action = "START_IDLE"
                                else:
                                    # przyszła meta bez biegu (np. retransmisja) → opcjonalnie migaj
                                    running = False
                                    finished = True
                                    display_time = val
                                    finish_time_shown_until = now + 7
                                    blink_state = True
                                    blink_last_toggle = now
                                    action = "META_WHILE_IDLE"

                print(f"[{frame_type}] czas: {time_str_local} -> {action}")

    ser.close()
    print("Port zamknięty, wątek kończy działanie")

# ---------------- DISPLAY THREAD ----------------
def display_func():
    global start_time_local, display_time, running, finished
    global finish_time_shown_until, blink_state, blink_last_toggle

    while not stop_event.is_set():
        with data_lock:
            now = time.time()

            if running and start_time_local is not None:
                # --- Priorytet dla aktywnego przejazdu ---
                t_val = now - start_time_local

            elif finished and now < finish_time_shown_until and not running:
                # --- Miganie tylko, gdy NIE ma nowego biegu ---
                if now - blink_last_toggle >= 0.7:
                    blink_state = not blink_state
                    blink_last_toggle = now

                if blink_state:
                    t_val = display_time
                else:
                    clear_strip(strip1)
                    clear_strip(strip2)
                    time.sleep(0.01)
                    continue

            else:
                # --- Brak aktywnego czasu i brak migania ---
                clear_strip(strip1)
                clear_strip(strip2)
                time.sleep(0.01)
                continue

        # --- Formatowanie czasu do wyświetlenia ---
        minutes = int(t_val // 60)
        seconds = int(t_val % 60)
        hundredths = int((t_val * 100) % 100)

        digits = [
            ' ', ' ',                                 # 2 lewe puste
            f"{minutes:02d}"[0], f"{minutes:02d}"[1], # minuty
            f"{seconds:02d}"[0], f"{seconds:02d}"[1], # sekundy
            f"{hundredths:02d}"[0], f"{hundredths:02d}"[1]  # setne
        ]

        # Ukrywanie zer wiodących
        if minutes < 10:
            digits[2] = ' '
        if minutes == 0 and seconds < 10:
            digits[4] = ' '

        segm_to_print = segm_from_frame(digits)
        print_strip(segm_to_print)
        time.sleep(0.01)  # 10 ms odświeżanie

# ---------------- SIGNAL HANDLER ----------------
def signal_handler(sig, frame):
    print("\nWyłączam...")
    clear_strip(strip1)
    clear_strip(strip2)
    stop_event.set()
    thread_comm.join()
    thread_disp.join()
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# ---------------- RUN THREADS ----------------
thread_comm = threading.Thread(target=comm_func, daemon=True)
thread_disp = threading.Thread(target=display_func, daemon=True)

dots_on()

thread_comm.start()
thread_disp.start()

# Główna pętla (żyje do CTRL+C)
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    signal_handler(None, None)
