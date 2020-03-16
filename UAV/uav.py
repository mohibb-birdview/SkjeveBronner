#!/usr/bin/env python3

import random
import time
import struct

import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.modbus_rtu as modbus_rtu
import modbus_tk.exceptions
import modbus_tk.modbus
import numpy as np
import serial
import serial.tools.list_ports

from Functions import functions

GCS_PORT = 1
MODBUS_PORT = 1


class Modbus:
    def __init__(self,
                 serial_port=None,
                 baudrate=19200,
                 timeout=0.52,
                 address=0x00,
                 unit=1
                 ):

        port = functions.get_port("UAV-Modbus port: ", port=serial_port)
        con = serial.Serial(port, baudrate=baudrate, bytesize=8, parity='N', stopbits=1, xonxoff=0)

        self.master = modbus_rtu.RtuMaster(con)
        self.master.set_timeout(timeout)
        self.master.set_verbose(True)

        self.x = 0
        self.y = 0

    def get_data(self):
        try:
            n = 5
            f = ">" + "f" * n
            data = self.master.execute(
                slave=1,
                function_code=cst.READ_INPUT_REGISTERS,
                starting_address=1006,
                quantity_of_x=2 * n,
                data_format=f
            )

            self.x = data[3]
            self.y = data[4]

        except modbus_tk.modbus.ModbusError as e:
            print("%s- Code=%d" % (e, e.get_exception_code()))

        except modbus_tk.exceptions.ModbusInvalidResponseError as e:
            print(e)

        return self.x, self.y

    def get_message(self):
        return "X{:+010.5f}Y{:+010.5f}".format(self.x, self.y)

    def __enter__(self, *argv):
        return self

    def __exit__(self, *argv):
        pass

    def flushInput(self):
        pass


def main():
    time_to_wait = 1.0

    gcs_port = functions.get_port("UAV-GCS port")
    dt = 1
    last_time = time.time()

    with Modbus(serial_port=MODBUS_PORT) as wh:
        with serial.Serial(gcs_port, baudrate=19200, bytesize=8, parity='N', stopbits=1, xonxoff=0) as gcs:
            while True:
                wh.flushInput()
                gcs.flushOutput()

                wh.get_data()
                message = wh.get_message()
                if message is None:
                    continue

                new_message = "M" + message
                gcs.write(new_message.encode())

                print("Read Message:\t {:s}".format(message))
                print("New Message:\t{:s}\t\tdt:{:2.1f}".format(new_message, 1/dt))
                print()

                dt = time.time() - last_time
                while dt < time_to_wait:
                    dt = time.time() - last_time
                last_time = time.time()

if __name__ == '__main__':
    main()
