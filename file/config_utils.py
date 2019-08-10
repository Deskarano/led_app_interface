# config settings for queue entries
QUEUE_ANIM = 'anim'
QUEUE_ANIM_NAME_VAL = 1
QUEU_ANIM_ID_VAL = 2

QUEUE_AREA = 'area'
QUEUE_AREA_ID = 1

QUEUE_TICKS = 'ticks'
QUEUE_TICKS_VAL = 1

QUEUE_COLOR = 'color'
QUEUE_COLOR_TYPE = 1
QUEUE_COLOR_ARG1 = 2
QUEUE_COLOR_ARG2 = 3

QUEUE_MOVE = 'movement'
QUEUE_MOVE_TYPE = 1
QUEUE_MOVE_FADE_TYPE = 2
QUEUE_MOVE_DIR = 3
QUEUE_MOVE_ARG1 = 4

# config settings for areas
AREA_ENTRY = 'area'
AREA_NAME = 1
AREA_ID = 2

AREA_BLOCK = 'block'
AREA_START_VAL = 1
AREA_END_VAL = 2

AREA_COLOR = 'color'
AREA_COLOR_VAL = 1

# config settings for events
EVENT_ENTRY = 'event'

EVENT_CONF = 'conf'
EVENT_TYPE = 1
EVENT_ARG1 = 2
EVENT_ARG2 = 3
EVENT_ARG3 = 4


def split(config):
    result = []
    split_config = config.split(';')

    for param in split_config:
        split_param = param.split(':')
        result.append(split_param)

    return result


def create_param(key, values):
    result = key + ':'

    for index, v in enumerate(values):
        result += v

        if index != len(values) - 1:
            result += ':'

    return result


def create_config(params):
    result = ''

    for index, p in enumerate(params):
        result += p

        if index != len(params) - 1:
            result += ';'

    return result


def get_param(config, key):
    split_config = config.split(';')

    for param in split_config:
        split_param = param.split(':')

        if split_param[0] == key:
            return split_param

    return []


def get_param_idx(config, key, index):
    param = get_param(config, key)

    if len(param) == 0:
        return None
    else:
        return param[index]


def edit_param(config, key, index, new_value):
    result = ''
    split_config = config.split(';')

    for c_index, param in enumerate(split_config):
        split_params = param.split(':')

        if split_params[0] == key:
            split_params[index] = new_value

        for p_index, value in enumerate(split_params):
            result += value

            if p_index < len(split_params) - 1:
                result += ':'

        if c_index < len(split_config) - 1:
            result += ';'

    return result
