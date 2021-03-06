import socket
import neopixel
import queue

from net import protocol
from file import file_utils, config_utils
from threading import Thread

from led_tools import player


class ClientThread(Thread):
    def __init__(self, client, player, thread_id):
        Thread.__init__(self)

        self.client = client
        self.player = player

        self.thread_id = thread_id
        self.subscribed_ids = []

    def stop_connect(self):
        for anim_id in self.subscribed_ids:
            print('[NETWORK', self.thread_id, ']: unsubscribing from animation', anim_id)
            self.player.unsub_from_anim(anim_id)

    def run(self):
        while True:
            try:
                command = self.client.recv(1024)

            except ConnectionResetError:
                self.stop_connect()
                break

            if command == b'':
                self.stop_connect()
                break

            command = protocol.socket_decode(command)

            print('[NETWORK', self.thread_id, ']: received command: ' + command)
            split_command = command.split('\\')

            # connection commands
            if split_command[0] == protocol.P_TEST_CONNECTION:
                print('[NETWORK', self.thread_id, ']: responding success')
                self.client.send(protocol.socket_encode(protocol.P_SUCCESS))

            elif split_command[0] == protocol.P_CLOSE_CONNECTION:
                print('[NETWORK', self.thread_id, ']: closing connection')
                self.stop_connect()
                self.client.close()
                break

            # request commands
            elif split_command[0] == protocol.P_REQUEST_QUEUE:
                print('[NETWORK', self.thread_id, ']: responding with queue entries')

                queue_entries = self.player.get_anim_queue()
                self.client.send(protocol.socket_encode(len(queue_entries)))

                for entry in queue_entries:
                    self.client.send(protocol.socket_encode(entry))

            elif split_command[0] == protocol.P_REQUEST_AREAS:
                print('[NETWORK', self.thread_id, ']: responding with area entries')

                areas = file_utils.get_areas()
                self.client.send(protocol.socket_encode(len(areas)))

                for area in areas:
                    self.client.send(protocol.socket_encode(areas[area]))

            elif split_command[0] == protocol.P_REQUEST_STRIP_SIZE:
                print('[NETWORK', self.thread_id, ']: responding with strip size')
                self.client.send(protocol.socket_encode(self.player.strip.numPixels()))

            # mode commands
            elif split_command[0] == protocol.P_MODE_ANIMATIONS:
                print('[NETWORK', self.thread_id, ']:invisible setting player mode to animations')

                self.player.set_mode(led_player.MODE_ANIMATION)
                self.client.send(protocol.socket_encode(protocol.P_SUCCESS))

            elif split_command[0] == protocol.P_MODE_AREAS:
                print('[NETWORK', self.thread_id, ']: setting player mode to areas')

                self.player.set_mode(led_player.MODE_AREA)
                self.client.send(protocol.socket_encode(protocol.P_SUCCESS))

            elif split_command[0] == protocol.P_MODE_IDLE:
                print('[NETWORK', self.thread_id, ']: setting player mode to idle')

                self.player.set_mode(led_player.MODE_IDLE)
                self.client.send(protocol.socket_encode(protocol.P_SUCCESS))

            # area commands
            elif split_command[0] == protocol.P_CREATE_AREA:
                print('[NETWORK', self.thread_id, ']: creating area')

                file_utils.set_file_config(file_utils.AREA_PATH,
                                           split_command[1],
                                           split_command[2])

                client_socket.send(protocol.socket_encode(protocol.P_SUCCESS))

            elif split_command[0] == protocol.P_EDIT_AREA:
                print('[NETWORK', self.thread_id, ']: editing area')

                area_config = file_utils.get_file_config(file_utils.AREA_PATH, split_command[2])

                if split_command[1] == protocol.P_EDIT_AREA_NAME:
                    result = config_utils.edit_param(area_config,
                                                     config_utils.AREA_ENTRY,
                                                     config_utils.AREA_NAME,
                                                     split_command[3])

                elif split_command[1] == protocol.P_EDIT_AREA_COLOR:
                    result = config_utils.edit_param(area_config,
                                                     config_utils.AREA_COLOR,
                                                     config_utils.AREA_COLOR_VAL,
                                                     split_command[3])

                elif split_command[1] == protocol.P_EDIT_AREA_BOUNDS:
                    result = config_utils.edit_param(area_config,
                                                     config_utils.AREA_BLOCK,
                                                     config_utils.AREA_START_VAL,
                                                     split_command[3])

                    result = config_utils.edit_param(result,
                                                     config_utils.AREA_BLOCK,
                                                     config_utils.AREA_END_VAL,
                                                     split_command[4])
                else:
                    result = ''

                if result == '':
                    self.client.send(protocol.socket_encode(protocol.P_FAILURE))
                    print('[NETWORK', self.thread_id, ']: failed to edit area')

                else:
                    file_utils.set_file_config(file_utils.AREA_PATH, split_command[2], result)
                    self.client.send(protocol.socket_encode(protocol.P_SUCCESS))
                    print('[NETWORK', self.thread_id, ']: successfully edited area')

            elif split_command[0] == protocol.P_DELETE_AREA:
                print('[NETWORK', self.thread_id, ']: deleting area')

                result = file_utils.delete_file(file_utils.AREA_PATH, split_command[1])
                self.player.delete_area(split_command[1])

                if result:
                    self.client.send(protocol.socket_encode(protocol.P_SUCCESS))
                    print('[NETWORK', self.thread_id, ']: successfully deleted area')
                else:
                    self.client.send(protocol.socket_encode(protocol.P_FAILURE))
                    print('[NETWORK', self.thread_id, ']: failed to delete area')

            # display commands
            elif split_command[0] == protocol.P_DISPLAY_AREA:
                print('[NETWORK', self.thread_id, ']: displaying area')
                self.player.display_area(split_command[1],
                                         int(split_command[2]),
                                         int(split_command[3]),
                                         int(split_command[4], 16))

                self.client.send(protocol.socket_encode(protocol.P_SUCCESS))

            elif split_command[0] == protocol.P_SET_AREA_VISIBLE:
                if split_command[2] == 'true':
                    print('[NETWORK', self.thread_id, ']: making area visible')

                    self.player.set_area_visible(split_command[1], True)
                    self.client.send(protocol.socket_encode(protocol.P_SUCCESS))

                elif split_command[2] == 'false':
                    print('[NETWORK', self.thread_id, ']: making area invisible')

                    self.player.set_area_visible(split_command[1], False)
                    self.client.send(protocol.socket_encode(protocol.P_SUCCESS))

                else:
                    print('[NETWORK', self.thread_id, ']: failed to change area visibility')
                    self.client.send(protocol.socket_encode(protocol.P_FAILURE))

            # animation commands
            elif split_command[0] == protocol.P_ADD_ANIMATION:
                print('[NETWORK', self.thread_id, ']: adding animation')

                self.player.add_anim(split_command[1], split_command[2], split_command[3], split_command[4])
                self.client.send(protocol.socket_encode(protocol.P_SUCCESS))

            elif split_command[0] == protocol.P_PLAY_ANIMATION:
                print('[NETWORK', self.thread_id, ']: playing animation', split_command[1])
                self.player.play_anim(split_command[1])
                self.client.send(protocol.socket_encode(protocol.P_SUCCESS))

            elif split_command[0] == protocol.P_PAUSE_ANIMATION:
                print('[NETWORK', self.thread_id, ']: pausing animation', split_command[1])
                self.player.pause_anim(split_command[1])
                self.client.send(protocol.socket_encode(protocol.P_SUCCESS))

            elif split_command[0] == protocol.P_STOP_ANIMATION:
                print('[NETWORK', self.thread_id, ']: stopping animation', split_command[1])
                self.player.stop_anim(split_command[1])
                self.client.send(protocol.socket_encode(protocol.P_SUCCESS))

            elif split_command[0] == protocol.P_TOGGLE_ANIMATION:
                if split_command[2] == 'true':
                    print('[NETWORK', self.thread_id, ']: making animation visible')

                    self.player.set_anim_visible(split_command[1], True)
                    self.client.send(protocol.socket_encode(protocol.P_SUCCESS))

                elif split_command[2] == 'false':
                    print('[NETWORK', self.thread_id, ']: making animation invisible')

                    self.player.set_anim_visible(split_command[1], False)
                    self.client.send(protocol.socket_encode(protocol.P_SUCCESS))

                else:
                    print('[NETWORK', self.thread_id, ']: failed to change animation visibility')
                    self.client.send(protocol.socket_encode(protocol.P_FAILURE))

            elif split_command[0] == protocol.P_SUBSCRIBE_TO_ANIM:
                print('[NETWORK', self.thread_id, ']: subscribing to events from animation', split_command[1])
                self.client.settimeout(.008)
                self.subscribed_ids.append(split_command[1])
                msg_queue = self.player.sub_to_anim(split_command[1], self.client)
                self.client.send(protocol.socket_encode(protocol.P_SUCCESS))

                while True:
                    try:
                        msg = self.client.recv(1024)
                        if msg == b'':
                            self.stop_connect()
                            break
                        else:
                            # any message we receive at this point should fail
                            self.client.send(protocol.socket_encode(protocol.P_FAILURE))

                    except socket.timeout:
                        try:
                            msg = msg_queue.get(True, .008)

                            if msg == 'tick':
                                opt = msg_queue.get(True, .008)
                                self.client.send(protocol.socket_encode(split_command[1] + '\\' +
                                                                        protocol.P_SUB_EVENT_TICK + '\\' +
                                                                        str(opt)))
                            else:
                                self.client.send(protocol.socket_encode(split_command[1] + '\\' +
                                                                        protocol.P_SUB_EVENT_STATE + '\\' +
                                                                        msg))

                        except queue.Empty:
                            # nothing to do, just no messages available
                            pass

                break

            else:
                print('[NETWORK', self.thread_id, ']: unrecognized command')
                self.client.send(protocol.socket_encode(protocol.P_FAILURE))

        print('[NETWORK', self.thread_id, ']: thread exiting')


# start parameters
port = 9989
gpio = 21
num = 300

strip = neopixel.Adafruit_NeoPixel(int(num), int(gpio), strip_type=neopixel.ws.WS2811_STRIP_GRB)
strip.begin()

led_player = player.Player(strip, 60)

client_thread_id = 0

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('', int(port)))
server_socket.listen(5)

print('[NETWORK]: listening')

while True:
    (client_socket, address) = server_socket.accept()
    print('[NETWORK]: got client with address', str(address))
    print('[NETWORK]: assigning thread', client_thread_id, 'to client', str(address))

    ClientThread(client_socket, led_player, client_thread_id).start()
    client_thread_id += 1
