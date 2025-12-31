import serial

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
    
def check_serial_alive(ser):
    try:
        # lekkie zapytanie – NIC nie wysyła do urządzenia
        ser.in_waiting
        return True
    except (OSError, serial.SerialException):
        return False
    
def check_rs232_lines(ser):
    try:
        return {
            "DSR": ser.getDSR(),
            "CTS": ser.getCTS(),
            "CD":  ser.getCD()
        }
    except (OSError, serial.SerialException):
        return None