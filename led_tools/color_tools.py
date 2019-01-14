import math
import random


def extract_red(color):
    return (color >> 16) & 0b11111111


def extract_green(color):
    return (color >> 8) & 0b11111111


def extract_blue(color):
    return color & 0b11111111


def make_color(red, green, blue):
    return (red << 16) | (green << 8) | blue


def adj_color_brightness(color, factor):
    red = round(extract_red(color) * factor)
    green = round(extract_green(color) * factor)
    blue = round(extract_blue(color) * factor)

    return make_color(red, green, blue)


def merge_colors(color_list):
    red_sum = 0
    green_sum = 0
    blue_sum = 0

    for color in color_list:
        red_sum += math.pow(extract_red(color), 2)
        green_sum += math.pow(extract_green(color), 2)
        blue_sum += math.pow(extract_blue(color), 2)

    red = round(math.sqrt(red_sum / len(color_list)))
    green = round(math.sqrt(green_sum / len(color_list)))
    blue = round(math.sqrt(blue_sum / len(color_list)))

    return make_color(red, green, blue)


def mix_colors(color1, color2, percent):
    red = extract_red(color1) + percent * (extract_red(color2) - extract_red(color1))
    green = extract_green(color1) + percent * (extract_green(color2) - extract_green(color1))
    blue = extract_blue(color1) + percent * (extract_blue(color2) - extract_blue(color1))

    return make_color(round(red), round(green), round(blue))


def random_color(max_red, max_green, max_blue):
    r = random.randint(0, max_red)
    g = random.randint(0, max_green)
    b = random.randint(0, max_blue)

    return make_color(r, g, b)