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
        self.color = color

    def set_bounds(self, block_start, block_end):
        self.values.clear()
        self.values = [self.color] * (block_end - block_start)


class Gradient(ColorAnimation):
    def __init__(self, color1, color2):
        super().__init__()

        self.color1 = color1
        self.color2 = color2

    def set_bounds(self, block_start, block_end):
        self.values.clear()

        for i in range(0, block_end - block_start):
            self.values.append(color_tools.mix_colors(self.color1,
                                                      self.color2,
                                                      i / (block_end - block_start - 1)))
