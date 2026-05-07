import sys
sys.path.insert(0, r"f:\__repos__\GEM_suite\A1_manager")

import serial
import time

PORT = "COM4"

ser = serial.Serial(
    port=PORT,
    baudrate=9600,
    timeout=1.0,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
)
time.sleep(2)
ser.reset_input_buffer()
print(f"Opened {PORT}")

def raw_send(cmd, wait=1.0):
    ser.reset_input_buffer()
    full = (cmd + '\r').encode('ascii')
    print(f"\n>>> Sending: {full}")
    ser.write(full)
    ser.flush()
    time.sleep(wait)
    resp = ser.read(ser.in_waiting or 1)
    print(f"<<< Response ({len(resp)} bytes): {resp!r}  hex={resp.hex()}")
    return resp

# Try char-by-char sending like _send_command does
def char_send(cmd, delay=0.005, wait=1.0):
    ser.reset_input_buffer()
    print(f"\n>>> char-by-char: '{cmd}'")
    for c in cmd:
        ser.write(c.encode('ascii'))
        ser.flush()
        time.sleep(delay)
    ser.write(b'\r')
    ser.flush()
    time.sleep(wait)
    resp = ser.read(ser.in_waiting or 1)
    print(f"<<< Response: {resp!r}")

char_send('j1000')
char_send('i500')
char_send('k500')
char_send('K')

ser.close()
print("\nDone.")
