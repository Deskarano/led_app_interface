from abc import ABC, abstractmethod
import math
import time


class MovementAnimation(ABC):
    def __init__(self):
        self.len = 0
        self.weights = []

    @abstractmethod
    def set_bounds(self, block_start, block_stop, total_ticks):
        pass

    @abstractmethod
    def get(self, tick):
        pass


class Fade(MovementAnimation):
    def __init__(self, fade_type, fade_direction):
        super().__init__()

        self.fade_type = fade_type
        self.fade_direction = fade_direction

    def set_bounds(self, block_start, block_stop, total_ticks):
        self.len = block_stop - block_start
        self.weights.clear()

        for tick in range(0, total_ticks + 1):
            # first generate the weight
            weight = 0
            if self.fade_type == 'linear':
                weight = tick / total_ticks

            elif self.fade_type == 'exponential':
                weight = math.exp(7 * (tick / total_ticks) - 7)

            elif self.fade_type == 'logarithmic':
                weight = math.log((math.e - 1) * (tick / total_ticks) + 1)

            elif self.fade_type == 'logistic':
                weight = 1 / (1 + math.exp((-14 / total_ticks) * (tick - (total_ticks / 2))))

            # then append it
            if self.fade_direction == '+':
                self.weights.append(weight)

            elif self.fade_direction == '-':
                self.weights.append(1 - weight)

    def get(self, tick):
        return [self.weights[tick]] * self.len


class Flicker(MovementAnimation):
    def __init__(self, max_deviation):
        super().__init__()

        self.dev = max_deviation

    def set_bounds(self, block_start, block_stop, total_ticks):
        pass

    def get(self, tick):
        pass


class Move(MovementAnimation):
    def __init__(self, length, fade_type, move_direction, acc_type):
        super().__init__()

        self.length = length
        self.fade_type = fade_type
        self.move_direction = move_direction
        self.acc_type = acc_type

        self.fade_ticks = 0
        self.velocity = 0

    def set_bounds(self, block_start, block_stop, total_ticks):
        self.len = block_stop - block_start
        self.weights.clear()

        self.fade_ticks = round((total_ticks * self.length) / (2 * (block_stop - block_start + self.length)))
        self.velocity = (total_ticks - 2 * self.fade_ticks) / (block_stop - block_start)

        for tick in range(0, self.fade_ticks):
            weight = 0

            if self.fade_type == 'linear':
                weight = tick / self.fade_ticks

            elif self.fade_type == 'exponential':
                weight = math.exp(7 * (tick / self.fade_ticks) - 7)

            elif self.fade_type == 'logarithmic':
                weight = math.log((math.e - 1) * (tick / self.fade_ticks) + 1)

            elif self.fade_type == 'logistic':
                weight = 1 / (1 + math.exp((-14 / self.fade_ticks) * (tick - (self.fade_ticks / 2))))

            self.weights.append(weight)

    def get(self, tick):
        tick_weights = []

        for x in range(0, self.len):
            tick_offset = 0

            if self.move_direction == '+':
                tick_offset = tick - round(x * self.velocity)
            elif self.move_direction == '-':
                tick_offset = tick - round((self.len - x - 1) * self.velocity)

            if 0 <= tick_offset < self.fade_ticks:
                tick_weights.append(self.weights[tick_offset])
            elif tick_offset == self.fade_ticks:
                tick_weights.append(1)
            elif self.fade_ticks < tick_offset <= 2 * self.fade_ticks:
                tick_weights.append(self.weights[self.fade_ticks - tick_offset])
            else:
                tick_weights.append(0)

        return tick_weights
