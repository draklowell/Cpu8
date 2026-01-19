import time

from serial import Serial

PORT = "/dev/ttyUSB0"
BAUDRATE = 115200
OUTPUT = "log.csv"

with Serial(PORT, BAUDRATE) as com:
    with open(OUTPUT, "wb") as f:
        for line in com:
            f.write(line)
            f.flush()
            print(line.decode("utf8", errors="ignore"), end=" ")
