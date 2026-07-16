# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28",
# ]
# ///
"""Analyze an example icon image to extract its style description.

Uses the MiniMax VLM (Vision Language Model) API to understand the visual
style of a user-provided icon, then outputs a style prompt that can be fed
into generate_icon.py via --custom-style.

Usage:
    uv run analyze_style.py path/to/example_icon.png
    uv run analyze_style.py https://example.com/icon.png
    uv run analyze_style.py path/to/icon.png --output-style-only

Environment:
    MINIMAX_API_KEY  - MiniMax API key (required)
    MINIMAX_API_HOST - API host, default https://api.minimaxi.com
"""

from __future__ import annotations

import argparse
import base64
import os
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: 'requests' not found. Run with: uv run analyze_style.py ...", file=sys.stderr)
    sys.exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent


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
CHAT_ENDPOINT = "/v1/chat/completions"
SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB (API limit)

ANALYSIS_PROMPT = """\
You are an expert icon designer. Analyze this icon image and describe its visual \
style in detail for the purpose of reproducing the same style in an AI image generator.

Describe the following aspects concisely:
1. Overall style (flat, line, 3D, isometric, hand-drawn, gradient, etc.)
2. Color palette (specific colors or color scheme - be precise, e.g. "navy blue (#1A237E) and amber (#FFC107)")
3. Line/shape characteristics (stroke width, rounded vs sharp corners, filled vs outline)
4. Shadows, gradients, or texture effects
5. Composition (centered, padding, simplicity level)
6. Background (color, texture, transparent)

Then, output a FINAL LINE starting with "STYLE_PROMPT:" containing a comma-separated \
English style description suitable for an image generation prompt. This line should \
capture ALL the visual characteristics so that an icon generated with this description \
would match the original style. Do NOT include the icon's subject (what it depicts), \
only describe the STYLE.

Example output format:
Overall style: flat design with subtle 3D depth
Color palette: navy blue (#1A237E), white, light gray
Line/shape: bold rounded shapes, no outlines, filled
Shadows/texture: soft drop shadow, subtle gradient on main shape
Composition: centered with generous padding, very simple
Background: solid white

STYLE_PROMPT: flat design with subtle 3D depth, navy blue (#1A237E) and white color scheme, bold rounded filled shapes, soft drop shadow, subtle gradient, centered with generous padding, solid white background, simple and clean, vector-like icon style
"""


def load_image_as_data_url(image_path: str) -> str:
    p = Path(image_path)
    if not p.exists():
        print(f"ERROR: file not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    ext = p.suffix.lower()
    if ext not in SUPPORTED_FORMATS:
        print(f"ERROR: unsupported format '{ext}'. Supported: {', '.join(SUPPORTED_FORMATS)}", file=sys.stderr)
        sys.exit(1)

    size = p.stat().st_size
    if size > MAX_FILE_SIZE:
        print(f"ERROR: file too large ({size/1024/1024:.1f}MB). Max: 10MB.", file=sys.stderr)
        sys.exit(1)

    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    mime = mime_map[ext]

    with open(p, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")

    return f"data:{mime};base64,{b64}"


def is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")


def call_vlm(image_input: str, api_key: str, host: str) -> str:
    url = f"{host.rstrip('/')}{CHAT_ENDPOINT}"

    if is_url(image_input):
        image_content: dict = {"type": "image_url", "image_url": {"url": image_input}}
    else:
        image_content = {"type": "image_url", "image_url": {"url": image_input}}

    payload = {
        "model": "MiniMax-M1",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": ANALYSIS_PROMPT},
                    image_content,
                ],
            }
        ],
        "max_tokens": 600,
        "temperature": 0.3,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    result = resp.json()

    base_resp = result.get("base_resp", {})
    if base_resp.get("status_code", 0) != 0:
        print(f"API ERROR: {base_resp.get('status_msg', 'unknown')}", file=sys.stderr)
        sys.exit(1)

    choices = result.get("choices", [])
    if not choices:
        print("ERROR: no response from model.", file=sys.stderr)
        sys.exit(1)

    return choices[0].get("message", {}).get("content", "")


def extract_style_prompt(text: str) -> str | None:
    for line in text.split("\n"):
        line = line.strip()
        if line.upper().startswith("STYLE_PROMPT:"):
            return line.split(":", 1)[1].strip()
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze an example icon image to extract its visual style description.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
The output STYLE_PROMPT can be passed to generate_icon.py:
  %(prog)s example.png --output-style-only > style.txt
  uv run generate_icon.py --prompt "growth" --custom-style "$(cat style.txt)"

Examples:
  %(prog)s path/to/icon.png
  %(prog)s https://example.com/icon.png
  %(prog)s icon.png --output-style-only
""",
    )
    parser.add_argument("image", help="Path or URL to the example icon image")
    parser.add_argument("--api-key", help="MiniMax API key (or set MINIMAX_API_KEY env)")
    parser.add_argument("--host", help="API host (or set MINIMAX_API_HOST env)")
    parser.add_argument("--output-style-only", action="store_true", help="Only output the extracted STYLE_PROMPT line (for scripting)")

    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("MINIMAX_API_KEY")
    if not api_key:
        print("ERROR: MINIMAX_API_KEY not set. Export it or pass --api-key.", file=sys.stderr)
        sys.exit(1)

    host = args.host or DEFAULT_HOST

    if is_url(args.image):
        image_input: str = args.image
        print(f"Analyzing image from URL: {args.image}")
    else:
        image_input = load_image_as_data_url(args.image)
        print(f"Analyzing image: {args.image}")

    response_text = call_vlm(image_input, api_key, host)

    style_prompt = extract_style_prompt(response_text)

    if args.output_style_only:
        if style_prompt:
            print(style_prompt)
        else:
            print(response_text.strip())
        return

    print("\n" + "=" * 60)
    print("STYLE ANALYSIS")
    print("=" * 60)
    print(response_text)

    if style_prompt:
        print("\n" + "=" * 60)
        print("EXTRACTED STYLE PROMPT (for generate_icon.py --custom-style):")
        print("=" * 60)
        print(style_prompt)
        print()
        print("Usage:")
        print(f'  uv run generate_icon.py --prompt "your subject" --custom-style "{style_prompt}"')


if __name__ == "__main__":
    main()
