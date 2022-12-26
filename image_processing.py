"""
This file defines image interpreting and processing functions.
"""

import os
from dataclasses import dataclass, field
from functools import cache
from io import BytesIO
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont


@dataclass
class TextLine:
    """
    A line of text, with modifiable words spacing, allowing for custom line
    width for provided text.
    """
    word_spacing: float
    start_point: Tuple[int, int]
    font: ImageFont
    words: List[str] = field(default_factory=lambda: [])

    @property
    def total_width(self):
        """
        Total line width.
        """
        total_width = self.words_width + self.word_spacing * len(self.words)
        return total_width

    @property
    def words_width(self):
        """
        Total width of all words.
        """
        return sum([get_word_width(w, font=self.font) for w in self.words])

    def add_word(self, word: str):
        """
        Add new word to line (stripped word).
        """
        self.words.append(word)

    def fit_length(self, length):
        """
        Fit line total width to provided length by adjusting words spacing.
        :param length: Total preferred length to fit line to.
        """
        if len(self.words) > 1:
            space_count = len(self.words) - 1
            self.word_spacing = (length - self.words_width) / space_count
        else:
            self.word_spacing = 0


@dataclass
class Boundary:
    """
    Boundary on the image, specifying an area to fit text onto.
    """
    start_point: Tuple[int, int]
    end_point: Tuple[int, int]

    @property
    def length(self):
        """
        Total boundary length.
        """
        return abs(self.start_point[0] - self.end_point[0])


def load_font(font_fp, font_size: int):
    """
    Load TrueTypeFont (ttf) with size and name

    :param font_size: Font size in int
    :param font_fp: Font name or file-like object
    """
    return ImageFont.truetype(font_fp, size=font_size)


@cache
def get_word_width(word: str, font: ImageFont):
    """
    Get word's width using provided font

    :param word: Target word
    :param font: Font to use
    :return: Maximum word's width rendered by given font
    """
    bbox = font.getbbox(word)
    return bbox[2] - bbox[0]


def find_pixel(image: Image.Image, start_x: int, start_y: int,
               step: int, find_transparent=False):
    """
    Find next target pixel with speed optimization

    :param image: Image to get pixels from
    :param start_x: x start
    :param start_y: y start
    :param step: Steps to jump if no valid pixels found
    :param find_transparent: True if target pixel need to be transparent, False
    otherwise
    :return: Next target pixel
    """

    def is_target_pixel(px: Tuple[int, int, int, int]):
        return ((find_transparent and px[3] == 0) or
                (not find_transparent and px[3] > 0))

    x = start_x
    while x < image.width:
        if is_target_pixel(image.getpixel((x, start_y))):
            for x in range(x, max(-1, x - step), -1):
                if is_target_pixel(image.getpixel((x, start_y))) is False:
                    x += 1
                    break
            break
        x += step
    if x < image.width:
        assert is_target_pixel(image.getpixel((x, start_y)))
    return min(x, image.width), start_y


def get_text_boundaries(image: Image.Image, boundaries_spacing):
    """
    Get boundaries of the image, in which boundaries will be inside area that
    has all pixels' brightness reach `white_threshold`
    @copyright Khanh Luong (khanhluong3005@gmail.com)

    :param image: Image
    :param boundaries_spacing: Spacing between boundaries vertically
    """
    boundaries = []

    for y in range(boundaries_spacing, image.height, boundaries_spacing):
        x = 0
        while True:
            x, _ = find_pixel(image, x, y,
                              boundaries_spacing,
                              find_transparent=False)
            if x == image.width:
                break
            end_x, _ = find_pixel(image, x + 1, y,
                                  boundaries_spacing,
                                  find_transparent=True)
            boundaries.append(Boundary((x, y), (end_x - 1, y)))
            x = end_x

    return boundaries


def align_text_to_boundaries(text: str, boundaries: List[Boundary],
                             font: ImageFont, min_spacing: float = 5):
    """
    Split text into lines with flexible spacing to fit provided boundaries

    :param text: Text to fit into boundaries
    :param boundaries: Boundaries to split the text into
    :param font: Font to calculate text width, height, etc.
    :param min_spacing: Minimum spacing between words in line
    """
    lines = []
    words = text.split()

    for boundary in boundaries:
        line = TextLine(min_spacing, boundary.start_point, font=font)
        while words:
            word = words.pop(0)
            additional_width = get_word_width(word, font) + min_spacing
            new_width = additional_width + line.total_width
            if (
                    new_width < boundary.length or
                    new_width - boundary.length < min_spacing * 0.25
            ):
                line.add_word(word)
            else:
                line.fit_length(boundary.length)
                lines.append(line)
                words.insert(0, word)
                break
        else:
            if line.words:
                line.fit_length(boundary.length)
                lines.append(line)

    return lines


def draw_text_lines(image: Image.Image, lines: List[TextLine],
                    font: ImageFont, color: Tuple[int, int, int, int]):
    """
    Draw lines of text to image. Lines will be rendered onto given image
    (in-place)

    :param image: Image to draw onto
    :param lines: Lines of text
    :param font: Font to render the text
    :param color: Text color
    """
    bbox = font.getbbox('A')
    line_height = bbox[1] - bbox[3]

    draw = ImageDraw.Draw(image)
    for line in lines:
        if os.environ.get('DEBUG'):
            print(line)

        point = list(line.start_point)
        point[1] += line_height * 0.8

        if len(line.words) == 1:
            length = line.total_width
            line.words = ['', line.words[0], '']
            line.fit_length(length)

        for word in line.words:
            # noinspection PyTypeChecker
            draw.text(tuple(point), word, fill=color, font=font)

            if os.environ.get('DEBUG'):
                draw.ellipse(((point[0] - 4, point[1] - 4),
                              (point[0] + 4, point[1] + 4)),
                             fill=(0, 0, 255))

            point[0] += get_word_width(word, font=font) + line.word_spacing


def fit_text_to_image(fp: Image.Image, text: str,
                      font_fp, color: Tuple[int, int, int, int]):
    """
    Render text onto a black & white image, fitting them into white areas, with
    auto-detected boundaries.

    :param fp: Image object
    :param text: Text to render
    :param font_fp: Font name (without .ttf) or file-like object
    :param color: Color of rendered text
    """
    image = fp.convert('RGBA')
    image_ratio = image.height / image.width
    scaled_width = max(2000, image.width)
    image = image.resize((scaled_width, int(scaled_width * image_ratio)))
    total_words = len(text.split())

    lower, upper = 1, scaled_width / 10
    font_size = upper
    lines, boundaries = [], []
    font = None

    while upper - lower > 0.5:
        spacings = [i * font_size for i in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]]
        if isinstance(font_fp, BytesIO):
            font_fp.seek(0)
        font = load_font(font_fp, int(font_size))

        for min_spacing in spacings:
            print(f"{font_size} - {lower} {upper}")
            boundaries = get_text_boundaries(image,
                                             boundaries_spacing=int(font_size))
            lines = align_text_to_boundaries(text, boundaries,
                                             font=font, min_spacing=min_spacing)
            if (
                    len(lines) == len(boundaries) and
                    sum([len(line.words) for line in lines]) == total_words
            ):
                break

        if len(lines) < len(boundaries):
            # Font too small
            if font_size >= upper:
                upper += (upper - lower) * 2
                font_size = upper
                continue
            else:
                lower = font_size
        elif sum([len(line.words) for line in lines]) < total_words:
            # Font too big
            upper = font_size
        else:
            break

        font_size = (upper + lower) / 2

    empty_image = Image.new('RGBA', image.size, color=(0, 0, 0, 0))
    draw_text_lines(empty_image, lines, font=font, color=color)

    if os.environ.get('DEBUG'):
        draw = ImageDraw.Draw(empty_image)
        for boundary in boundaries:
            for point in (boundary.start_point, boundary.end_point):
                draw.ellipse(((point[0] - 5, point[1] - 5),
                              (point[0] + 5, point[1] + 5)),
                             fill=(0, 255, 0))
        print(get_word_width.cache_info())

    get_word_width.cache_clear()
    return empty_image


if __name__ == '__main__':
    fname = 'shapes/shape2.jpg'
    txt = ("Đêm nay một đêm buồn. Anh muốn cảm xúc của mình không ai có "
           "thể được chạm vào nó. Nơi có ai làn xe chạy giờ thì anh đứng "
           "ở giữa mơ màng gọi gió. Anh nhớ nụ cười thân thương ngày "
           "trước. Anh mặt lạnh nhạt ở trên đỉnh đầu. Người chưa từng "
           "khóc là người chưa từng biết đau. Nỗi buồn của anh, anh cũng "
           "k muốn cho em biết đâu. Ngày dài tháng rộng che chở ta ôm lấy "
           "nhau. Giấu thật sâu vào trong đôi mắt buồn. Nhìn thấy nhau "
           "vui là điều ai cũng muốn, em đừng buồn. Thả xuống lại những "
           "kỉ niệm, anh dành cho em. Dù đẹp dù xấu dù có vụn vỡ, "
           "anh dành cho em. Nghe xong xin em đừng khóc, vì khi anh viết "
           "đã bao lần khóc. Anh thấy nặng nề đôi chân của mình vì lỡ đi "
           "nhẫm lên trên sườn dốc. Kết thúc không đẹp đâu phải nói quên "
           "là quên. Khi trong bao đêm anh say, anh vẫn muốn em 1 lần gọi "
           "tên. Và có thể trong giây phút nào đó, những tổn thương này "
           "hóa thành sắt đá. Thôi thì phần vui em cứ giữ, gồng gánh phần "
           "buồn cứ để anh. một con vịt xoè ra hai cái cánh")
    print(txt)
    # im = fit_text_to_image(fname, txt, 'times')
    # im.show()
