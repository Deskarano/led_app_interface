from abc import ABC, abstractmethod
import datetime
import time

from led_tools.animation.control import triggers


class Repeat(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def is_done(self):
        pass

    @abstractmethod
    def cycle(self):
        pass


class CountRepeat(Repeat):
    def __init__(self, count):
        super().__init__()

        self.count = count

    def is_done(self):
        return self.count == 0

    def cycle(self):
        if self.count != 0:
            self.count -= 1
            return triggers.DefaultTrigger()
        else:
            return triggers.NoneTrigger()


class TimeRepeat(Repeat):
    def __init__(self, target_time):
        super().__init__()

        self.repeat_time = target_time

    def is_done(self):
        return False

    def cycle(self):
        result = datetime.datetime.combine(datetime.datetime.today(), self.repeat_time)

        if result.timestamp() < time.time():
            result = result + datetime.timedelta(days=1)

        return triggers.TimeTrigger(result.timestamp())


class DelayRepeat(Repeat):
    def __init__(self, target_delay):
        super().__init__()

        self.delay_time = target_delay

    def is_done(self):
        return False

    def cycle(self):
        return triggers.DelayTrigger(self.delay_time)


class ChainRepeat(Repeat):
    def __init__(self, repeat_list):
        super().__init__()

        self.children = []
        for r in repeat_list:
            self.children.append(r)

    def is_done(self):
        for r in self.children:
            if r.is_done():
                return True

    def cycle(self):
        t = []

        for r in self.children:
            t.append(r.cycle())

        return triggers.ChainTrigger(t)