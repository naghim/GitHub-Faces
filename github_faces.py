"""
Generate GitHub-style identicons (profile pictures).

GitHub identicons are 5x5 grids with horizontal symmetry:
  - col 0 <-> col 4  (mirrored)
  - col 1 <-> col 3  (mirrored)
  - col 2            (center, unique)
This gives 15 unique cells that drive the pattern.

NOTE: GitHub's exact algorithm is not public. This is an approximation based on
the classic identicon algorithm. The color and pattern generation is designed 
to produce similar results, but may not match GitHub's output exactly.

Usage:
    python github_faces.py <text> [output_file] [size]

Examples:
    python github_faces.py octocat
    python github_faces.py slytebot slytebot.png
    python github_faces.py "hello world" hello.png 200
"""

import colorsys
import hashlib
import sys

from PIL import Image, ImageDraw


def hsl_to_rgb(h: float, s: float, l: float) -> tuple[int, int, int]:
    """Convert HSL (h: 0-360, s: 0-1, l: 0-1) to an RGB tuple (0-255 each)."""
    # colorsys uses HLS ordering
    r, g, b = colorsys.hls_to_rgb(h / 360.0, l, s)
    return (int(r * 255), int(g * 255), int(b * 255))


def generate_identicon(text: str, size: int = 420) -> Image.Image:
    """
    Generate a GitHub-style identicon image for the given text.

    Args:
        text: Input string (username, email, etc.). Lowercased before hashing.
        size: Output image size in pixels (square). Default 420.

    Returns:
        A PIL Image object.
    """
    digest = hashlib.md5(text.lower().encode("utf-8")).digest()

    ### Main color
    # Use last 7 bytes for color to avoid overlap with pattern bytes.
    # Hue: full range. Saturation: 45-65%. Lightness: 55-75% (pastel range).
    hue        = ((digest[13] << 8) | digest[14]) % 360
    saturation = 0.45 + (digest[15] % 21) / 100.0   # 45-65%
    lightness  = 0.55 + (digest[12] % 21) / 100.0   # 55-75%

    fg_color = hsl_to_rgb(hue, saturation, lightness)
    bg_color = (240, 240, 240)  # light gray, matches GitHub

    ### Cell pattern
    # 15 unique cells (3 cols x 5 rows). Use first 15 bytes.
    # Cell is filled when the low bit is set (byte & 1).
    # This produces ~50% fill density on average.
    
    # Build 5x5 boolean grid, applying horizontal mirror symmetry.
    grid: list[list[bool]] = [[False] * 5 for _ in range(5)]
    idx = 0
    for row in range(5):
        for col in range(3):
            filled = (digest[idx] & 1) == 1
            grid[row][col] = filled
            grid[row][4 - col] = filled  # mirror: col 0<->4, col 1<->3
            idx += 1

    ### Render
    # Divide the image into a 7-unit grid: 1 unit padding on each side,
    # 5 units for the cell area. This reproduces the "padded frame" look.
    cell_size = size // 7                 # each of the 5 cells
    actual_grid = cell_size * 5
    padding = (size - actual_grid) // 2   # centers the grid precisely

    img = Image.new("RGB", (size, size), bg_color)
    draw = ImageDraw.Draw(img)

    for row in range(5):
        for col in range(5):
            if grid[row][col]:
                x0 = padding + col * cell_size
                y0 = padding + row * cell_size
                x1 = x0 + cell_size - 1
                y1 = y0 + cell_size - 1
                draw.rectangle([x0, y0, x1, y1], fill=fg_color)

    return img


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    text    = sys.argv[1]
    output  = sys.argv[2] if len(sys.argv) > 2 else f"{text.replace(' ', '_')}_identicon.png"
    size    = int(sys.argv[3]) if len(sys.argv) > 3 else 420

    img = generate_identicon(text, size)
    img.save(output)
    print(f"Saved: '{output}'  ({size}x{size} px)  input='{text}'")


if __name__ == "__main__":
    main()
