#!/usr/bin/env bash

THRESHOLD=60       # temperatura w °C
INTERVAL=30         # interwał sprawdzania [s]
TARGET_SERVICE="7seg.service"

while true; do
    TEMP=$(vcgencmd measure_temp | grep -oE '[0-9]+\.[0-9]+')

    if (( $(echo "$TEMP > $THRESHOLD" | bc -l) )); then
        logger "TEMP-WATCHDOG: WARNING – High temperature ${TEMP}°C"

        # 1. Zatrzymanie głównej usługi
        logger "TEMP-WATCHDOG: Stopping ${TARGET_SERVICE}"
        systemctl stop "$TARGET_SERVICE"

        # 2. Odczekanie chwili
        sleep 3

        # 3. Sprawdzenie, czy usługa faktycznie padła
        if systemctl is-active --quiet "$TARGET_SERVICE"; then
            logger "TEMP-WATCHDOG: Service still running – forcing kill"
            systemctl kill "$TARGET_SERVICE"
        else
            logger "TEMP-WATCHDOG: Service stopped cleanly"
        fi

        # 4. Shutdown systemu
        logger "TEMP-WATCHDOG: System shutting down due to overtemperature"
        /usr/sbin/shutdown -h now
        exit 0
    fi

    sleep "$INTERVAL"
done
