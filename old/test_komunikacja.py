import serial
import re
import time

# --- konfiguracja ---
PORT = '/dev/ttyUSB0'
BAUD = 1200

ser = serial.Serial(
    port=PORT,
    baudrate=BAUD,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)

print(f"Otwarty port: {ser.portstr}")

def parse_time_str(tstr):
    """Zwraca (float_seconds, secs_int, ms_int) lub (None, None, None) jeśli brak."""
    try:
        val = float(tstr)
        secs = int(val)
        ms = int(round((val - secs) * 1000))
        return val, secs, ms
    except Exception:
        return None, None, None

start_time = time.time()

try:
    buffer = ""

    while True:
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

except KeyboardInterrupt:
    print("\nZamykam...")
finally:
    ser.close()
