import pigpio
import time

class WS2812Strip:
    def __init__(self, gpio, led_count, brightness=1.0):
        self.gpio = gpio
        self.led_count = led_count
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("pigpio daemon not running")

        self.brightness = max(0.0, min(1.0, brightness))
        self.buffer = [(0, 0, 0)] * led_count

    def set_pixel(self, i, color):
        r, g, b = color
        self.buffer[i] = (
            int(r * self.brightness),
            int(g * self.brightness),
            int(b * self.brightness),
        )

    def show(self):
        pulses = []
        for r, g, b in self.buffer:
            for byte in (g, r, b):  # GRB
                for bit in range(7, -1, -1):
                    if byte & (1 << bit):
                        pulses.append(pigpio.pulse(1 << self.gpio, 0, 800))
                        pulses.append(pigpio.pulse(0, 1 << self.gpio, 450))
                    else:
                        pulses.append(pigpio.pulse(1 << self.gpio, 0, 400))
                        pulses.append(pigpio.pulse(0, 1 << self.gpio, 850))

        self.pi.wave_add_generic(pulses)
        wid = self.pi.wave_create()
        self.pi.wave_send_once(wid)
        while self.pi.wave_tx_busy():
            time.sleep(0.001)
        self.pi.wave_delete(wid)

    def clear(self):
        self.buffer = [(0, 0, 0)] * self.led_count
        self.show()
