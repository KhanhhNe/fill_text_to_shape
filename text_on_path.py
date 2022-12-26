import cmath
import math
import os
from functools import lru_cache
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont
from svg.path import parse_path


@lru_cache(maxsize=100)
def letter_size(letter: str, font: ImageFont.ImageFont):
    return font.getsize(letter)


def get_total_width(text: str, font: ImageFont.ImageFont,
                    letter_spacing: 1, word_spacing: 5):
    width = 0
    for ind, letter in enumerate(text):
        if letter == ' ':
            width += word_spacing
        else:
            width += letter_size(letter, font)[0]
            try:
                if text[ind + 1] != ' ':
                    width += letter_spacing
            except IndexError:
                pass
    return width


def find_center(a: complex, b: complex, c: complex):
    mid = (a + c) / 2
    return mid


def complex_to_tuple(p: complex, to_int=False):
    if to_int:
        return int(p.real), int(p.imag)
    else:
        return p.real, p.imag


def write_text_on_path(path_str: str, text: str, font: ImageFont.ImageFont,
                       color: Tuple[int, int, int, int],
                       view_box: Tuple[int, int, int, int],
                       letter_spacing: 1, word_spacing: 5):
    image = Image.new('RGBA', view_box[2:])
    draw = ImageDraw.Draw(image)
    path = parse_path(path_str)
    path_length = path.length(error=0.5)
    current_pos = 0

    for ind, letter in enumerate(text):
        if letter == ' ':
            current_pos += word_spacing

        letter_width = letter_size(letter, font)[0]
        relative_pos = (current_pos + letter_width / 2 - 1e-1,
                        current_pos + letter_width / 2,
                        current_pos + letter_width / 2 + 1e-1)
        actual_pos = tuple(p / path_length for p in relative_pos)
        if actual_pos[-1] > 1:
            break

        points = tuple(path.point(p, error=0.1) for p in actual_pos)
        circle_center = find_center(*points)
        angle = math.degrees(cmath.phase(points[1] - circle_center))
        angle = math.degrees(cmath.phase(points[0] - points[2]) + 45)
        letter_img = Image.new('RGBA', letter_size(letter, font))
        letter_draw = ImageDraw.Draw(letter_img)
        letter_draw.text((0, 0), letter, fill=color, font=font)
        rotated = letter_img.rotate(angle, expand=True)
        image.alpha_composite(rotated, complex_to_tuple(points[1], to_int=True))

        if os.environ.get('DEBUG'):
            draw.ellipse([complex_to_tuple(points[1] - (5 + 5j)),
                          complex_to_tuple(points[1] + (5 + 5j))],
                         fill=(0, 255, 0, 255))
            end = cmath.rect(10, cmath.phase(points[2] - points[0]))
            draw.line((complex_to_tuple(points[0]),
                       complex_to_tuple(points[2])),
                      fill=(255, 0, 255, 255), width=60)

        current_pos += letter_width
        try:
            if text[ind + 1] != ' ':
                current_pos += letter_spacing
        except IndexError:
            pass

        if ind == 3:
            break

    image.show()


write_text_on_path("M381.83,842.42c0-245.25,198.83-444.06,444.1-444.06,"
                   "250.27,0,453.16,202.87,453.16,453.13,0,255.35-207,"
                   "462.37-462.41,462.37-260.6,0-471.85-211.24-471.85-471.81,"
                   "0-265.89,215.56-481.44,481.48-481.44,271.34,0,491.3,"
                   "219.95,491.3,491.26,0,276.86-224.45,501.29-501.33,"
                   "501.29-282.53,0-511.56-229-511.56-511.52,0-288.26,"
                   "233.71-521.95,522-521.95,294.18,0,532.66,238.45,532.66,"
                   "532.61,0,300.15-243.35,543.47-543.53,543.47-306.31,"
                   "0-554.62-248.29-554.62-554.57,0-312.53,253.38-565.88,"
                   "565.94-565.88,318.94,0,577.49,258.52,577.49,577.43,0,"
                   "325.42-263.83,589.22-589.28,589.22-332.08,"
                   "0-601.3-269.18-601.3-601.24,0-338.84,274.71-613.52,"
                   "613.58-613.52,345.78,0,626.09,280.29,626.09,626,0,"
                   "352.8-286,638.81-638.87,638.81-360,"
                   "0-651.91-291.84-651.91-651.85,0-367.35,297.83-665.15,"
                   "665.21-665.15,374.89,0,678.79,303.88,678.79,678.73",

                   "Heart beats fast Colors and promises I have loved you for "
                   "a thousand years I'll love you for a thousand more And "
                   "all along I believed, I would find you Time has brought "
                   "your heart to me, I have loved you for a thousand years "
                   "I'll love you for a thousand more One step closer One "
                   "step closer I have died everyday, waiting for you "
                   "Darling, don't be afraid, I have loved you for a thousand "
                   "years I'll love you for a thousand more And all along I "
                   "believed, I would find you Time has brought your heart to "
                   "me, I have loved you for a thousand years I'll love you "
                   "for a thousand more. 123",
                   font=ImageFont.truetype('times', size=60),
                   color=(255, 0, 0, 255),
                   view_box=(0, 0, 1650, 2100),
                   letter_spacing=1,
                   word_spacing=5)
