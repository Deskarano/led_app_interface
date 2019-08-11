P_SUCCESS = 'success'
P_FAILURE = 'failed'
P_TEST_CONNECTION = 'test_connect'
P_CLOSE_CONNECTION = 'close_connect'

P_MODE_ANIMATIONS = 'mode_anims'
P_MODE_AREAS = 'mode_areas'
P_MODE_IDLE = 'mode_idle'

P_REQUEST_QUEUE = 'request_queue'
P_REQUEST_AREAS = 'request_areas'
P_REQUEST_STRIP_SIZE = 'request_strip_size'

P_CREATE_AREA = 'create_area'
P_EDIT_AREA = 'edit_area'
P_EDIT_AREA_NAME = 'name'
P_EDIT_AREA_COLOR = 'color'
P_EDIT_AREA_BOUNDS = 'bounds'
P_DELETE_AREA = 'delete_area'
P_DISPLAY_AREA = 'display_area'
P_SET_AREA_VISIBLE = 'set_area_visible'

P_ADD_ANIMATION = 'add_anim'
P_PLAY_ANIMATION = 'play_anim'
P_PAUSE_ANIMATION = 'pause_anim'
P_STOP_ANIMATION = 'stop_anim'
P_TOGGLE_ANIMATION = 'toggle_anim'

P_SUBSCRIBE_TO_ANIM = 'subscribe_anim'
P_SUB_EVENT_TICK = 'tick'
P_SUB_EVENT_STATE = 'state'


def socket_encode(value):
    result = (str(value) + '\n').encode('UTF-8')
    return result


def socket_decode(value):
    result = value.decode('UTF-8').strip()
    return result


def send_tick(client, anim_id, t):
    client.send(socket_encode(anim_id + '\\' + P_SUB_EVENT_TICK + '\\' + str(t)))


def send_state(client, anim_id, s):
    client.send(socket_encode(anim_id + "\\" + P_SUB_EVENT_STATE + '\\' + str(s)))
