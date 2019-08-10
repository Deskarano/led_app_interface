import socket
from threading import Thread

from net import protocol


def socket_encode(value):
    return (str(value) + '\n').encode('UTF-8')


def socket_decode(value):
    return value.decode('UTF-8').strip()


class ForwardThread(Thread):
    def __init__(self, from_socket, from_name, to_socket, to_name, count):
        super().__init__()

        self.from_socket = from_socket
        self.to_socket = to_socket

        self.from_name = from_name
        self.to_name = to_name

        self.count = count

    def run(self):
        while True:
            msg = self.from_socket.recv(1024)
            if msg == b'':
                break

            print(self.from_name, '->', self.to_name, '(', self.count, '): forwarding', socket_decode(msg))
            self.to_socket.send(msg)

        self.to_socket.send(socket_encode(protocol.P_CLOSE_CONNECTION))
        print(self.from_name, '->', self.to_name, '(', self.count, '): stopping')


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('', 9989))
server_socket.listen(5)

port = input('port > ')
print('listening')

count = 0

while True:
    (client_socket, address) = server_socket.accept()

    print('got a connection! creating threads for count', count)

    to_pi = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    to_pi.connect(('172.16.11.58', int(port)))

    emulator_to_pi = ForwardThread(client_socket, 'emulator', to_pi, 'pi', count)
    pi_to_emulator = ForwardThread(to_pi, 'pi', client_socket, 'emulator', count)

    emulator_to_pi.start()
    pi_to_emulator.start()
    #
    # while emulator_to_pi.is_alive():
    #     pass
    #
    # to_pi.send(socket_encode(protocol.P_CLOSE_CONNECTION))
    #
    # while pi_to_emulator.is_alive():
    #     pass

    count += 1