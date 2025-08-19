import serial

PORT = '/dev/ttyUSB0'
BAUD = 1200
parity=serial.PARITY_NONE,
stopbits=serial.STOPBITS_ONE
bytesize=serial.EIGHTBITS
timeout=1