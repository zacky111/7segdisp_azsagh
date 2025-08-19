import serial

from src.comm.config import PORT, BAUD, parity, stopbits, bytesize, timeout

def ser_init():
    ser = serial.Serial(PORT, BAUD, parity,
                    stopbits,
                    bytesize,
                    timeout)
    print(f"Otwarty port: {ser.portstr}")
    return ser