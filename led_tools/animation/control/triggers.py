from abc import ABC, abstractmethod
import time


class Trigger(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def is_met(self):
        pass


class DefaultTrigger(Trigger):
    def __init__(self):
        super().__init__()

    def is_met(self):
        return True


class TimeTrigger(Trigger):
    def __init__(self, target_time):
        super().__init__()
        self.target_time = target_time

    def is_met(self):
        if time.time() > self.target_time:
            return True
        else:
            return False


class DelayTrigger(TimeTrigger):
    def __init__(self, delay):
        super().__init__(time.time() + delay)

        self.delay = delay


class ChainTrigger(Trigger):
    def __init__(self, trigger_list):
        super().__init__()

        self.children = []
        self.index = 0

        for t in trigger_list:
            self.children.append(t)

    def is_met(self):
        for i in range(self.index, len(self.children)):
            if self.children[i].is_met():
                self.index += 1
            else:
                return False

        return True
