import os

QUEUE_PATH = 'test/queue/'
AREA_PATH = 'test/areas/'


def get_queue():
    files = os.listdir(QUEUE_PATH)
    result = {}

    for f in files:
        result[f] = get_file_config(QUEUE_PATH, f)

    return result


def get_areas():
    files = os.listdir(AREA_PATH)
    result = {}

    for f in files:
        result[f] = get_file_config(AREA_PATH, f)

    return result


def get_file_config(path, f_id):
    result = ''
    f_obj = open(path + f_id)

    lines = f_obj.readlines()

    for index, line in enumerate(lines):
        result += line.strip()

        if index < len(lines) - 1:
            result += ';'

    return result


def set_file_config(path, f_id, config):
    f_obj = open(path + f_id, 'w')

    split_config = config.split(';')
    for index, line in enumerate(split_config):
        f_obj.write(line)

        if index < len(split_config) - 1:
            f_obj.write('\n')

    f_obj.close()


def delete_file(path, f_id):
    if os.path.exists(path + f_id):
        os.remove(path + f_id)
        return True

    else:
        return False
