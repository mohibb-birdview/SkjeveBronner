import serial.tools.list_ports
import random
import string


def get_port(text, port=None):
    ports = serial.tools.list_ports.comports()

    if port is None:
        if text is not None:
            print(text)

        for i in range(len(ports)):
            print("\t{:2d} - {:s}".format(i, ports[i].device))

        port = int(input("Select port:  "))

    return ports[port].device


def test_connection():
    baudrate = 57600

    ser_send = get_port("Sending")
    ser_rec = get_port("Receiving")

    with serial.Serial(ser_send, baudrate, timeout=1) as send:
        with serial.Serial(ser_rec, baudrate, timeout=1) as receive:
            send.flushOutput()
            receive.flushInput()

            N = random.randint(50, 100)
            send_message = ''.join(random.choice(string.printable) for _ in range(N))

            send.write(send_message.encode())
            rec_message = receive.read(len(send_message)).decode()

    print("Sent Message:   \t", send_message)
    print("Receive Message:\t", rec_message)
    print()

    if send_message == rec_message:
        print("Connection operational")
    else:
        print("Connection failed")


if __name__ == '__main__':
    test_connection()
