"""
Generate GitHub-style identicons (profile pictures).

GitHub identicons are 5x5 grids with horizontal symmetry:
  - col 0 <-> col 4  (mirrored)
  - col 1 <-> col 3  (mirrored)
  - col 2            (center, unique)
This gives 15 unique cells that drive the pattern.

This implementation matches the original unofficial Rust identicon library algorithm.

Usage:
    python github_faces.py <text> [output_file] [size]

Examples:
    python github_faces.py octocat
    python github_faces.py slytebot slytebot.png
    python github_faces.py "hello world" hello.png 200
"""

import hashlib
import sys
from typing import Iterator

from PIL import Image, ImageDraw


def nibbles(data: bytes) -> Iterator[int]:
    """Yield 4-bit nibbles from bytes (high nibble first, then low)."""
    for byte in data:
        yield (byte & 0xF0) >> 4  # high nibble
        yield byte & 0x0F         # low nibble


def hue_to_rgb(a: float, b: float, hue: float) -> float:
    """Convert hue component to RGB value (W3C CSS3 algorithm)."""
    h = hue
    if h < 0.0:
        h += 1.0
    elif h > 1.0:
        h -= 1.0

    if h < 1.0 / 6.0:
        return a + (b - a) * 6.0 * h
    if h < 1.0 / 2.0:
        return b
    if h < 2.0 / 3.0:
        return a + (b - a) * (2.0 / 3.0 - h) * 6.0
    return a


def hsl_to_rgb(h: float, s: float, l: float) -> tuple[int, int, int]:
    """Convert HSL (h: 0-360, s: 0-100, l: 0-100) to RGB (0-255 each).
    
    Uses the W3C CSS3 color specification algorithm to match Rust implementation.
    """
    hue = h / 360.0
    sat = s / 100.0
    lum = l / 100.0

    if lum <= 0.5:
        b_val = lum * (sat + 1.0)
    else:
        b_val = lum + sat - lum * sat
    a_val = lum * 2.0 - b_val

    r = hue_to_rgb(a_val, b_val, hue + 1.0 / 3.0)
    g = hue_to_rgb(a_val, b_val, hue)
    b = hue_to_rgb(a_val, b_val, hue - 1.0 / 3.0)

    return (round(r * 255), round(g * 255), round(b * 255))


def generate_identicon(data: bytes, size: int = 420) -> Image.Image:
    """
    Generate a GitHub-style identicon image for the given MD5 hash bytes.

    Args:
        data: 16-byte MD5 digest.
        size: Output image size in pixels (square). Default 420.

    Returns:
        A PIL Image object.
    """
    ### Foreground color (matches Rust implementation)
    # Use last 4 bytes (indices 12-15) to determine HSL values.
    # Hue: 12 bits from bytes 12-13, mapped to 0-360
    h1 = (data[12] & 0x0F) << 8
    h2 = data[13]
    h = h1 | h2  # 0-4095

    s = data[14]  # 0-255
    l = data[15]  # 0-255

    # Map values to ranges (matches Rust map function)
    hue = h * 360 / 4095
    sat = s * 20 / 255
    lum = l * 20 / 255

    # Final HSL: sat = 65 - sat_offset (45-65%), lum = 75 - lum_offset (55-75%)
    fg_color = hsl_to_rgb(hue, 65.0 - sat, 75.0 - lum)
    bg_color = (240, 240, 240)

    ### Cell pattern using nibbles
    # Iterate columns 2,1,0 (reversed), then rows 0-4
    # A cell is filled if nibble % 2 == 0 (even)
    grid: list[list[bool]] = [[False] * 5 for _ in range(5)]
    nib_iter = nibbles(data)

    for col in range(2, -1, -1):  # columns 2, 1, 0
        for row in range(5):
            nib = next(nib_iter, 1)  # default 1 (odd = not filled)
            filled = (nib % 2 == 0)
            grid[row][col] = filled
            grid[row][4 - col] = filled  # mirror

    ### Render
    pixel_size = 70
    margin = pixel_size // 2  # 35

    img = Image.new("RGB", (size, size), bg_color)
    draw = ImageDraw.Draw(img)

    for row in range(5):
        for col in range(5):
            if grid[row][col]:
                x = col * pixel_size + margin
                y = row * pixel_size + margin
                # Rust uses exclusive end coords, PIL rectangle is inclusive
                draw.rectangle([x, y, x + pixel_size - 1, y + pixel_size - 1], fill=fg_color)

    return img


def generate_identicon_from_text(text: str, size: int = 420) -> Image.Image:
    """
    Generate a GitHub-style identicon from a text string.

    Args:
        text: Input string (username, email, etc.). NOT lowercased (matches Rust).
        size: Output image size in pixels (square). Default 420.

    Returns:
        A PIL Image object.
    """
    digest = hashlib.md5(text.encode("utf-8")).digest()
    return generate_identicon(digest, size)


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    text    = sys.argv[1]
    output  = sys.argv[2] if len(sys.argv) > 2 else f"{text.replace(' ', '_')}_identicon.png"
    size    = int(sys.argv[3]) if len(sys.argv) > 3 else 420

    img = generate_identicon_from_text(text, size)
    img.save(output)
    print(f"Saved: '{output}'  ({size}x{size} px)  input='{text}'")


if __name__ == "__main__":
    main()
