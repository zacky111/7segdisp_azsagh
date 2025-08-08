import serial

# Otwórz port szeregowy
ser = serial.Serial(
port='/dev/ttyUSB0',  
baudrate=9600,        
bytesize=serial.EIGHTBITS,  
parity=serial.PARITY_NONE,  
stopbits=serial.STOPBITS_ONE,  
timeout=1  
)

print(f"Otwarty port: {ser.portstr}")

try:
    while True:
        if ser.in_waiting:  # jeśli są dane w buforze
            line = ser.readline().decode(errors='ignore').strip()
            if line:
                print(f"Odebrano: {line}")
except KeyboardInterrupt:
    print("\nZamykam...")
    ser.close()
