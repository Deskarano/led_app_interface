import socket
from threading import Thread

from net import protocol


def socket_encode(value):
    return (str(value) + '\n').encode('UTF-8')


def socket_decode(value):
    return value.decode('UTF-8').strip()


class ForwardThread(Thread):
    def __init__(self, from_socket, from_name, to_socket, to_name):
        Thread.__init__(self)

        self.from_socket = from_socket
        self.to_socket = to_socket

        self.from_name = from_name
        self.to_name = to_name

    def run(self):
        while True:
            msg = self.from_socket.recv(8192)

            if msg == b'':
                break

            print(self.from_name, '->', self.to_name, ': forwarding', socket_decode(msg))
            self.to_socket.send(msg)

        print(self.from_name, '->', self.to_name, ': stopping')


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('', 9989))
server_socket.listen(5)

port = input('port > ')
print('listening')

while True:
    (client_socket, address) = server_socket.accept()

    to_pi = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    to_pi.connect(('192.168.13.180', int(port)))

    emulator_to_pi = ForwardThread(client_socket, 'emulator', to_pi, 'pi')
    pi_to_emulator = ForwardThread(to_pi, 'pi', client_socket, 'emulator')

    emulator_to_pi.start()
    pi_to_emulator.start()

    while emulator_to_pi.is_alive():
        pass

    to_pi.send(socket_encode(protocol.P_CLOSE_CONNECTION))

    while pi_to_emulator.is_alive():
        pass
