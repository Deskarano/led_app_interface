from abc import ABC, abstractmethod
from led_tools import color_tools


class ColorAnimation(ABC):
    def __init__(self):
        self.values = []

    @abstractmethod
    def set_bounds(self, block_start, block_end):
        pass

    def get(self):
        return self.values


class Solid(ColorAnimation):
    def __init__(self, color):
        super().__init__()
        print('[COLOR -', id(self), ']: instantiating solid color', color)

        self.color = color

    def set_bounds(self, block_start, block_end):
        self.values.clear()
        print('[COLOR -', id(self), ']: setting bounds', block_start, block_end)

        self.values = [self.color] * (block_end - block_start)
        print('[COLOR -', id(self), ']: calculated values', self.values)


class Gradient(ColorAnimation):
    def __init__(self, color1, color2):
        super().__init__()

        print('[COLOR -', id(self), ']: instantiating gradient color from', color1, 'to', color2)

        self.color1 = color1
        self.color2 = color2

    def set_bounds(self, block_start, block_end):
        self.values.clear()
        print('[COLOR -', id(self), ']: setting bounds', block_start, block_end)

        for i in range(0, block_end - block_start):
            self.values.append(color_tools.mix_colors(self.color1,
                                                      self.color2,
                                                      i / (block_end - block_start - 1)))

        print('[COLOR -', id(self), ']: calculated values', self.values)