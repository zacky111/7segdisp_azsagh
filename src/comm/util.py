import serial
import time

from src.comm.config import PORT, BAUD, parity, stopbits, bytesize, timeout

def ser_init():
    try:
        ser = serial.Serial(PORT, BAUD, parity=parity,
                        stopbits=stopbits,
                        bytesize=bytesize,
                        timeout=timeout)
        print(f"Otwarty port: {ser.portstr}")
        return ser
    except Exception as e:
        print(f"Błąd otwarcia portu szeregowego: {e}")
        return None

def parse_time_str(tstr):
    try:
        val = float(tstr)
        secs = int(val)
        ms = int(round((val - secs) * 1000))
        return val, secs, ms
    except Exception:
        return None, None, None
    

def racetime_alive(ser, timeout=0.2):
    try:
        #ser.reset_input_buffer()

        # PRZYKŁAD: ramka zapytania (sprawdź dokładny format w manualu!)
        ser.write(b'\x1bST\x03')   # ESC ... ETX

        start = time.time()
        buf = ""

        while time.time() - start < timeout:
            if ser.in_waiting:
                buf += ser.read(ser.in_waiting).decode('latin-1', errors='ignore')
                if '\x03' in buf:
                    return True   # odpowiedź przyszła

        return False
    except (OSError, serial.SerialException):
        return False
    

def ping_comm_func(ser):
    try:
        ser.write(b'\x1bPING\x03')   # ESC ... ETX
    except (OSError, serial.SerialException):
        pass