import random
import time

import modbus_tk.defines as cst
import numpy as np
import serial
import serial.tools.list_ports
from modbus_tk import modbus_rtu

from Functions import functions


class WaveSignal:
    def __init__(self):
        self.x_rand = random.random() * 2 * np.pi * 1
        self.y_rand = random.random() * 2 * np.pi * 1

        self.x_freq = 1
        self.y_freq = 1

        self.x_amp = 2
        self.y_amp = 2

    def get_signal(self, t):
        x = 1 * self.x_amp * np.sin(self.x_freq * t + self.x_rand)
        y = 1 * self.y_amp * np.sin(self.y_freq * t + self.y_rand)

        x = int(x*1000) + self.x_amp*1000
        y = int(y*1000) + self.y_amp*1000

        return x, y

def main():
    print("Creating modbus server")
    port = functions.get_port("Modbus Server Port")
    con = serial.Serial(port=port, baudrate=57600, bytesize=8, parity='N', stopbits=1, xonxoff=0)
    server = modbus_rtu.RtuServer(con)
    server.set_timeout(0.1)
    server.set_verbose(False)

    print("Starting Server on port: " + port)
    server.start()

    print("Adding Slave")
    slave1 = server.add_slave(1)

    print("Adding Blocks")
    n = 2
    slave1.add_block("c", cst.COILS, 0, n)
    slave1.add_block("d", cst.DISCRETE_INPUTS, 0, n)
    slave1.add_block("b", cst.HOLDING_REGISTERS, 0, n)


    print("Running Server\n")
    time.sleep(1)

    try:
        t_start = time.time()
        signal = WaveSignal()

        while True:
            t = time.time() - 0
            new_signal = signal.get_signal(t)
            slave1.set_values("b", 0x00, new_signal)
            print(new_signal)

            time.sleep(0.1)

    except KeyboardInterrupt as e:
        print(e)

    finally:
        print("Stopping server.")
        server.stop()


if __name__ == '__main__':
    main()