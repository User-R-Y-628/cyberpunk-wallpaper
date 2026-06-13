"""
Resize and optimize generated images to 1080x1920 portrait wallpaper format.
Usage: python process.py [--input output/] [--output processed/]
"""

import argparse
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
TARGET_SIZE = (TARGET_WIDTH, TARGET_HEIGHT)


def process_image(src: Path, dest: Path, sharpen: bool = True, vibrance: float = 1.1) -> None:
    with Image.open(src) as img:
        img = img.convert("RGB")

        src_ratio = img.width / img.height
        target_ratio = TARGET_WIDTH / TARGET_HEIGHT

        if src_ratio > target_ratio:
            # Wider than target: fit height, crop width
            new_h = TARGET_HEIGHT
            new_w = int(new_h * src_ratio)
        else:
            # Taller than target: fit width, crop height
            new_w = TARGET_WIDTH
            new_h = int(new_w / src_ratio)

        img = img.resize((new_w, new_h), Image.LANCZOS)

        left = (new_w - TARGET_WIDTH) // 2
        top = (new_h - TARGET_HEIGHT) // 2
        img = img.crop((left, top, left + TARGET_WIDTH, top + TARGET_HEIGHT))

        if sharpen:
            img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=120, threshold=3))

        if vibrance != 1.0:
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(vibrance)

        dest.parent.mkdir(parents=True, exist_ok=True)
        img.save(dest, "PNG", optimize=True, compress_level=6)
        print(f"[OK] {src.name} → {dest}")


def parse_args():
    parser = argparse.ArgumentParser(description="Resize wallpapers to 1080x1920")
    parser.add_argument("--input", default="output", help="Source directory (default: output/)")
    parser.add_argument("--output", default="processed", help="Destination directory (default: processed/)")
    parser.add_argument("--no-sharpen", action="store_true", help="Skip unsharp mask")
    parser.add_argument("--vibrance", type=float, default=1.1, help="Color vibrance multiplier (default: 1.1)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing processed files")
    return parser.parse_args()


def main():
    args = parse_args()
    src_dir = Path(args.input)
    dst_dir = Path(args.output)

    images = sorted(src_dir.glob("*.png")) + sorted(src_dir.glob("*.jpg")) + sorted(src_dir.glob("*.webp"))

    if not images:
        print(f"No images found in {src_dir}/")
        return

    print(f"Processing {len(images)} image(s): {src_dir}/ → {dst_dir}/\n")

    ok = skipped = errors = 0
    for src in images:
        dest = dst_dir / src.name
        if dest.exists() and not args.overwrite:
            print(f"[SKIP] {src.name} (exists, use --overwrite to replace)")
            skipped += 1
            continue
        try:
            process_image(src, dest, sharpen=not args.no_sharpen, vibrance=args.vibrance)
            ok += 1
        except Exception as e:
            print(f"[ERR]  {src.name}: {e}")
            errors += 1

    print(f"\nDone. {ok} processed, {skipped} skipped, {errors} errors.")


if __name__ == "__main__":
    main()
