import serial

from config import PORT, BAUD, parity, stopbits, bytesize, timeout

def ser_init():
    ser = serial.Serial(PORT, BAUD, parity=parity,
                    stopbits=stopbits,
                    bytesize=bytesize,
                    timeout=timeout)
    print(f"Otwarty port: {ser.portstr}")
    return ser