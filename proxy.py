# -*- coding: utf-8 -*-
""" The Command line utility used to test the serial channel 
    of the electromagnetic compensator KF1.

    Author: Aleksandr Smirnov
"""

from collections import deque
from dataclasses import dataclass
import glob
from functools import reduce
import sys

import serial

'''
This protocols for communication between system CM2/AMK21 and CED KF1/1M

Format "CM":
| Header (3 bytes) | Data (variable) | Checksum (1 bytes) | End (2 bytes)|
    where DATA = | Channel | Value | ... | Channel43/150 | Value43/150 |

Format "AMK" 
| Header (3 bytes) | Number Channels (1 bytes) | Data (variable) | Checksum (1 bytes) | End (2 bytes)|
    where DATA = | Channel | Value | ... | Channel43/150 | Value43/150 |
'''

protocols = {
    "input": {"header": "$01", "end": "\r\n", "count_bytes": False},
    "output": {
        "cm": {"header": "$CM", "end": "\r\n", "count_bytes": False},
        "amk": {"header": "$CM", "end": "\r\n", "count_bytes": True}
    }
}


QUEUE = deque(maxlen=1)
QUEUE_INPUT = deque(maxlen=1)


def scan(n=256):
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(n)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


def create_message(values, protocol):
    """ This function used to create message from data and bytes-string """
    sequence_bytes = [protocol['header'].encode()]
    if protocol['count_bytes']:
        cb = (len(values)).to_bytes(1, byteorder='big')
        sequence_bytes.append(cb)
    sequence_bytes.extend(databytes(values))
    sequence_bytes.append(checksum(sequence_bytes))
    sequence_bytes.append(protocol['end'].encode())
    return b"".join(sequence_bytes)


def databytes(data):
    db = []
    for index, value in enumerate(data, 1):
        index_byte = index.to_bytes(1, byteorder='big')
        value_bytes = value.to_bytes(2, byteorder='big', signed=True)
        db.extend([index_byte, value_bytes])
    return db


def checksum(data, module=256):
    """ Calculate checksum and return in the bytes """
    seq_bytes = b"".join(data)
    return (reduce(lambda x, y: x + y, seq_bytes) % module).to_bytes(1, byteorder='big')


def parse_message(message: bytes):
    """ This function used to parse data from message. 
        Fetch data from message and return list of values
    """
    data = message[3:-2]
    values = [int.from_bytes(b, byteorder='big', signed=True) for b in split_seq(data)]
    return values


def split_seq(seq, start=1, stop=3):
    """ This generator split sequence on part (start:stop) and return generator """
    while seq:
        yield seq[start:stop]
        seq = seq[stop:]


def message_pattern(pattern, imax=9.99, *, as_voltage=False):
    """ This function generate pattern and return it as generator
    :param pattern:
    """
    kwarg = {
        "Max": int(imax * 100),
        "Min": -int(imax * 100),
        "Null": 0
    }
    return [kwarg[key] if key != 'L' else key for key in pattern]

@dataclass
class PatternHandler:
    """ This class represents a hook. 
    It changes data in the message with specified pattern 
    and returns a new data.
    """
    pattern: list = None
    channels: int = None

    def __post_init__(self):
        self.pattern = self.pattern[:self.channels]

    def __call__(self, data):
        return self._handle(data)

    def _handle(self, data: list) -> list:
        value = data[0]
        data_changed = [value if i == 'L' else i for i in self.pattern]

        return data_changed


@dataclass
class VoltageHandler:
    """ This handler convert all values in data to current
    and return list of values"""
    
    imax: float = 9.99
    vmax: float = 300
    ku: float = 1            # Coefficient corect ADC values

    def __call__(self, data):
        return self._handler(data)

    def _handler(self, data):
        res = []
        for value in data:
            res.append(int((self.imax / self.vmax) * self.ku * value) * 100)
        return res

#TODO: Make function read message from com-port 
def read():
    input_data = [300, 0, 0, 0, 0, 0]
    message = create_message(input_data, protocol=protocols['input'])
    print("read: ", message.hex())
    return message

#TODO: Make function write message to com-port
def write(message):
    msg = message.hex()
    length = len(message)
    print(f"out: {length} : {msg}")

def write_to_serial(message):
    with serial.Serial as sobj:
        sobj.writelines(message)


class VirtualPort(serial.Serial):
    def __init__(self, *args, **kwargs):
        super(VirtualPort, self).__init__()
        input_data = [300, 0, 0, 0, 0, 0]
        self.message = create_message(input_data, protocol=protocols['input'])

    def read(self, size=1):
        return self.message

    def write(self, message):
        msg = message.hex()
        length =  len(message)
        print(f"send: {length=}, {msg=}\n")


def redirect(reader, writter, handlers, dbytes=False):
    """ This function read message from reader and redirect it to writter."""
    message = reader.read()

    data = parse_message(message)
    QUEUE_INPUT.append(data)

    if handlers:
        for handler in handlers:
            data = handler(data)

    QUEUE.append(data)


    if dbytes:
        protocol_name = 'amk'
    else:
        protocol_name = 'cm'

    message = create_message(data, protocol=protocols['output'][protocol_name])

    writter.write(message)

    return message


def run(pattern, settings):
    pattern = message_pattern(pattern, imax=(settings['imax'] - 0.01))
    handlers = []
    handlers.append(VoltageHandler(imax=settings['imax']))
    handlers.append(PatternHandler(pattern=pattern, channels=settings['channels']))

    pin = settings['port_input']
    pout = settings['port_output']

    if pin == 'VCOM':
        reader = VirtualPort()
    else:
        reader = serial.Serial(port=pin)

    if pout == 'VCOM':
        writter = VirtualPort()
    else:
        writter = serial.Serial(port=pout)

    redirect(reader, writter, handlers, dbytes=settings['channels_byte'])


def main():
    pattern = message_pattern()
    run(pattern)


if __name__ == "__main__":
    main()
