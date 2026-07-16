# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""Generate PPT icons using MiniMax image-01 model.

Usage:
    uv run generate_icon.py --prompt "a growth arrow icon" --style flat-color
    uv run generate_icon.py --prompt "team collaboration" --style line-monochrome -n 3
    uv run generate_icon.py --prompt "innovation lightbulb" --custom-style "isometric, pastel colors, soft shadow" -n 2 --transparent
    uv run generate_icon.py --list-styles
    uv run generate_icon.py --list-subjects

Environment:
    MINIMAX_API_KEY  - MiniMax API key (required)
    MINIMAX_API_HOST - API host, default https://api.minimaxi.com
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: 'requests' not found. Run with: uv run generate_icon.py ...", file=sys.stderr)
    sys.exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
STYLES_PATH = SCRIPT_DIR / "styles.json"


def load_env_file() -> None:
    """Load .env file from script directory as fallback for env vars.

    Precedence: shell environment > .env file > built-in defaults.
    """
    env_path = SCRIPT_DIR / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_env_file()

DEFAULT_HOST = os.environ.get("MINIMAX_API_HOST", "https://api.minimaxi.com")
ENDPOINT = "/v1/image_generation"
MAX_PROMPT_LEN = 1500


def load_styles() -> dict:
    with open(STYLES_PATH, encoding="utf-8") as f:
        return json.load(f)


def list_styles() -> None:
    data = load_styles()
    print("Available icon styles:\n")
    print(f"  {'Key':<20} {'Name':<18} {'Name (CN)':<12} Description")
    print(f"  {'---':<20} {'----':<18} {'---------':<12} -----------")
    for key, s in data["styles"].items():
        print(f"  {key:<20} {s['name']:<18} {s['name_cn']:<12} {s['description'][:60]}")
    print(f"\n  Available backgrounds: {', '.join(data['backgrounds'].keys())}")


def list_subjects() -> None:
    data = load_styles()
    print("Common icon subjects (use as --prompt):\n")
    for i, subj in enumerate(data["common_subjects"], 1):
        print(f"  {i:>2}. {subj}")


def build_prompt(
    user_prompt: str,
    style_key: str | None,
    custom_style: str | None,
    background: str,
) -> str:
    data = load_styles()
    parts: list[str] = []

    user_clean = user_prompt.strip()
    if not user_clean.startswith("a ") and not user_clean.startswith("an "):
        user_clean = f"a {user_clean}"
    parts.append(user_clean)

    if custom_style:
        parts.append(custom_style.strip())
    elif style_key:
        styles = data["styles"]
        if style_key not in styles:
            print(f"ERROR: style '{style_key}' not found. Use --list-styles.", file=sys.stderr)
            sys.exit(1)
        parts.append(styles[style_key]["prompt_suffix"])
    else:
        parts.append("icon design, clean, centered composition, simple, high quality")

    bg_desc = data["backgrounds"].get(background, data["backgrounds"]["white"])
    parts.append(bg_desc)

    parts.append("icon design, centered composition, no text, no watermark")
    full = ", ".join(parts)
    if len(full) > MAX_PROMPT_LEN:
        full = full[:MAX_PROMPT_LEN]
    return full


def call_image_generation(
    prompt: str,
    n: int = 1,
    aspect_ratio: str = "1:1",
    api_key: str | None = None,
    host: str | None = None,
    seed: int | None = None,
) -> dict:
    api_key = api_key or os.environ.get("MINIMAX_API_KEY")
    if not api_key:
        print("ERROR: MINIMAX_API_KEY not set. Export it or pass --api-key.", file=sys.stderr)
        sys.exit(1)

    host = host or DEFAULT_HOST
    url = f"{host.rstrip('/')}{ENDPOINT}"

    payload: dict = {
        "model": "image-01",
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "n": n,
        "response_format": "base64",
        "prompt_optimizer": True,
        "aigc_watermark": False,
    }
    if seed is not None:
        payload["seed"] = seed

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    result = resp.json()

    base_resp = result.get("base_resp", {})
    status_code = base_resp.get("status_code", -1)
    if status_code != 0:
        print(
            f"API ERROR [{status_code}]: {base_resp.get('status_msg', 'unknown')}",
            file=sys.stderr,
        )
        sys.exit(1)

    return result


def slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
    return slug[:40] if slug else "icon"


def save_images(result: dict, output_dir: Path, name_base: str) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    data = result.get("data", {})
    images_b64 = data.get("image_base64", [])
    if not images_b64:
        images_url = data.get("image_urls", [])
        if images_url:
            print("WARNING: API returned URLs instead of base64. Downloading...", file=sys.stderr)
            saved = []
            for i, url in enumerate(images_url):
                resp = requests.get(url, timeout=60)
                resp.raise_for_status()
                path = output_dir / f"{name_base}-{i}.png"
                path.write_bytes(resp.content)
                saved.append(path)
            return saved
        print("ERROR: No images in response.", file=sys.stderr)
        sys.exit(1)

    saved = []
    for i, b64 in enumerate(images_b64):
        img_bytes = base64.b64decode(b64)
        suffix = f"-{i}" if len(images_b64) > 1 else ""
        path = output_dir / f"{name_base}{suffix}.png"
        path.write_bytes(img_bytes)
        saved.append(path)
    return saved


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate PPT icons using MiniMax image-01 model.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  %(prog)s --list-styles
  %(prog)s --prompt "growth arrow" --style flat-color
  %(prog)s --prompt "team collaboration" --style line-monochrome -n 3
  %(prog)s --prompt "innovation" --custom-style "isometric, pastel" --transparent
""",
    )
    parser.add_argument("--prompt", "-p", help="Icon subject description, e.g. 'growth arrow'")
    parser.add_argument("--style", "-s", help="Preset style key (use --list-styles to see options)")
    parser.add_argument("--custom-style", help="Custom style description (overrides --style)")
    parser.add_argument("-n", type=int, default=1, help="Number of images to generate (1-9), default 1")
    parser.add_argument("--aspect-ratio", default="1:1", help="Aspect ratio, default 1:1")
    parser.add_argument("--background", default="white", help="Background preset key, default 'white'")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--transparent", action="store_true", help="Remove background (post-process to transparent PNG)")
    parser.add_argument("--output", "-o", default="./output", help="Output directory, default ./output")
    parser.add_argument("--name", help="Base filename for output (default: slugified prompt)")
    parser.add_argument("--api-key", help="MiniMax API key (or set MINIMAX_API_KEY env)")
    parser.add_argument("--host", help="API host (or set MINIMAX_API_HOST env)")
    parser.add_argument("--list-styles", action="store_true", help="List available preset styles and exit")
    parser.add_argument("--list-subjects", action="store_true", help="List common icon subjects and exit")
    parser.add_argument("--dry-run", action="store_true", help="Print the constructed prompt and exit without calling API")

    args = parser.parse_args()

    if args.list_styles:
        list_styles()
        return
    if args.list_subjects:
        list_subjects()
        return
    if not args.prompt:
        parser.error("--prompt is required (unless using --list-styles or --list-subjects)")

    if not (1 <= args.n <= 9):
        parser.error("-n must be between 1 and 9")

    prompt = build_prompt(args.prompt, args.style, args.custom_style, args.background)

    if args.dry_run:
        print(f"Constructed prompt ({len(prompt)} chars):")
        print(f"  {prompt}")
        return

    print(f"Generating {args.n} icon(s)...")
    print(f"Prompt: {prompt[:120]}{'...' if len(prompt) > 120 else ''}")

    t0 = time.time()
    result = call_image_generation(
        prompt=prompt,
        n=args.n,
        aspect_ratio=args.aspect_ratio,
        api_key=args.api_key,
        host=args.host,
        seed=args.seed,
    )
    elapsed = time.time() - t0

    meta = result.get("metadata", {})
    print(f"API success: {meta.get('success_count', '?')} generated, {meta.get('failed_count', '?')} blocked, {elapsed:.1f}s")

    output_dir = Path(args.output)
    name_base = args.name or slugify(args.prompt)
    saved = save_images(result, output_dir, name_base)

    print(f"\nSaved {len(saved)} image(s):")
    for p in saved:
        print(f"  {p}")

    if args.transparent:
        print("\nRemoving backgrounds...")
        try:
            remove_bg_path = SCRIPT_DIR / "remove_bg.py"
            for p in saved:
                ret = os.system(f'uv run "{remove_bg_path}" "{p}" --output "{p}"')
                if ret == 0:
                    print(f"  Transparent: {p}")
                else:
                    print(f"  WARNING: bg removal failed for {p}", file=sys.stderr)
        except Exception as e:
            print(f"  WARNING: could not run remove_bg.py: {e}", file=sys.stderr)
            print(f"  Run manually: uv run remove_bg.py <image_path>", file=sys.stderr)

    print("\nDone.")


if __name__ == "__main__":
    main()
