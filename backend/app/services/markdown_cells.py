"""Markdown pieces of a node description that a spreadsheet cell cannot show as text:
GFM tables (rendered as pictures) and images."""

import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

_SEPARATOR_RE = re.compile(r"^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?$")
_IMAGE_RE = re.compile(r"^!\[([^\]]*)\]\(([^)]*)\)$")

# Rendering: drawn at 2x for sharpness, shown at 1x
_SCALE = 2
_FONT_PX = 11
_PAD = 4
_MAX_WIDTH = 480  # px, about the width of the Description column
PICTURE_SCALE = 0.75  # extracted figures are shown at 75% of the size that fits the column
MAX_BLOCK_HEIGHT = 520  # px, a picture must fit in one Excel row (409 pt = 545 px)
_MIN_COLUMN = 60
_HEADER_FILL = (217, 217, 217)
_FONT_DIRS = ("/usr/share/fonts/truetype/liberation", "/usr/share/fonts/truetype/dejavu")
_FONT_FILES = {False: ("LiberationSans-Regular.ttf", "DejaVuSans.ttf"),
               True: ("LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf")}


@dataclass(frozen=True)
class Segment:
    """A piece of a description: ``text``, ``table`` (rows of cells) or ``image``."""

    kind: str  # "text" | "table" | "image"
    text: str = ""
    rows: tuple[tuple[str, ...], ...] = ()
    alt: str = ""
    target: str = ""


@dataclass(frozen=True)
class Picture:
    """A rendered or loaded picture and its display size in px."""

    png: bytes
    width: int
    height: int


def _split_cells(line: str) -> tuple[str, ...]:
    line = line.strip()
    line = line.removeprefix("|").removesuffix("|")
    return tuple(re.sub(r"<br\s*/?>", "\n", c, flags=re.IGNORECASE).replace("**", "").strip()
                 for c in line.split("|"))


def split_segments(markdown: str) -> list[Segment]:
    """Split a description into text, GFM tables and standalone images, in order."""
    lines = markdown.splitlines()
    segments: list[Segment] = []
    text: list[str] = []

    def flush_text() -> None:
        if any(t.strip() for t in text):
            segments.append(Segment("text", text="\n".join(text).strip()))
        text.clear()

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("|") and i + 1 < len(lines) and _SEPARATOR_RE.match(lines[i + 1].strip()):
            end = i + 2
            while end < len(lines) and lines[end].strip().startswith("|"):
                end += 1
            flush_text()
            rows = [_split_cells(lines[i])] + [_split_cells(r) for r in lines[i + 2:end]]
            width = max(len(r) for r in rows)
            segments.append(Segment("table", rows=tuple(r + ("",) * (width - len(r)) for r in rows)))
            i = end
            continue
        image = _IMAGE_RE.match(line.strip())
        if image:
            flush_text()
            segments.append(Segment("image", alt=image.group(1), target=image.group(2)))
        else:
            text.append(line)
        i += 1
    flush_text()
    return segments


def table_as_text(rows: tuple[tuple[str, ...], ...]) -> str:
    """Plain-text fallback of a table, one line per row."""
    return "\n".join(" | ".join(c.replace("\n", " ") for c in row) for row in rows)


def _font(bold: bool) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    for directory in _FONT_DIRS:
        for name in _FONT_FILES[bold]:
            path = Path(directory) / name
            if path.is_file():
                return ImageFont.truetype(str(path), _FONT_PX * _SCALE)
    return ImageFont.load_default(size=_FONT_PX * _SCALE)


def _wrap(text: str, font, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        current = ""
        for word in paragraph.split(" "):
            candidate = f"{current} {word}".strip()
            if current and font.getlength(candidate) > max_width:
                lines.append(current)
                current = word
            else:
                current = candidate
            while font.getlength(current) > max_width and len(current) > 1:  # unbreakable word
                cut = len(current) - 1
                while cut > 1 and font.getlength(current[:cut]) > max_width:
                    cut -= 1
                lines.append(current[:cut])
                current = current[cut:]
        lines.append(current)
    return lines


def _table_layout(rows: tuple[tuple[str, ...], ...]):
    """Column widths and wrapped cell lines of a table, in drawing pixels."""
    regular, bold = _font(False), _font(True)
    pad, columns = _PAD * _SCALE, len(rows[0])
    natural = [
        max(max((regular if r else bold).getlength(line) for line in row[c].split("\n") or [""])
            for r, row in enumerate(rows)) + 2 * pad + 2  # +2: rounding slack, no self-wrapping
        for c in range(columns)
    ]
    budget = _MAX_WIDTH * _SCALE
    if sum(natural) > budget:  # shrink the wide columns first, never below the minimum
        floor = [min(n, _MIN_COLUMN * _SCALE) for n in natural]
        spare = max(budget - sum(floor), 0)
        extra = sum(n - f for n, f in zip(natural, floor)) or 1
        widths = [f + (n - f) * spare / extra for n, f in zip(natural, floor)]
    else:
        widths = natural
    widths = [int(w) for w in widths]
    line_height = int(_FONT_PX * _SCALE * 1.25)
    wrapped = [
        [_wrap(cell, bold if r == 0 else regular, widths[c] - 2 * pad) for c, cell in enumerate(row)]
        for r, row in enumerate(rows)
    ]
    heights = [max(len(cell) for cell in row) * line_height + 2 * pad for row in wrapped]
    return widths, wrapped, heights, line_height, regular, bold


def _draw_rows(
    widths, wrapped, heights, line_height, regular, bold, indexes: list[int], max_height: int
) -> Picture:
    """Draw the given table rows (the header is row 0 and is drawn grey and bold)."""
    pad = _PAD * _SCALE
    image = Image.new("RGB", (sum(widths) + 1, sum(heights[r] for r in indexes) + 1), "white")
    draw = ImageDraw.Draw(image)
    top = 0
    for r in indexes:
        left = 0
        for c, lines in enumerate(wrapped[r]):
            draw.rectangle(
                [left, top, left + widths[c], top + heights[r]],
                fill=_HEADER_FILL if r == 0 else "white", outline="black", width=_SCALE // 2 or 1,
            )
            for n, line in enumerate(lines):
                draw.text((left + pad, top + pad + n * line_height), line,
                          fill="black", font=bold if r == 0 else regular)
            left += widths[c]
        top += heights[r]
    if image.height > max_height * _SCALE:  # one row alone is taller than a spreadsheet row
        ratio = max_height * _SCALE / image.height
        image = image.resize((max(int(image.width * ratio), 1), max_height * _SCALE), Image.LANCZOS)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return Picture(buffer.getvalue(), image.width // _SCALE, image.height // _SCALE)


def render_table(
    rows: tuple[tuple[str, ...], ...], max_height: int = MAX_BLOCK_HEIGHT
) -> list[Picture]:
    """Draw a table with grid lines and a grey bold header, like a Word table.

    A table taller than ``max_height`` px is cut between rows into several pictures,
    each one repeating the header.
    """
    layout = _table_layout(rows)
    heights = layout[2]
    limit = max_height * _SCALE
    slices: list[list[int]] = [[0]]
    used = heights[0]
    for r in range(1, len(rows)):
        if used + heights[r] > limit and len(slices[-1]) > 1:
            slices.append([0])
            used = heights[0]
        slices[-1].append(r)
        used += heights[r]
    return [_draw_rows(*layout, indexes, max_height) for indexes in slices]


def load_picture(path: Path) -> Picture | None:
    """Read an extracted figure, scaled down to the column width. ``None`` if unreadable."""
    try:
        with Image.open(path) as source:
            width, height = source.size
            buffer = BytesIO()
            source.convert("RGB").save(buffer, format="PNG")
    except OSError:
        return None
    ratio = min(1.0, _MAX_WIDTH / width, MAX_BLOCK_HEIGHT / height) * PICTURE_SCALE
    return Picture(buffer.getvalue(), max(round(width * ratio), 1), max(round(height * ratio), 1))
