import serial

from src.comm.config import PORT, BAUD, parity, stopbits, bytesize, timeout

def ser_init():
    ser = serial.Serial(PORT, BAUD, parity=parity,
                    stopbits=stopbits,
                    bytesize=bytesize,
                    timeout=timeout)
    print(f"Otwarty port: {ser.portstr}")
    return ser

def parse_time_str(tstr):
    try:
        val = float(tstr)
        secs = int(val)
        ms = int(round((val - secs) * 1000))
        return val, secs, ms
    except Exception:
        return None, None, None