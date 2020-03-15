import serial.tools.list_ports


def get_port(text, port=None):
    ports = serial.tools.list_ports.comports()

    if port is None:
        if text is not None:
            print(text)

        for i in range(len(ports)):
            print("\t{:2d} - {:s}".format(i, ports[i].device))

        port = int(input("Select port:  "))

    return ports[port].device


if __name__ == '__main__':
    print(get_port("Testing:"))
