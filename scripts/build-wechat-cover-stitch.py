#!/usr/bin/env python3
"""Combine an approved 1:1 cover and an approved 2.35:1 cover side by side."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageCms


RESAMPLING = Image.Resampling.LANCZOS


def srgb_profile() -> bytes | None:
    try:
        return ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    except Exception:
        return None


def validate_ratio(width: int, height: int, target: float, tolerance: float, label: str) -> None:
    if width < 1 or height < 1 or abs(width / height - target) > tolerance:
        raise ValueError(f"{label} ratio is invalid: {width}x{height}")


def build_stitch(square_path: Path, wide_path: Path, output_path: Path) -> Path:
    if not square_path.is_file():
        raise FileNotFoundError(f"square image does not exist: {square_path}")
    if not wide_path.is_file():
        raise FileNotFoundError(f"wide image does not exist: {wide_path}")

    with Image.open(square_path) as square_source, Image.open(wide_path) as wide_source:
        validate_ratio(*square_source.size, 1.0, 0.005, "square image")
        validate_ratio(*wide_source.size, 2.35, 0.05, "wide image")

        target_height = wide_source.height
        square = square_source.convert("RGBA").resize((target_height, target_height), RESAMPLING)
        wide_width = round(wide_source.width * target_height / wide_source.height)
        wide = wide_source.convert("RGBA").resize((wide_width, target_height), RESAMPLING)

        canvas = Image.new("RGBA", (square.width + wide.width, target_height), (0, 0, 0, 255))
        canvas.alpha_composite(square, (0, 0))
        canvas.alpha_composite(wide, (square.width, 0))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_args: dict[str, object] = {"format": "PNG", "compress_level": 9}
        profile = srgb_profile()
        if profile:
            save_args["icc_profile"] = profile
        canvas.convert("RGB").save(output_path, **save_args)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Join an approved 1:1 image and an approved 2.35:1 image without a gap."
    )
    parser.add_argument("square", type=Path, help="approved 1:1 image")
    parser.add_argument("wide", type=Path, help="approved 2.35:1 image")
    parser.add_argument("--output", type=Path, help="output PNG path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = args.output or args.wide.parent / (
        f"公众号封面拼接_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    )
    print(build_stitch(args.square, args.wide, output).resolve())


if __name__ == "__main__":
    main()
