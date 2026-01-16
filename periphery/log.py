from serial import Serial
import time

PORT = "/dev/ttyUSB0"
BAUDRATE = 115200
OUTPUT = "log.csv"

with Serial(PORT, BAUDRATE) as com:
    with open(OUTPUT, "wb") as f:
        for line in com:
            f.write(str(int(time.time() * 1000)).encode("utf-8") + b",")
            f.write(line + b"\n")
            f.flush()
            print(line.decode("utf8", errors="ignore"))