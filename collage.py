"""
Generates a collage of GitHub-style icons ("identicons").

Usage:
    python collage.py <output_file> <text1> <text2> [text3] ...
    python collage.py <output_file> --random <count> [--cols <num>] [--size <pixels>] [--padding <pixels>]

Examples:
    python collage.py wall.png alice bob charlie dave
    python collage.py random_wall.png --random 25
    python collage.py grid.png --random 100 --cols 10
"""

import argparse
import math
import random
import string
import sys

from PIL import Image

from github_faces import generate_identicon


def random_string(length: int = 8) -> str:
    """Generate a random alphanumeric string."""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def create_collage(
    texts: list[str],
    cols: int | None = None,
    cell_size: int = 120,
    padding: int = 4,
    bg_color: tuple[int, int, int] = (255, 255, 255),
) -> Image.Image:
    """
    Create a collage of identicons.

    Args:
        texts: List of strings to generate identicons for.
        cols: Number of columns. If None, computed as ceil(sqrt(count)).
        cell_size: Size of each identicon in the grid.
        padding: Pixels between identicons.
        bg_color: Background color of the collage.

    Returns:
        A PIL Image containing the collage.
    """
    count = len(texts)
    if count == 0:
        raise ValueError("Need at least one text input")

    # Determine grid dimensions
    if cols is None:
        cols = math.ceil(math.sqrt(count))
    rows = math.ceil(count / cols)

    # Calculate total image size
    total_width = cols * cell_size + (cols + 1) * padding
    total_height = rows * cell_size + (rows + 1) * padding

    collage = Image.new("RGB", (total_width, total_height), bg_color)

    for i, text in enumerate(texts):
        row = i // cols
        col = i % cols

        # Generate and resize identicon
        icon = generate_identicon(text, size=cell_size)

        # Calculate position
        x = padding + col * (cell_size + padding)
        y = padding + row * (cell_size + padding)

        collage.paste(icon, (x, y))

    return collage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a collage of GitHub-style identicons."
    )
    parser.add_argument("output", help="Output filename (e.g., collage.png)")
    parser.add_argument("texts", nargs="*", help="Text strings to generate identicons for")
    parser.add_argument(
        "--random", "-r", type=int, metavar="N",
        help="Generate N random identicons instead of using text inputs"
    )
    parser.add_argument(
        "--cols", "-c", type=int, default=None,
        help="Number of columns (default: auto, based on sqrt)"
    )
    parser.add_argument(
        "--size", "-s", type=int, default=120,
        help="Size of each identicon in pixels (default: 120)"
    )
    parser.add_argument(
        "--padding", "-p", type=int, default=4,
        help="Padding between identicons in pixels (default: 4)"
    )

    args = parser.parse_args()

    if args.random:
        texts = [random_string() for _ in range(args.random)]
        print(f"Generating {args.random} random identicons...")
    elif args.texts:
        texts = args.texts
    else:
        parser.print_help()
        sys.exit(1)

    collage = create_collage(
        texts,
        cols=args.cols,
        cell_size=args.size,
        padding=args.padding,
    )

    collage.save(args.output)

    # Calculate final dimensions
    cols = args.cols or math.ceil(math.sqrt(len(texts)))
    rows = math.ceil(len(texts) / cols)
    print(f"Saved: '{args.output}'  ({collage.width}×{collage.height} px)  "
          f"{len(texts)} identicons in {rows}×{cols} grid")


if __name__ == "__main__":
    main()
