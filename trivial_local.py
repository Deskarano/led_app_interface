import socket
from net import protocol
from threading import Thread, get_ident


def socket_encode(value):
    result = (str(value) + '\n').encode('UTF-8')
    return result


def socket_decode(value):
    result = value.decode('UTF-8').strip()
    return result


class ClientThread(Thread):
    def __init__(self, client):
        Thread.__init__(self)

        self.client = client

    def run(self):
        print(str(get_ident()), 'started')
        while True:
            command = self.client.recv(8192)

            if command == b'':
                break

            command = socket_decode(command)

            print(str(get_ident()), 'received command:', command)
            split_command = command.split('\\')

            if split_command[0] in (protocol.P_REQUEST_QUEUE, protocol.P_REQUEST_AREAS):
                self.client.send(socket_encode('0'))
            else:
                self.client.send(socket_encode(protocol.P_SUCCESS))

        print(str(get_ident()), 'closing')


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('', 9989))
server_socket.listen(5)

print('listening')

while True:
    (client_socket, address) = server_socket.accept()
    ClientThread(client_socket).start()
