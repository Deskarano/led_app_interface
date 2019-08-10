import time
import queue

from collections import defaultdict
from threading import Thread, Condition
from datetime import date as dt_date, time as dt_time, datetime, timedelta

from led_tools.animation import animation, colors, movements, events
from file import config_utils, file_utils

from . import color_tools


class AnimationThread(Thread):
    STATE_READY = 'ready'
    STATE_DONE = 'done'

    def __init__(self, anim):
        super().__init__()

        self.animation = anim
        self.tick = 0

        self.rendered_queue = queue.Queue(maxsize=5)
        self.cont = True

    def signal_done(self):
        self.cont = False

    def get_state(self):
        if not self.is_alive() and self.rendered_queue.qsize() == 0:
            return self.STATE_DONE
        else:
            return self.STATE_READY

    def get_next_tick(self):
        return self.rendered_queue.get()

    def run(self):
        while self.cont and (self.tick <= self.animation.total_ticks):
            next_tick = self.animation.render(self.tick)
            self.rendered_queue.put(next_tick)

            self.tick += 1


class AnimationManager(Thread):
    STATE_WAITING = 'waiting'
    STATE_PLAYING = 'playing'
    STATE_PAUSED = 'paused'

    STATE_VISIBLE = 'visible'
    STATE_INVISIBLE = 'invisible'

    def __init__(self, strip, render_rate):
        super().__init__()

        self.strip = strip
        self.render_rate = render_rate

        self.configs = {}
        self.animations = {}

        self.run_states = {}
        self.vis_states = {}

        self.play_events = {}
        self.pause_events = {}
        self.end_events = {}

        self.paused_renders = {}

        self.enabled = False
        self.lock = Condition()
        self.tick = 0

    @staticmethod
    def _parse_movement(config):
        move_type = config_utils.get_param_idx(config, config_utils.QUEUE_MOVE, config_utils.QUEUE_MOVE_TYPE)
        move_fade_type = config_utils.get_param_idx(config, config_utils.QUEUE_MOVE, config_utils.QUEUE_MOVE_FADE_TYPE)
        move_dir = config_utils.get_param_idx(config, config_utils.QUEUE_MOVE, config_utils.QUEUE_MOVE_DIR)

        print('[ANIM_ADD]: parsed movement and extracted type', move_type)

        if move_type == 'fade':
            return movements.Fade(move_fade_type, move_dir)

        elif move_type == 'move':
            move_length = config_utils.get_param_idx(config, config_utils.QUEUE_MOVE, config_utils.QUEUE_MOVE_ARG1)

            return movements.Move(int(move_length), move_fade_type, move_dir, '')

        elif move_type == 'flicker':
            # TODO
            return None
        else:
            return None

    @staticmethod
    def _parse_color(config):
        color_type = config_utils.get_param_idx(config, config_utils.QUEUE_COLOR, config_utils.QUEUE_COLOR_TYPE)

        print('[ANIM_ADD]: parsed color and extracted type', color_type)

        if color_type == 'solid':
            color_solid = config_utils.get_param_idx(config, config_utils.QUEUE_COLOR, config_utils.QUEUE_COLOR_ARG1)

            if color_solid == 'random':
                return colors.Solid(color_tools.random_color(0xFF, 0xFF, 0xFF))
            else:
                return colors.Solid(int(color_solid, 16))

        elif color_type == 'gradient':
            color_gradient1 = config_utils.get_param_idx(config, config_utils.QUEUE_COLOR,
                                                         config_utils.QUEUE_COLOR_ARG1)
            color_gradient2 = config_utils.get_param_idx(config, config_utils.QUEUE_COLOR,
                                                         config_utils.QUEUE_COLOR_ARG2)

            if color_gradient1 == 'random':
                color1 = color_tools.random_color(0xFF, 0xFF, 0xFF)
            else:
                color1 = int(color_gradient1, 16)

            if color_gradient2 == 'random':
                color2 = color_tools.random_color(0xFF, 0xFF, 0xFF)
            else:
                color2 = int(color_gradient2, 16)

            return colors.Gradient(color1, color2)
        elif color_type == 'rainbow':
            # todo
            return None

        else:
            return None

    @staticmethod
    def _parse_animation(config):
        anim_id = config_utils.get_param_idx(config, config_utils.QUEUE_ANIM, config_utils.QUEU_ANIM_ID_VAL)

        area_id = config_utils.get_param_idx(config, config_utils.QUEUE_AREA, config_utils.QUEUE_AREA_ID)
        area_config = file_utils.get_file_config(file_utils.AREA_PATH, area_id)

        anim_block_start = config_utils.get_param_idx(area_config, config_utils.AREA_BLOCK, config_utils.AREA_START_VAL)
        anim_block_end = config_utils.get_param_idx(area_config, config_utils.AREA_BLOCK, config_utils.AREA_END_VAL)
        anim_ticks = config_utils.get_param_idx(config, config_utils.QUEUE_TICKS, config_utils.QUEUE_TICKS_VAL)

        print('[ANIM_ADD]: finished parsing animation', anim_id, 'and creating object')
        return animation.Animation(anim_id, int(anim_block_start), int(anim_block_end), int(anim_ticks))

    @staticmethod
    def _parse_event(config):
        event_configs = config_utils.split(config)
        event_results = []

        print('[ANIM_ADD]: parsing event config', config)

        for e in event_configs[1:]:
            print('[ANIM_ADD]: extracting event of type', e[1])

            if e[1] == 'now':
                event_results.append(events.NowEvent())

            elif e[1] == 'never':
                event_results.append(events.NeverEvent())

            elif e[1] == 'time':
                event_date = datetime.today()
                event_time = dt_time(hour=int(e[2]), minute=int(e[3]), second=int(e[4]))

                event_datetime = datetime.combine(event_date, event_time)
                if event_datetime.timestamp() < time.time():
                    event_delta = timedelta(days=1)
                    event_datetime += event_delta

                event_results.append(events.TimeEvent(event_datetime))

            elif e[1] == 'date':
                event_date = dt_date(year=datetime.today().year, month=int(e[2]), day=int(e[3]))
                event_time = dt_time(hour=0, minute=0, second=0)

                event_datetime = datetime.combine(event_date, event_time)
                if event_datetime.timestamp() < time.time():
                    event_delta = timedelta(days=365)
                    event_datetime += event_delta

                event_results.append(events.DateEvent(event_datetime))

            elif e[1] == 'delay':
                event_results.append(events.DelayEvent(int(e[2]), int(e[3]), int(e[4])))

            elif e[1] == 'boolean':
                if e[3] == 'AND':
                    event_results.append(events.BooleanEvent(int(e[2]), events.BooleanEvent.AND))

                elif e[3] == 'OR':
                    event_results.append(events.BooleanEvent(int(e[2]), events.BooleanEvent.OR))

            elif e[1] == 'chain':
                event_results.append(events.ChainEvent(int(e[2])))

        if len(event_results) == 0:
            return None

        elif len(event_results) == 1:
            return event_results[0]

        else:
            print('[ANIM_ADD]: rebuilding event hierarchy')
            result = event_results[0]
            current = result
            idx = 1

            while idx < len(event_results):
                if isinstance(event_results[idx], events.CombinedEvent):
                    last = current
                    current = event_results[idx]

                    for i in range(current.count):
                        current.add_child(event_results[idx + i])

                    idx += current.count
                    current = last
                else:
                    current.add_child(event_results[idx])
                    idx += 1

            return result

    def add(self, animation_config, play_config, pause_config, end_config):
        print('[ANIM_ADD]: adding a new animation', animation_config)
        mov = self._parse_movement(animation_config)
        col = self._parse_color(animation_config)
        anim = self._parse_animation(animation_config)

        anim.set_movement(mov)
        anim.set_color(col)

        play_event = self._parse_event(play_config)
        pause_event = self._parse_event(pause_config)
        end_event = self._parse_event(end_config)

        with self.lock:
            print('[ANIM_ADD]: holding lock, adding animation to player')

            self.configs[anim.anim_id] = animation_config
            self.animations[anim.anim_id] = AnimationThread(anim)
            self.animations[anim.anim_id].start()

            self.run_states[anim.anim_id] = self.STATE_WAITING
            self.vis_states[anim.anim_id] = self.STATE_VISIBLE

            self.play_events[anim.anim_id] = play_event
            self.pause_events[anim.anim_id] = pause_event
            self.end_events[anim.anim_id] = end_event

    def play(self, anim_id):
        with self.lock:
            print('[ANIM_PLAY]: holding lock, playing animation', anim_id)
            self.run_states[anim_id] = self.STATE_PLAYING

            if anim_id in self.paused_renders:
                del self.paused_renders[anim_id]

    def pause(self, anim_id):
        with self.lock:
            print('[ANIM_PLAY]: holding lock, pausing animation', anim_id)

            self.run_states[anim_id] = self.STATE_PAUSED
            self.paused_renders[anim_id] = self.animations[anim_id].get_next_tick()

    def stop(self, anim_id):
        with self.lock:
            print('[ANIM_PLAY]: holding lock, stopping animation', anim_id)
            self.animations[anim_id].signal_done()

            del self.configs[anim_id]
            del self.animations[anim_id]

            del self.run_states[anim_id]
            del self.vis_states[anim_id]

            del self.play_events[anim_id]
            del self.pause_events[anim_id]
            del self.end_events[anim_id]

            if anim_id in self.paused_renders:
                del self.paused_renders[anim_id]

    def set_visible(self, anim_id, visible):
        with self.lock:
            if visible:
                print('[ANIM_PLAY]: holding lock, making animation', anim_id, 'visible')
                self.vis_states[anim_id] = self.STATE_VISIBLE
            else:
                print('[ANIM_PLAY]: holding lock, making animation', anim_id, 'invisible')
                self.vis_states[anim_id] = self.STATE_INVISIBLE

    def check_events(self):
        for key in list(self.animations):
            # animations that are waiting but need to be played
            if self.run_states[key] == self.STATE_WAITING and self.play_events[key].is_met():
                print('[ANIM_CHECK_EVENTS]: play event for animation', key, 'is met, (re)starting animation')

                if self.animations[key].get_state() == AnimationThread.STATE_DONE:
                    del self.animations[key]

                    new_mov = self._parse_movement(self.configs[key])
                    new_col = self._parse_color(self.configs[key])
                    new_anim = self._parse_animation(self.configs[key])

                    new_anim.set_movement(new_mov)
                    new_anim.set_color(new_col)

                    with self.lock:
                        self.animations[new_anim.anim_id] = AnimationThread(new_anim)
                        self.animations[new_anim.anim_id].start()

                self.play(key)

            # animations that are playing but need to be paused
            elif self.run_states[key] == self.STATE_PLAYING and self.pause_events[key].is_met():
                print('[ANIM_CHECK_EVENTS]: pause event for animation', key, 'is met, pausing animation')
                self.pause(key)

            # animations that need to be ended and removed
            elif self.run_states[key] == self.STATE_WAITING and self.end_events[key].is_met():
                print('[ANIM_CHECK_EVENTS]: stop event for animation', key, 'is met, stopping animation')
                self.stop(key)

    def run(self):
        while True:
            start = time.time()

            if self.enabled:
                event_start_time = time.time()
                self.check_events()
                event_end_time = time.time()

                with self.lock:
                    num_ready = 0

                    for key in list(self.animations):
                        # count playing or invisible animations
                        if self.run_states[key] == self.STATE_PLAYING:
                            num_ready += 1

                        if self.animations[key].get_state() == AnimationThread.STATE_DONE:
                            self.run_states[key] = self.STATE_WAITING
                            num_ready -= 1

                    # after states are updated, render all necessary animations
                    if num_ready > 0:
                        pull_start_time = time.time()
                        result_unmerged = [[] for _ in range(self.strip.numPixels())]

                        for key in list(self.animations):
                            # render any playing animations
                            if self.run_states[key] == self.STATE_PLAYING:
                                anim_thread = self.animations[key]
                                anim_render = anim_thread.get_next_tick()

                                if self.vis_states[key] == self.STATE_VISIBLE:
                                    for index, val in enumerate(anim_render):
                                        if val != 0:
                                            result_unmerged[anim_thread.animation.block.start + index].append(val)

                            # include paused animations
                            if (self.run_states[key] == self.STATE_PAUSED) and (
                                    self.vis_states[key] == self.STATE_VISIBLE):
                                anim_thread = self.animations[key]

                                for index, val in enumerate(self.paused_renders[key]):
                                    if val != 0:
                                        result_unmerged[anim_thread.animation.block.start + index].append(val)

                        pull_end_time = time.time()

                        # and merge the result
                        for index, values in enumerate(result_unmerged):
                            if len(values) == 0:
                                res = 0
                            elif len(values) == 1:
                                res = values[0]
                            else:
                                res = color_tools.merge_colors(values)

                            self.strip.setPixelColor(index, res)

                        merge_end_time = time.time()
                        self.strip.show()
                        show_end_time = time.time()

            end = time.time()
            if (1 / self.render_rate) > (end - start):
                time.sleep((1 / self.render_rate) - (end - start))
            else:
                print('[ANIM_RENDER]: went over frame time, took', round(end - start, 5),
                      'allowed', round(1 / self.render_rate, 5), 'diff', round((end - start) - (1 / self.render_rate), 5))
                print('[ANIM_RENDER]: \tevent checking took', round(event_end_time - event_start_time, 5),
                      '(', round((event_end_time - event_start_time) / (end - start) * 100, 2), '% )')
                print('[ANIM_RENDER]: \tanimation pull took', round(pull_end_time - pull_start_time, 5),
                      '(', round((pull_end_time - pull_start_time) / (end - start) * 100, 2), '% )')
                print('[ANIM_RENDER]: \tanimation merge took', round(merge_end_time - pull_start_time, 5),
                      '(', round((merge_end_time - pull_end_time) / (end - start) * 100, 2), '% )')
                print('[ANIM_RENDER]: \tshowing animation took', round(show_end_time - merge_end_time, 5),
                      '(', round((show_end_time - merge_end_time) / (end - start) * 100, 2), '% )')


class AreaManager(Thread):
    def __init__(self, strip, render_rate):
        super().__init__()

        self.strip = strip
        self.render_rate = render_rate

        self.lock = Condition()
        self.enabled = False

        self.run_update = False

        self.color = {}
        self.lower = {}
        self.upper = {}

        self.last_color = {}
        self.last_lower = {}
        self.last_upper = {}

        self.visible = {}
        self.state = defaultdict(list)

    def init_areas(self):
        area_configs = file_utils.get_areas()

        for area_id, config in area_configs.items():
            color = config_utils.get_param_idx(config,
                                               config_utils.AREA_COLOR,
                                               config_utils.AREA_COLOR_VAL)

            lower = config_utils.get_param_idx(config,
                                               config_utils.AREA_BLOCK,
                                               config_utils.AREA_START_VAL)

            upper = config_utils.get_param_idx(config,
                                               config_utils.AREA_BLOCK,
                                               config_utils.AREA_END_VAL)

            self.color[area_id] = int(color, 16)
            self.lower[area_id] = int(lower)
            self.upper[area_id] = int(upper)

            self.visible[area_id] = False
            self.state[area_id] = [0 for _ in range(self.strip.numPixels())]

        self.run_update = True

    def update_area(self, area_id, lower, upper, color):
        with self.lock:
            self.color[area_id] = color
            self.lower[area_id] = lower
            self.upper[area_id] = upper

            if area_id not in self.state:
                self.visible[area_id] = True
                self.state[area_id] = [0 for _ in range(self.strip.numPixels())]

            self.run_update = True

    def set_area_visible(self, area_id, visible):
        self.visible[area_id] = bool(visible)
        self.run_update = True

    def delete_area(self, area_id):
        with self.lock:
            del self.color[area_id]
            del self.lower[area_id]
            del self.upper[area_id]

            del self.last_color[area_id]
            del self.last_lower[area_id]
            del self.last_upper[area_id]

            del self.visible[area_id]
            del self.state[area_id]

            self.run_update = True

    def run(self):
        while True:
            start = time.time()

            if self.enabled:
                with self.lock:
                    if self.run_update:
                        # update each area
                        for area_id in list(self.state):
                            if (area_id not in self.last_color) or (self.color[area_id] != self.last_color[area_id]):
                                for i in range(self.lower[area_id], self.upper[area_id]):
                                    self.state[area_id][i] = self.color[area_id]

                            else:
                                if self.last_lower[area_id] < self.lower[area_id]:
                                    for i in range(self.last_lower[area_id], self.lower[area_id]):
                                        self.state[area_id][i] = 0

                                elif self.last_lower[area_id] > self.lower[area_id]:
                                    for i in range(self.lower[area_id], self.last_lower[area_id]):
                                        self.state[area_id][i] = self.color[area_id]

                                if self.last_upper[area_id] < self.upper[area_id]:
                                    for i in range(self.last_upper[area_id], self.upper[area_id]):
                                        self.state[area_id][i] = self.color[area_id]

                                elif self.last_upper[area_id] > self.upper[area_id]:
                                    for i in range(self.upper[area_id], self.last_upper[area_id]):
                                        self.state[area_id][i] = 0

                            self.last_color[area_id] = self.color[area_id]
                            self.last_lower[area_id] = self.lower[area_id]
                            self.last_upper[area_id] = self.upper[area_id]

                        # grab from defaultdict
                        result_unmerged = [[] for _ in range(self.strip.numPixels())]
                        for area_id in list(self.state):
                            if self.visible[area_id]:
                                for index, color in enumerate(self.state[area_id]):
                                    if color != 0:
                                        result_unmerged[index].append(color)

                        # merge and throw on the strip
                        for index, values in enumerate(result_unmerged):
                            if len(values) == 0:
                                self.strip.setPixelColor(index, 0)
                            elif len(values) == 1:
                                self.strip.setPixelColor(index, values[0])
                            else:
                                self.strip.setPixelColor(index, color_tools.merge_colors(values))

                        self.strip.show()
                        self.run_update = False

            end = time.time()
            if (1 / self.render_rate) > (end - start):
                time.sleep((1 / self.render_rate) - (end - start))


class Player:
    MODE_ANIMATION = 'animation'
    MODE_AREA = 'area'
    MODE_IDLE = 'idle'

    def __init__(self, strip, render_rate):
        self.animation_thread = AnimationManager(strip, render_rate)
        self.animation_thread.start()
        self.animation_thread.enabled = True

        self.area_manager = AreaManager(strip, render_rate)
        self.area_manager.start()
        self.area_manager.enabled = False

        self.strip = strip

        for i in range(0, strip.numPixels() + 1):
            strip.setPixelColor(i, 0)
        strip.show()

    def set_mode(self, mode):
        if mode == self.MODE_ANIMATION:
            self.area_manager.enabled = False

            self.area_manager.color.clear()
            self.area_manager.lower.clear()
            self.area_manager.upper.clear()

            self.area_manager.last_color.clear()
            self.area_manager.last_lower.clear()
            self.area_manager.last_upper.clear()

            self.area_manager.state.clear()
            self.area_manager.visible.clear()

            for i in range(0, self.strip.numPixels() + 1):
                self.strip.setPixelColor(i, 0)
            self.strip.show()

            self.animation_thread.enabled = True

        elif mode == self.MODE_AREA:
            self.animation_thread.enabled = False

            self.area_manager.init_areas()
            self.area_manager.enabled = True

        elif mode == self.MODE_IDLE:
            self.animation_thread.enabled = False
            self.area_manager.enabled = False

    def add_anim(self, animation_config, play_config, pause_config, end_config):
        self.animation_thread.add(animation_config, play_config, pause_config, end_config)

    def play_anim(self, anim_id):
        self.animation_thread.play(anim_id)

    def pause_anim(self, anim_id):
        self.animation_thread.pause(anim_id)

    def stop_anim(self, anim_id):
        self.animation_thread.stop(anim_id)

    def set_anim_visible(self, anim_id, visible):
        self.animation_thread.set_visible(anim_id, visible)

    def display_area(self, area_id, lower, upper, color):
        self.area_manager.update_area(area_id, lower, upper, color)

    def delete_area(self, area_id):
        self.area_manager.delete_area(area_id)

    def set_area_visible(self, area_id, visible):
        self.area_manager.set_area_visible(area_id, visible)
