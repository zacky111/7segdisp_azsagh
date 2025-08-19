import time
import signal
import sys
import re
import threading
import serial
import RPi.GPIO as GPIO

from src.dot.util import dot_init, dots_on, dots_off
from src.stripe.util import strip_init, clear_strip, print_strip, segm_from_frame
from src.comm.util import ser_init

# ---------------- LED SETUP ----------------
strip1, strip2 = strip_init()

# ---------------- DOTS -------------------------
dot_init()

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

    ser = ser_init()
    
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
                        if finished:
                            if frame_type == 'A' and '.' not in time_str_local:
                                # Clear start - without '.'
                                start_time_local = time.time() - val
                                running = True
                                finished = False
                                display_time = val
                                finish_time_shown_until = 0
                                blink_state = True
                                blink_last_toggle = time.time()
                            else:
                                continue  # ignorujemy resztę ramek

                        # --- rozróżnienie START/META ---
                        elif frame_type == 'A':
                            if '.' in time_str_local:
                                # META
                                running = False
                                finished = True
                                display_time = val
                                finish_time_shown_until = time.time() + 7
                                blink_state = True
                                blink_last_toggle = time.time()
                            else:
                                # START
                                start_time_local = time.time() - val
                                running = True
                                finished = False
                                display_time = val
                                finish_time_shown_until = 0
                                blink_state = True
                                blink_last_toggle = time.time()

                        elif running:
                            # ramki sekundowe → korekta dryfu
                            measured_now = time.time() - start_time_local
                            drift = val - measured_now
                            if abs(drift) > 0.05:
                                start_time_local += drift
                            display_time = measured_now

                print(f"[{frame_type}] czas: {time_str_local}")

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
                t_val = now - start_time_local

            elif finished and now < finish_time_shown_until:
                # mruganie 1 Hz
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
                # brak aktywnego czasu → wygaszenie
                clear_strip(strip1)
                clear_strip(strip2)
                time.sleep(0.01)
                continue

        # --- Formatowanie czasu
        minutes = int(t_val // 60)
        seconds = int(t_val % 60)
        hundredths = int((t_val * 100) % 100)

        digits = [
            ' ', ' ',  # 2 lewe puste
            ' ', ' ',  # domyślnie minuty wygaszone
            f"{seconds:02d}"[0], f"{seconds:02d}"[1],
            f"{hundredths:02d}"[0], f"{hundredths:02d}"[1]
        ]

        # Jeśli czas >= 1 min, to pokaż minuty normalnie
        if minutes > 0:
            digits[2] = f"{minutes:02d}"[0]
            digits[3] = f"{minutes:02d}"[1]

        # Ukrywanie zer wiodących dla sekund < 10
        if minutes == 0 and seconds < 10:
            digits[4] = ' '

        segm_to_print = segm_from_frame(digits)
        print_strip(segm_to_print,strip1, strip2)
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

# Main loop - to close remotly - Ctrl+C
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    signal_handler(None, None)
