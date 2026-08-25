#!/usr/bin/env python3
"""Render ratio-native cover packs from a reusable JSON layer manifest."""

from __future__ import annotations

import argparse
import json
import math
import tempfile
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageChops, ImageCms, ImageDraw, ImageFilter, ImageOps
except ImportError as exc:  # pragma: no cover - dependency failure is user-facing
    raise SystemExit(
        "Pillow is required. Install dependencies with: "
        "python3 -m pip install -r requirements.txt"
    ) from exc


RESAMPLING = Image.Resampling.LANCZOS


def srgb_profile() -> bytes | None:
    try:
        return ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    except Exception:
        return None


SRGB_PROFILE = srgb_profile()


def resolve_path(base: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (base / path).resolve()


def require_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise ValueError(f"{label} does not exist: {path}")


def parse_box(value: Any, label: str) -> tuple[int, int, int, int]:
    if not isinstance(value, list) or len(value) != 4:
        raise ValueError(f"{label} must be [left, top, width, height]")
    left, top, width, height = (int(item) for item in value)
    if left < 0 or top < 0 or width <= 0 or height <= 0:
        raise ValueError(f"{label} contains invalid coordinates: {value}")
    return left, top, width, height


def apply_mask(image: Image.Image, spec: dict[str, Any] | None) -> Image.Image:
    if not spec or spec.get("type", "none") == "none":
        return image

    width, height = image.size
    mask_type = spec.get("type")
    inset = max(0, int(spec.get("inset", 0)))
    blur = max(0.0, float(spec.get("blur", 0)))
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)

    if mask_type == "soft-rect":
        radius = max(0, int(spec.get("radius", min(width, height) * 0.05)))
        draw.rounded_rectangle(
            (inset, inset, width - inset - 1, height - inset - 1),
            radius=radius,
            fill=255,
        )
    elif mask_type == "ellipse":
        draw.ellipse((inset, inset, width - inset - 1, height - inset - 1), fill=255)
    elif mask_type == "polygon":
        raw_points = spec.get("points")
        if not isinstance(raw_points, list) or len(raw_points) < 3:
            raise ValueError("polygon mask needs at least three normalized points")
        points: list[tuple[int, int]] = []
        for item in raw_points:
            if not isinstance(item, list) or len(item) != 2:
                raise ValueError("polygon points must be [x, y]")
            x, y = float(item[0]), float(item[1])
            if not (0 <= x <= 1 and 0 <= y <= 1):
                raise ValueError("polygon points must use normalized 0-1 coordinates")
            points.append((round(x * (width - 1)), round(y * (height - 1))))
        draw.polygon(points, fill=255)
    else:
        raise ValueError(f"unsupported mask type: {mask_type}")

    if blur:
        mask = mask.filter(ImageFilter.GaussianBlur(blur))

    current_alpha = image.getchannel("A")
    image = image.copy()
    image.putalpha(ImageChops.multiply(current_alpha, mask))
    return image


def load_group(
    source: Image.Image,
    manifest_dir: Path,
    name: str,
    spec: dict[str, Any],
) -> Image.Image:
    if "path" in spec:
        layer_path = resolve_path(manifest_dir, str(spec["path"]))
        require_file(layer_path, f"group {name}")
        image = Image.open(layer_path).convert("RGBA")
    elif "crop" in spec:
        left, top, width, height = parse_box(spec["crop"], f"group {name} crop")
        if left + width > source.width or top + height > source.height:
            raise ValueError(f"group {name} crop exceeds source bounds")
        image = source.crop((left, top, left + width, top + height)).convert("RGBA")
    else:
        raise ValueError(f"group {name} needs either path or crop")
    return apply_mask(image, spec.get("mask"))


def fit_background(image: Image.Image, size: tuple[int, int], fit: str, color: str) -> Image.Image:
    if fit == "fill":
        return image.resize(size, RESAMPLING).convert("RGBA")
    if fit == "cover":
        return ImageOps.fit(image.convert("RGBA"), size, method=RESAMPLING)
    if fit == "contain":
        contained = ImageOps.contain(image.convert("RGBA"), size, method=RESAMPLING)
        canvas = Image.new("RGBA", size, color)
        canvas.alpha_composite(
            contained,
            ((size[0] - contained.width) // 2, (size[1] - contained.height) // 2),
        )
        return canvas
    raise ValueError(f"unsupported background fit: {fit}")


def normalized_position(value: Any, extent: int, label: str) -> int:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    return round(number * extent)


def composite_clipped(canvas: Image.Image, layer: Image.Image, x: int, y: int) -> None:
    """Alpha-composite a layer while safely clipping intentional edge crops."""
    left = max(0, -x)
    top = max(0, -y)
    right = min(layer.width, canvas.width - x)
    bottom = min(layer.height, canvas.height - y)
    if right <= left or bottom <= top:
        raise ValueError("placement falls completely outside the canvas")
    visible = layer.crop((left, top, right, bottom))
    canvas.alpha_composite(visible, (max(0, x), max(0, y)))


def render_output(
    output: dict[str, Any],
    groups: dict[str, Image.Image],
    group_specs: dict[str, dict[str, Any]],
    backgrounds: dict[str, dict[str, Any]],
    manifest_dir: Path,
    output_dir: Path,
    required_roles: set[str],
    scale: float,
    overwrite: bool,
) -> tuple[Path, list[dict[str, Any]]]:
    filename = str(output.get("filename", "")).strip()
    if not filename.lower().endswith(".png"):
        raise ValueError("each output filename must end in .png")
    base_width = int(output.get("width", 0))
    base_height = int(output.get("height", 0))
    if base_width <= 0 or base_height <= 0:
        raise ValueError(f"{filename} needs positive width and height")
    width = max(1, round(base_width * scale))
    height = max(1, round(base_height * scale))

    background_name = output.get("background")
    background_color = str(output.get("background_color", "#000000"))
    if background_name:
        if background_name not in backgrounds:
            raise ValueError(f"{filename} references unknown background: {background_name}")
        background_spec = backgrounds[background_name]
        background_path = resolve_path(manifest_dir, str(background_spec["path"]))
        require_file(background_path, f"background {background_name}")
        background_image = Image.open(background_path).convert("RGBA")
        canvas = fit_background(
            background_image,
            (width, height),
            str(background_spec.get("fit", "cover")),
            background_color,
        )
    else:
        canvas = Image.new("RGBA", (width, height), background_color)

    placements = output.get("placements")
    if not isinstance(placements, list) or not placements:
        raise ValueError(f"{filename} needs at least one placement")

    placed_roles: set[str] = set()
    report: list[dict[str, Any]] = []
    for index, placement in enumerate(placements):
        group_name = placement.get("group")
        if group_name not in groups:
            raise ValueError(f"{filename} placement {index} references unknown group: {group_name}")
        layer = groups[group_name]
        has_width = "width" in placement
        has_height = "height" in placement
        if has_width == has_height:
            raise ValueError(
                f"{filename} placement {group_name} must set exactly one of width or height"
            )
        if has_width:
            target_width = normalized_position(placement["width"], width, "placement width")
            if target_width <= 0:
                raise ValueError(f"{filename} placement {group_name} has non-positive width")
            target_height = max(1, round(layer.height * target_width / layer.width))
        else:
            target_height = normalized_position(placement["height"], height, "placement height")
            if target_height <= 0:
                raise ValueError(f"{filename} placement {group_name} has non-positive height")
            target_width = max(1, round(layer.width * target_height / layer.height))

        x = normalized_position(placement.get("x", 0), width, "placement x")
        y = normalized_position(placement.get("y", 0), height, "placement y")
        allow_crop = bool(placement.get("allow_crop", False))
        if not allow_crop and (x < 0 or y < 0 or x + target_width > width or y + target_height > height):
            raise ValueError(
                f"{filename} placement {group_name} exceeds canvas: "
                f"({x}, {y}, {target_width}, {target_height}) on {width}x{height}"
            )

        resized = layer.resize((target_width, target_height), RESAMPLING)
        composite_clipped(canvas, resized, x, y)
        role = str(group_specs[group_name].get("role", "")).strip()
        if role:
            placed_roles.add(role)
        report.append(
            {
                "group": group_name,
                "role": role,
                "box": [x, y, target_width, target_height],
                "allow_crop": allow_crop,
            }
        )

    missing_roles = required_roles - placed_roles
    if missing_roles:
        raise ValueError(f"{filename} is missing required roles: {sorted(missing_roles)}")

    destination = output_dir / filename
    if destination.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite existing output: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    save_args: dict[str, Any] = {"format": "PNG", "compress_level": 9}
    if SRGB_PROFILE:
        save_args["icc_profile"] = SRGB_PROFILE
    canvas.save(destination, **save_args)
    return destination, report


def render_pack(manifest_path: Path, scale: float, overwrite: bool) -> list[Path]:
    if not (0 < scale <= 1):
        raise ValueError("preview scale must be greater than 0 and no more than 1")
    manifest_path = manifest_path.resolve()
    require_file(manifest_path, "manifest")
    manifest_dir = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    source_path = resolve_path(manifest_dir, str(manifest["source"]))
    require_file(source_path, "source")
    source = Image.open(source_path).convert("RGBA")
    group_specs = manifest.get("groups")
    if not isinstance(group_specs, dict) or not group_specs:
        raise ValueError("manifest needs groups")
    groups = {
        name: load_group(source, manifest_dir, name, spec)
        for name, spec in group_specs.items()
    }

    raw_backgrounds = manifest.get("backgrounds", {})
    if not isinstance(raw_backgrounds, dict):
        raise ValueError("backgrounds must be an object")
    backgrounds: dict[str, dict[str, Any]] = {}
    for name, spec in raw_backgrounds.items():
        if isinstance(spec, str):
            backgrounds[name] = {"path": spec, "fit": "cover"}
        elif isinstance(spec, dict) and "path" in spec:
            backgrounds[name] = spec
        else:
            raise ValueError(f"background {name} needs a path")

    output_dir = resolve_path(manifest_dir, str(manifest["output_dir"]))
    if scale < 1:
        output_dir = output_dir / "previews"
    output_dir.mkdir(parents=True, exist_ok=True)
    required_roles = {str(role) for role in manifest.get("required_roles", [])}
    outputs = manifest.get("outputs")
    if not isinstance(outputs, list) or not outputs:
        raise ValueError("manifest needs outputs")

    destinations: list[Path] = []
    layout_report: dict[str, Any] = {}
    for output in outputs:
        destination, report = render_output(
            output,
            groups,
            group_specs,
            backgrounds,
            manifest_dir,
            output_dir,
            required_roles,
            scale,
            overwrite,
        )
        destinations.append(destination)
        layout_report[destination.name] = report

    report_path = output_dir / "layout-report.json"
    if report_path.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite existing report: {report_path}")
    report_path.write_text(
        json.dumps(
            {
                "source": str(source_path),
                "scale": scale,
                "outputs": layout_report,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return destinations


def run_self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="creator-cover-ratio-pack-") as temp:
        root = Path(temp)
        source_path = root / "source.png"
        background_path = root / "background.png"
        source = Image.new("RGB", (800, 600), "#121212")
        draw = ImageDraw.Draw(source)
        draw.rounded_rectangle((40, 40, 740, 190), radius=24, fill="#f4eee8")
        draw.ellipse((70, 220, 370, 520), fill="#e26a14")
        draw.rounded_rectangle((470, 150, 740, 570), radius=80, fill="#304050")
        source.save(source_path)
        background = Image.new("RGB", (1200, 600), "#0b0d10")
        ImageDraw.Draw(background).line((0, 300, 1200, 300), fill="#e26a14", width=10)
        background.save(background_path)

        manifest = {
            "source": str(source_path),
            "output_dir": str(root / "outputs"),
            "required_roles": ["title", "subject", "core"],
            "backgrounds": {"wide": {"path": str(background_path), "fit": "fill"}},
            "groups": {
                "title": {
                    "role": "title",
                    "crop": [40, 40, 700, 150],
                    "mask": {"type": "soft-rect", "inset": 2, "blur": 2},
                },
                "core": {
                    "role": "core",
                    "crop": [70, 220, 300, 300],
                    "mask": {"type": "ellipse", "inset": 2, "blur": 2},
                },
                "subject": {
                    "role": "subject",
                    "crop": [470, 150, 270, 420],
                    "mask": {
                        "type": "polygon",
                        "points": [[0.1, 0], [0.9, 0], [1, 1], [0, 1]],
                        "blur": 2,
                    },
                },
            },
            "outputs": [
                {
                    "filename": "3：4.png",
                    "width": 300,
                    "height": 400,
                    "background": "wide",
                    "placements": [
                        {"group": "title", "x": 0.05, "y": 0.05, "width": 0.9},
                        {"group": "core", "x": 0.05, "y": 0.48, "width": 0.42},
                        {"group": "subject", "x": 0.4, "y": 0.3, "height": 0.68},
                    ],
                },
                {
                    "filename": "16：9.png",
                    "width": 640,
                    "height": 360,
                    "background": "wide",
                    "placements": [
                        {"group": "title", "x": 0.04, "y": 0.08, "width": 0.52},
                        {"group": "core", "x": 0.43, "y": 0.34, "height": 0.56},
                        {"group": "subject", "x": 0.66, "y": 0.04, "height": 0.92},
                    ],
                },
                {
                    "filename": "5：1.png",
                    "width": 1000,
                    "height": 200,
                    "background": "wide",
                    "placements": [
                        {"group": "title", "x": 0.03, "y": 0.12, "width": 0.38},
                        {"group": "core", "x": 0.44, "y": 0.08, "height": 0.84},
                        {"group": "subject", "x": 0.77, "y": 0.02, "height": 0.96},
                    ],
                },
            ],
        }
        manifest_path = root / "layout.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        preview_paths = render_pack(manifest_path, 0.25, overwrite=True)
        final_paths = render_pack(manifest_path, 1.0, overwrite=True)
        expected = [(300, 400), (640, 360), (1000, 200)]
        if len(final_paths) != len(expected):
            raise AssertionError("final output count mismatch")
        for path, size in zip(final_paths, expected):
            with Image.open(path) as image:
                if image.size != size:
                    raise AssertionError(f"unexpected size for {path}: {image.size}")
                if SRGB_PROFILE and "icc_profile" not in image.info:
                    raise AssertionError(f"missing sRGB profile: {path}")
        if len(preview_paths) != 3:
            raise AssertionError("preview output count mismatch")
        print("OK: ratio pack renderer self-test passed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="?", type=Path)
    parser.add_argument("--preview-scale", type=float, default=1.0)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        run_self_test()
        return
    if args.manifest is None:
        parser.error("manifest is required unless --self-test is used")
    destinations = render_pack(args.manifest, args.preview_scale, args.overwrite)
    for destination in destinations:
        print(destination)


if __name__ == "__main__":
    main()
