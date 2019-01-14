from led_tools import color_tools


class Animation():
    movement = None
    color = None

    def __init__(self, anim_id,
                 block_start, block_stop, total_ticks,
                 movement=None, color=None):

        super().__init__()

        self.anim_id = anim_id
        self.block = range(block_start, block_stop)
        self.total_ticks = total_ticks

        if movement is not None:
            self.set_movement(movement)

        if color is not None:
            self.set_color(color)

    def set_movement(self, movement):
        movement.set_bounds(self.block.start, self.block.stop, self.total_ticks)
        self.movement = movement

    def set_color(self, color):
        color.set_bounds(self.block.start, self.block.stop)
        self.color = color

    def render(self, tick):
        values = self.color.get()
        weights = self.movement.get(tick)

        result = []
        for i, color in enumerate(values):
            if weights[i] == 0:
                result.append(0)
            else:
                result.append(color_tools.adj_color_brightness(color, weights[i]))

        return result


class AnimationGroup:
    def __init__(self):
        self.children = {}
        self.triggers = {}

        self.block_start = None
        self.block_stop = None

    def add_animation(self, animation, trigger=None):
        if self.block_start is None or animation.block.start < self.block_start:
            self.block_start = animation.block.start

        if self.block_stop is None or animation.block.stop > self.block_stop :
            self.block_stop = animation.block.stop

        self.children[animation.anim_id] = animation
        if trigger is not None:
            self.triggers[animation.anim_id] = trigger

    def render(self, tick):
        result_unmerged = [[]] * (self.block_stop - self.block_start)

        for anim in self.children:
            anim_render = anim.render(tick)

            for index, val in enumerate(anim_render):
                result_unmerged[anim.block.start - self.block_start + index].append(val)

        result = [] * (self.block_stop - self.block_start)

        for index, values in enumerate(result_unmerged):
            if len(values) == 0:
                result[index] = 0

            elif len(values) == 1:
                result[index] = result_unmerged[index][0]

            else:
                result[index] = color_tools.merge_colors(result_unmerged[index])

        return result
