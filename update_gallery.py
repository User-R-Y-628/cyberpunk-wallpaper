"""
Scan processed/ directory and regenerate docs/index.html gallery.
Usage: python update_gallery.py [--dir processed] [--base-url ./images]
"""

import argparse
import csv
import json
import shutil
from datetime import datetime
from pathlib import Path

DOCS_DIR = Path("docs")
IMAGES_DIR = DOCS_DIR / "images"
PROMPTS_CSV = "prompts.csv"
INDEX_HTML = DOCS_DIR / "index.html"


def load_prompts(csv_path: str) -> dict[str, dict]:
    prompts = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            prompts[row["id"]] = row
    return prompts


def extract_id(filename: str) -> str:
    """Extract zero-padded ID from filename like '001_neon_tokyo_rain.png'."""
    part = filename.split("_")[0]
    return str(int(part))  # strip leading zeros for dict lookup


def build_card(image_file: Path, prompt_data: dict | None, idx: int) -> str:
    filename = image_file.name
    title = prompt_data["title"] if prompt_data else filename.replace(".png", "").replace("_", " ").title()
    tags = prompt_data["style_tags"].split(",") if prompt_data else []
    prompt_text = prompt_data["prompt"] if prompt_data else ""
    prompt_id = prompt_data["id"] if prompt_data else str(idx)

    tags_html = "".join(f'<span class="tag">{t.strip()}</span>' for t in tags)
    prompt_short = (prompt_text[:120] + "…") if len(prompt_text) > 120 else prompt_text

    return f"""
        <article class="card" data-id="{prompt_id}" data-tags="{' '.join(t.strip() for t in tags)}">
          <div class="card-img-wrap">
            <img src="images/{filename}" alt="{title}" loading="lazy" />
            <a class="download-btn" href="images/{filename}" download="{filename}" title="Download">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 15V3m0 12l-4-4m4 4l4-4M2 17l.621 2.485A2 2 0 0 0 4.561 21h14.878a2 2 0 0 0 1.94-1.515L22 17"/>
              </svg>
            </a>
          </div>
          <div class="card-body">
            <h3 class="card-title">#{prompt_id} {title}</h3>
            <p class="card-prompt">{prompt_short}</p>
            <div class="tags">{tags_html}</div>
          </div>
        </article>"""


def build_html(cards: str, total: int, generated_at: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Cyberpunk Wallpaper Gallery</title>
  <link rel="stylesheet" href="style.css" />
</head>
<body>
  <header class="site-header">
    <div class="header-inner">
      <h1 class="logo">CYBER<span>WALL</span></h1>
      <p class="subtitle">AI-Generated 1080×1920 Cyberpunk Wallpapers</p>
      <p class="meta">{total} wallpapers · Updated {generated_at}</p>
    </div>
  </header>

  <nav class="filter-bar" aria-label="Filter by tag">
    <button class="filter-btn active" data-filter="all">All</button>
    <button class="filter-btn" data-filter="neon">Neon</button>
    <button class="filter-btn" data-filter="city">City</button>
    <button class="filter-btn" data-filter="rain">Rain</button>
    <button class="filter-btn" data-filter="dark">Dark</button>
    <button class="filter-btn" data-filter="abstract">Abstract</button>
    <button class="filter-btn" data-filter="japan">Japan</button>
    <button class="filter-btn" data-filter="space">Space</button>
  </nav>

  <main class="gallery" id="gallery">
{cards}
  </main>

  <footer class="site-footer">
    <p>Generated with <a href="https://replicate.com" target="_blank" rel="noopener">Replicate</a> · Flux 1.1 Pro</p>
  </footer>

  <script>
    const btns = document.querySelectorAll('.filter-btn');
    const cards = document.querySelectorAll('.card');
    btns.forEach(btn => {{
      btn.addEventListener('click', () => {{
        btns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const f = btn.dataset.filter;
        cards.forEach(c => {{
          const show = f === 'all' || c.dataset.tags.includes(f);
          c.style.display = show ? '' : 'none';
        }});
      }});
    }});
  </script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Rebuild docs/index.html from processed images")
    parser.add_argument("--dir", default="processed", help="Source directory of processed images")
    parser.add_argument("--copy", action="store_true", help="Copy images into docs/images/")
    args = parser.parse_args()

    src_dir = Path(args.dir)
    prompts = load_prompts(PROMPTS_CSV)

    images = sorted(src_dir.glob("*.png")) + sorted(src_dir.glob("*.jpg"))
    if not images:
        print(f"No images found in {src_dir}/")
        return

    DOCS_DIR.mkdir(exist_ok=True)
    IMAGES_DIR.mkdir(exist_ok=True)

    if args.copy:
        for img in images:
            shutil.copy2(img, IMAGES_DIR / img.name)
            print(f"[COPY] {img.name}")

    cards_html = ""
    for i, img in enumerate(images, 1):
        try:
            pid = extract_id(img.stem)
            prompt_data = prompts.get(pid)
        except (ValueError, IndexError):
            prompt_data = None
        cards_html += build_card(img, prompt_data, i)

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    html = build_html(cards_html, len(images), generated_at)
    INDEX_HTML.write_text(html, encoding="utf-8")
    print(f"\nGallery updated: {INDEX_HTML}  ({len(images)} images)")


if __name__ == "__main__":
    main()
