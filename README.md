# 7-Segment RaceTime Display System

![Men slaloming](images/slalom1.jpg)

## Project Overview
This project is the practical implementation of my engineering thesis, focused on building a **real-time sports timing and visualization system**.  
It integrates with the **RaceTime** timing device and uses a **Raspberry Pi** as the central controller to:

- receive and parse data frames from RaceTime,
- compute and synchronize the race time,
- display results on a **7-segment LED display**,
- handle additional visual signals (status LEDs).

The system was designed for **sports competitions**, ensuring clear, reliable, and immediate feedback for athletes and organizers.  
It is optimized to run in a **standalone mode**, starting automatically on boot and tolerant to sudden power-offs.

---

## Key Features
- **Real-time display** of RaceTime measurements.  
- Automatic detection of race events:  
  - **Start** → measurement begins,  
  - **Finish** → time stops, blinks for 5 seconds, then clears,  
  - **No signal** → warning indication on the rightmost digit.  
- **Error handling**: time drift correction based on RaceTime sync frames.  
- **Auto-start on boot** with `systemd`.  
- Power-loss resistant (read-only filesystem logs, no manual shutdown required).  

---

## Technologies Used
- **Python 3.11** – main implementation language  
- **RPi.GPIO** – Raspberry Pi GPIO control  
- **pySerial** – communication with RaceTime device  
- **rpi_ws281x** – WS2812B LED strip driver for 7-segment display  
- **systemd** – service management for auto-start  
- **GitHub** – version control and documentation  

---

## System Architecture

The system is divided into **three cooperating layers**:

1. **Input (Communication Layer)**  
   - The RaceTime device sends data frames through a USB–UART interface (`/dev/ttyUSB0`).  
   - A dedicated **communication thread** (`comm_func`) continuously reads incoming frames.  
   - Frames are parsed into start/finish events or synchronization packets.  
   - Shared state variables (`running`, `finished`, `start_time_local`, etc.) are updated under a lock to avoid race conditions.

2. **Processing (Control Logic)**  
   - A **timekeeping mechanism** ensures that the display remains synchronized with RaceTime:  
     - On **start**: the local timer begins counting.  
     - On **finish**: the time freezes and blinks for a few seconds.  
     - On **no data**: a warning symbol is shown.  
   - A drift correction algorithm realigns the local clock with RaceTime using periodic sync frames.

3. **Output (Display Layer)**  
   - A **display thread** (`display_func`) updates two LED strips configured as 7-segment digits.  
   - The system supports:  
     - Suppressing leading zeros,  
     - Showing minutes only when > 0,  
     - Blinking finish times,  
     - Warning signal if communication is lost.  
   - GPIO pins also control **status LEDs (dots)** for additional feedback.

---


## Project structure

```
7segdisp_azsagh/
├── 7seg.log
├── 7seg.service
├── main.py
├── old             #test files, to be removed after finish of implementation ;)
│   ├── test_komunikacja.py
│   ├── test_led_2tasmy.py
│   └── test_led.py
├── README.md
├── requirements.txt
├── src
│   ├── comm
│   │   ├── config.py
│   │   └── util.py
│   ├── dot
│   │   ├── config.py
│   │   └── util.py
│   └── stripe
│       ├── config.py
│       └── util.py
└── venv
    └── ...
```

## Installation & Usage
Clone the repository and create a Python virtual environment:
```bash
git clone https://github.com/zacky111/7segdisp_azsagh.git
cd 7segdisp_azsagh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run the program manually:

``` bash
sudo /venv/bin/python3 main.py
```

Or enable auto-start on boot (systemd service) - sollution possible on RaspberryPi:

``` bash
sudo cp 7seg.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable 7seg.service
sudo systemctl start 7seg.service
```


## Author
**Jakub Ciura** - Automation and Robotics student of AGH University.

This project was originally developed as part of my engineering thesis - *Design of a Device Cooperating with Sports Timing Systems* - and extended for practical deployment.