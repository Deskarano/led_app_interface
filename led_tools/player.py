import time
import datetime
import queue

from collections import defaultdict
from threading import Thread, Condition

from led_tools.animation import animation, colors, movements
from led_tools.animation.control import triggers, repeats

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

        self.triggers = {}
        self.repeats = {}

        self.paused_renders = {}

        self.enabled = False
        self.lock = Condition()
        self.tick = 0

    @staticmethod
    def _parse_movement(config):
        move_type = config_utils.get_param_idx(config,
                                               config_utils.QUEUE_MOVE,
                                               config_utils.QUEUE_MOVE_TYPE)

        move_fade_type = config_utils.get_param_idx(config,
                                                    config_utils.QUEUE_MOVE,
                                                    config_utils.QUEUE_MOVE_FADE_TYPE)

        move_dir = config_utils.get_param_idx(config,
                                              config_utils.QUEUE_MOVE,
                                              config_utils.QUEUE_MOVE_DIR)

        if move_type == 'fade':
            return movements.Fade(move_fade_type, move_dir)

        elif move_type == 'move':
            move_length = config_utils.get_param_idx(config,
                                                     config_utils.QUEUE_MOVE,
                                                     config_utils.QUEUE_MOVE_ARG1)

            # TODO: implement acceleration here once done
            return movements.Move(int(move_length), move_fade_type, move_dir, '')

        elif move_type == 'flicker':
            # TODO
            return None
        else:
            return None

    @staticmethod
    def _parse_color(config):
        color_type = config_utils.get_param_idx(config,
                                                config_utils.QUEUE_COLOR,
                                                config_utils.QUEUE_COLOR_TYPE)

        if color_type == 'solid':
            color_solid = config_utils.get_param_idx(config,
                                                     config_utils.QUEUE_COLOR,
                                                     config_utils.QUEUE_COLOR_ARG1)

            if color_solid == 'random':
                return colors.Solid(color_tools.random_color(0xFF, 0xFF, 0xFF))
            else:
                return colors.Solid(int(color_solid, 16))

        elif color_type == 'gradient':
            color_gradient1 = config_utils.get_param_idx(config,
                                                         config_utils.QUEUE_COLOR,
                                                         config_utils.QUEUE_COLOR_ARG1)

            color_gradient2 = config_utils.get_param_idx(config,
                                                         config_utils.QUEUE_COLOR,
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
        anim_id = config_utils.get_param_idx(config,
                                             config_utils.QUEUE_ANIM,
                                             config_utils.QUEU_ANIM_ID_VAL)

        area_id = config_utils.get_param_idx(config,
                                             config_utils.QUEUE_AREA,
                                             config_utils.QUEUE_AREA_ID)

        area_config = file_utils.get_file_config(file_utils.AREA_PATH, area_id)

        anim_block_start = config_utils.get_param_idx(area_config,
                                                      config_utils.AREA_BLOCK,
                                                      config_utils.AREA_START_VAL)

        anim_block_end = config_utils.get_param_idx(area_config,
                                                    config_utils.AREA_BLOCK,
                                                    config_utils.AREA_END_VAL)

        anim_ticks = config_utils.get_param_idx(config,
                                                config_utils.QUEUE_TICKS,
                                                config_utils.QUEUE_TICKS_VAL)

        return animation.Animation(anim_id, int(anim_block_start), int(anim_block_end), int(anim_ticks))

    @staticmethod
    def _parse_triggers(config):
        trigger_configs = config_utils.split(config)
        trigger_results = []

        for t in trigger_configs:
            if t[0] == 'default':
                trigger_results.append(triggers.DefaultTrigger())

            elif t[0] == 'time':
                trigger_time = datetime.time(hour=int(t[1]), minute=int(t[2]), second=int(t[3]))
                trigger_date = datetime.datetime.today()

                trigger_datetime = datetime.datetime.combine(trigger_date, trigger_time)

                if trigger_datetime.timestamp() < time.time():
                    print('already past time, forwarding to tomorrow')
                    trigger_delta = datetime.timedelta(days=1)
                    trigger_datetime = trigger_datetime + trigger_delta

                trigger_results.append(triggers.TimeTrigger(trigger_datetime.timestamp()))

            elif t[0] == 'delay':
                trigger_results.append(triggers.DelayTrigger(float(t[1])))

        if len(trigger_results) == 0:
            return None
        elif len(trigger_results) == 1:
            return trigger_results[0]
        else:
            return triggers.ChainTrigger(trigger_results)

    @staticmethod
    def _parse_repeats(config):
        repeat_configs = config_utils.split(config)
        repeat_results = []

        for r in repeat_configs:
            if r[0] == 'count':
                repeat_results.append(repeats.CountRepeat(int(r[1])))

            elif r[0] == 'time':
                repeat_time = datetime.time(hour=int(r[1]), minute=int(r[2]), second=int(r[3]))
                repeat_results.append(repeats.TimeRepeat(repeat_time))

            elif r[0] == 'delay':
                repeat_results.append(repeats.DelayRepeat(float(r[1])))

        if len(repeat_results) == 0:
            return None
        elif len(repeat_results) == 1:
            return repeat_results[0]
        else:
            return repeats.ChainRepeat(repeat_results)

    def add(self, animation_config, trigger_config, repeat_config):
        mov = self._parse_movement(animation_config)
        col = self._parse_color(animation_config)
        anim = self._parse_animation(animation_config)

        anim.set_movement(mov)
        anim.set_color(col)

        trigger = self._parse_triggers(trigger_config)
        repeat = self._parse_repeats(repeat_config)

        with self.lock:
            self.configs[anim.anim_id] = animation_config
            self.animations[anim.anim_id] = AnimationThread(anim)
            self.animations[anim.anim_id].start()

            self.run_states[anim.anim_id] = self.STATE_WAITING
            self.vis_states[anim.anim_id] = self.STATE_VISIBLE

            # todo
            self.triggers[anim.anim_id] = trigger
            self.repeats[anim.anim_id] = repeat

    def play(self, anim_id):
        with self.lock:
            self.run_states[anim_id] = self.STATE_PLAYING

            if anim_id in self.paused_renders:
                del self.paused_renders[anim_id]

    def pause(self, anim_id):
        with self.lock:
            self.run_states[anim_id] = self.STATE_PAUSED
            self.paused_renders[anim_id] = self.animations[anim_id].get_next_tick()

    def stop(self, anim_id):
        with self.lock:
            self.animations[anim_id].signal_done()

            del self.configs[anim_id]
            del self.animations[anim_id]

            del self.run_states[anim_id]
            del self.vis_states[anim_id]

            del self.triggers[anim_id]
            del self.repeats[anim_id]

            if anim_id in self.paused_renders:
                del self.paused_renders[anim_id]

    def set_visible(self, anim_id, visible):
        with self.lock:
            if visible:
                self.vis_states[anim_id] = self.STATE_VISIBLE
            else:
                self.vis_states[anim_id] = self.STATE_INVISIBLE

    def run(self):
        while True:
            if self.enabled:
                with self.lock:
                    start = time.time()

                    num_ready = 0

                    # first update states
                    for key in list(self.animations):
                        # count playing or invisible animations
                        if self.run_states[key] == self.STATE_PLAYING:
                            num_ready += 1

                        # wake up any waiting animations
                        if self.run_states[key] == self.STATE_WAITING:
                            if self.triggers[key] is not None and self.triggers[key].is_met():
                                self.run_states[key] = self.STATE_PLAYING
                                num_ready += 1

                        # if animation is done, evaluate the repeat
                        if self.animations[key].get_state() == AnimationThread.STATE_DONE:
                            if (self.repeats[key] is not None) and (not self.repeats[key].is_done()):
                                self.triggers[key] = self.repeats[key].cycle()

                                new_mov = self._parse_movement(self.configs[key])
                                new_col = self._parse_color(self.configs[key])
                                new_anim = self._parse_animation(self.configs[key])

                                new_anim.set_movement(new_mov)
                                new_anim.set_color(new_col)

                                with self.lock:
                                    self.animations[new_anim.anim_id] = AnimationThread(new_anim)
                                    self.animations[new_anim.anim_id].start()

                                    self.run_states[new_anim.anim_id] = self.STATE_WAITING
                            else:
                                del self.configs[key]
                                del self.animations[key]

                                del self.run_states[key]
                                del self.vis_states[key]

                                del self.triggers[key]
                                del self.repeats[key]

                    # after states are updated, render all necessary animations
                    if num_ready > 0:
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

                        # and merge the result
                        for index, values in enumerate(result_unmerged):
                            if len(values) == 0:
                                res = 0
                            elif len(values) == 1:
                                res = values[0]
                            else:
                                res = color_tools.merge_colors(values)

                            self.strip.setPixelColor(index, res)
                        self.strip.show()

                end = time.time()

                if (1 / self.render_rate) > (end - start):
                    print('sleeping for', ((1 / self.render_rate) - (end - start)) / (1 / self.render_rate) * 100, '% of frame')
                    time.sleep((1 / self.render_rate) - (end - start))


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
                print('creating state for', area_id)
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
            if self.enabled:
                with self.lock:
                    start = time.time()

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
                else:
                    print('went over time!!!')


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

    def add_anim(self, animation_config, trigger_config, repeat_config):
        self.animation_thread.add(animation_config, trigger_config, repeat_config)

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
