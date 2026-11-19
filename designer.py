import json
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont

# ---- قالب ثابت پیج ----
WIDTH, HEIGHT = 1080, 1350
MARGIN = 100
BACKGROUND = (245, 241, 234)
TEXT_COLOR = (43, 43, 43)
ACCENT = (107, 143, 113)
PAGE_NAME = "@your_page"

FONT_BOLD = "fonts/Vazirmatn-Bold.ttf"
FONT_REGULAR = "fonts/Vazirmatn-Regular.ttf"


def load_font(path, size):
    return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.BASIC)


def shape(text):
    return get_display(arabic_reshaper.reshape(text))


def wrap(text, font, max_width, draw):
    lines, current = [], ""
    for word in text.split():
        test = f"{current} {word}".strip()
        if draw.textlength(shape(test), font=font) <= max_width:
            current = test
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_lines(draw, lines, font, y, line_height, align="right"):
    for line in lines:
        visual = shape(line)
        width = draw.textlength(visual, font=font)
        if align == "center":
            x = (WIDTH - width) / 2
        else:
            x = WIDTH - MARGIN - width
        draw.text((x, y), visual, font=font, fill=TEXT_COLOR)
        y += line_height
    return y


def make_slide(slide, number, total):
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    text_width = WIDTH - 2 * MARGIN

    if number == 1:
        font = load_font(FONT_BOLD, 76)
        lines = wrap(slide["body"], font, text_width, draw)
        block_height = len(lines) * 120
        y = (HEIGHT - block_height) / 2 - 40
        draw_lines(draw, lines, font, y, 120, align="center")
        hint = load_font(FONT_REGULAR, 34)
        draw_lines(draw, ["ورق بزن"], hint, HEIGHT - 220, 50, align="center")
    else:
        title_font = load_font(FONT_BOLD, 64)
        body_font = load_font(FONT_REGULAR, 46)
        draw.rectangle([WIDTH - MARGIN - 80, 200,
                       WIDTH - MARGIN, 210], fill=ACCENT)
        title_lines = wrap(slide["title"], title_font, text_width, draw)
        y = draw_lines(draw, title_lines, title_font, 250, 95)
        body_lines = wrap(slide["body"], body_font, text_width, draw)
        draw_lines(draw, body_lines, body_font, y + 50, 80)

    footer = load_font(FONT_REGULAR, 30)
    draw.text((MARGIN, HEIGHT - 110),
              f"{number}/{total}", font=footer, fill=ACCENT)
    name_width = draw.textlength(PAGE_NAME, font=footer)
    draw.text((WIDTH - MARGIN - name_width, HEIGHT - 110),
              PAGE_NAME, font=footer, fill=ACCENT)
    return image


if __name__ == "__main__":
    carousel = json.loads(Path("carousel.json").read_text(encoding="utf-8"))
    slides = carousel["slides"]
    out_dir = Path("slides")
    out_dir.mkdir(exist_ok=True)
    for i, slide in enumerate(slides, start=1):
        image = make_slide(slide, i, len(slides))
        image.save(out_dir / f"slide_{i:02d}.png")
    print(f"Saved {len(slides)} slides to the 'slides' folder")
