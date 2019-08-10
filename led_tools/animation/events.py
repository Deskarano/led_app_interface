from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import time


class Event(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def is_met(self):
        pass


class CombinedEvent(Event):
    def __init__(self, count):
        super().__init__()
        self.count = count
        self.children = []

    def add_child(self, ev):
        self.children.append(ev)

    @abstractmethod
    def is_met(self):
        pass


class NowEvent(Event):
    def __init__(self):
        super().__init__()

    def is_met(self):
        return True


class NeverEvent(Event):
    def __init__(self):
        super().__init__()

    def is_met(self):
        return False


class TimeEvent(Event):
    def __init__(self, target_time):
        super().__init__()
        self.target_time = target_time

    def is_met(self):
        # pulse once
        if time.time() > self.target_time.timestamp():
            self.target_time += timedelta(days=1)
            return True
        else:
            return False


class DateEvent(Event):
    def __init__(self, target_datetime):
        super().__init__()
        self.target_datetime = target_datetime

    def is_met(self):
        if datetime.today().month == self.target_datetime.month and datetime.today().day == self.target_datetime.day:
            # return true that whole day
            return True
        else:
            return False


class DelayEvent(Event):
    def __init__(self, delay_hours, delay_minutes, delay_seconds):
        super().__init__()

        self.delay_hours = delay_hours
        self.delay_minutes = delay_minutes
        self.delay_seconds = delay_seconds

        self.target_time = None

    def is_met(self):
        if self.target_time is None:
            self.target_time = datetime.now() + timedelta(hours=self.delay_hours, minutes=self.delay_minutes,
                                                          seconds=self.delay_seconds)

            return False

        elif time.time() > self.target_time.timestamp():
            self.target_time = None
            return True

        else:
            return False


class AnimationEvent(Event):
    ON_START = 1
    ON_END = 1

    def __init__(self, anim, anim_type):
        super().__init__()
        self.anim = anim
        self.anim_type = anim_type

    def is_met(self):
        pass


class BooleanEvent(CombinedEvent):
    AND = 0
    OR = 1

    def __init__(self, count, bool_type):
        super().__init__(count)
        self.bool_type = bool_type

    def is_met(self):
        if self.bool_type == BooleanEvent.AND:
            result = True

            for c in self.children:
                result = result and c.is_met()

            return result

        elif self.bool_type == BooleanEvent.OR:
            result = False

            for c in self.children:
                result = result or c.is_met()

            return result


class ChainEvent(CombinedEvent):
    def __init__(self, count):
        super().__init__(count)
        self.index = 0

    def is_met(self):
        for i in range(self.index, len(self.children)):
            if self.children[i].is_met():
                self.index += 1
            else:
                return False

        return True
