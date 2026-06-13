"""
Generate cyberpunk wallpapers using Replicate Flux API.
Usage: python generate.py [--ids 1,2,3] [--all] [--start N] [--end N]
"""

import csv
import os
import time
import argparse
import urllib.request
from pathlib import Path

import replicate

PROMPTS_CSV = "prompts.csv"
OUTPUT_DIR = Path("output")
MODEL = "black-forest-labs/flux-1.1-pro"

GENERATION_PARAMS = {
    "width": 768,
    "height": 1344,
    "num_inference_steps": 28,
    "guidance_scale": 3.5,
    "output_format": "png",
    "output_quality": 95,
}

STYLE_SUFFIX = (
    ", cyberpunk aesthetic, ultra detailed, cinematic lighting, "
    "professional photography, 8k resolution, masterpiece"
)


def load_prompts(csv_path: str) -> list[dict]:
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def download_image(url: str, dest: Path) -> None:
    urllib.request.urlretrieve(url, dest)


def generate_image(row: dict) -> Path:
    prompt_id = row["id"].zfill(3)
    output_path = OUTPUT_DIR / f"{prompt_id}_{sanitize(row['title'])}.png"

    if output_path.exists():
        print(f"[SKIP] #{row['id']} {row['title']} already exists")
        return output_path

    full_prompt = row["prompt"] + STYLE_SUFFIX
    print(f"[GEN]  #{row['id']} {row['title']}")

    output = replicate.run(MODEL, input={**GENERATION_PARAMS, "prompt": full_prompt})

    # Replicate returns a list of FileOutput objects or URLs
    url = output[0] if isinstance(output, list) else output
    url_str = str(url)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    download_image(url_str, output_path)
    print(f"[DONE] saved → {output_path}")
    return output_path


def sanitize(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name).lower()


def parse_args():
    parser = argparse.ArgumentParser(description="Generate cyberpunk wallpapers via Replicate Flux")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Generate all prompts")
    group.add_argument("--ids", help="Comma-separated IDs to generate, e.g. 1,3,5")
    group.add_argument("--start", type=int, help="Generate from this ID onwards")
    parser.add_argument("--end", type=int, help="Stop at this ID (used with --start)")
    parser.add_argument("--delay", type=float, default=12.0, help="Seconds between requests (default: 12)")
    return parser.parse_args()


def main():
    args = parse_args()
    rows = load_prompts(PROMPTS_CSV)

    if args.ids:
        target_ids = set(args.ids.split(","))
        rows = [r for r in rows if r["id"] in target_ids]
    elif args.start:
        rows = [r for r in rows if int(r["id"]) >= args.start]
        if args.end:
            rows = [r for r in rows if int(r["id"]) <= args.end]
    elif not args.all:
        # Default: generate first 5 as a test batch
        rows = rows[:5]
        print("No filter specified — running first 5 prompts as a test batch.")
        print("Use --all to generate all 50.\n")

    print(f"Generating {len(rows)} image(s)...\n")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for i, row in enumerate(rows):
        try:
            generate_image(row)
        except Exception as e:
            print(f"[ERR]  #{row['id']} {row['title']}: {e}")
        if i < len(rows) - 1:
            time.sleep(args.delay)

    print("\nDone.")


if __name__ == "__main__":
    main()
