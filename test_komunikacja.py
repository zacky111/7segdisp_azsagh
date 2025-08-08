import serial

# Otwórz port szeregowy
ser = serial.Serial(
    port='/dev/ttyUSB0',
    baudrate=1200,  # ustaw zgodnie z dokumentacją Microgate RaceTime2
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)

print(f"Otwarty port: {ser.portstr}")

try:
    currentData=[]
    while True:
        if ser.in_waiting:  # jeśli są dane w buforze
            data = ser.read(ser.in_waiting)  
            currentData.append(data)

            if currentData[-1] =='\r':

                print(currentData)
                currentData = []
                
except KeyboardInterrupt:
    print("\nZamykam...")
    ser.close()
