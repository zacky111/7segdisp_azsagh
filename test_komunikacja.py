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
    currentData=[]
    while True:
        if ser.in_waiting > 0:  # jeśli są dane w buforze
            print(data.hex())
            data = ser.read(ser.in_waiting)  
            currentData.append(data)

            if currentData[-1] =='\r':
                print(currentData)
                currentData=[]

except KeyboardInterrupt:
    print("\nZamykam...")
    ser.close()
