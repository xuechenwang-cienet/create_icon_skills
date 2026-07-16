---
name: create-icon
description: Generate professional icons for PPT slides and presentations using MiniMax image-01 multimodal image generation. Use when the user wants to create, design, or generate icons for slides, decks, or presentations. Supports preset styles (flat, line, 3D, gradient, etc.), custom style from example images, batch generation, and transparent background output. Triggers on requests like "generate an icon for my PPT", "create slide icons", "make presentation icons", "design icons for slides".
---

# Create Icon Skill

Generate professional icons for PPT/presentation slides using the MiniMax `image-01` text-to-image model.

## Prerequisites

- **uv** must be installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **MINIMAX_API_KEY** must be available via one of:
  - Shell environment variable (`export MINIMAX_API_KEY=<key>`)
  - A `.env` file in the skill directory (scripts auto-load it as fallback)
  - The `--api-key` flag when running scripts directly
  - Get a key from https://platform.minimaxi.com/user-center/basic-information/interface-key
  - The MiniMax coding-plan key (`sk-cp-...`) also works for image generation
  - Image generation costs ~0.025 CNY per image (very affordable)

Verify the key is set before proceeding:
```bash
echo $MINIMAX_API_KEY | head -c 10  # should show first 10 chars, not empty
```

If the key is not set, check for a `.env` file in the skill directory. If neither exists, ask the user to provide it or set `export MINIMAX_API_KEY=<key>`.

## Available Scripts

All scripts use **PEP 723 inline metadata** and are run via `uv run` with zero manual installation — uv handles dependencies automatically.

| Script | Purpose |
|--------|---------|
| `generate_icon.py` | Main: generate icons via MiniMax image-01 API |
| `analyze_style.py` | Analyze an example icon image to extract its style (uses VLM) |
| `remove_bg.py` | Post-process: remove solid background to make transparent PNG |
| `styles.json` | Preset style templates and common subjects |

## Workflow

### Step 1: Determine the Icon Style

Ask the user which mode they prefer:

**Mode A — Preset Style Selection:**

List the available presets by running:
```bash
uv run generate_icon.py --list-styles
```

Present the styles to the user in a clean table and let them pick one. The presets are:

| Key | Style | Best for |
|-----|-------|----------|
| `flat-color` | Flat Color (扁平彩色) | Modern business PPTs |
| `line-monochrome` | Line Monochrome (线性单色) | Minimalist, easy recolor |
| `line-color` | Line Color (彩色线性) | Professional, modern |
| `3d-render` | 3D Render (3D 立体) | Eye-catching, premium |
| `duotone` | Duotone (双色调) | Stylish, contemporary |
| `filled-color` | Filled Color (填充彩色) | Bold, strong presence |
| `isometric` | Isometric (等距视角) | Technical, approachable |
| `hand-drawn` | Hand Drawn (手绘风格) | Warm, casual |
| `gradient` | Gradient (渐变风格) | SaaS, vibrant |
| `minimal-solid` | Minimal Solid (极简实心) | Maximum clarity, bold |

**Mode B — Learn from Example Image:**

If the user provides an example icon image (file path or URL), analyze its style:
```bash
uv run analyze_style.py path/to/example_icon.png
```

This uses the MiniMax Vision Language Model to extract a detailed style description. The output includes a `STYLE_PROMPT:` line that can be passed to `generate_icon.py --custom-style`.

**Alternative:** If you (the agent) have a built-in image understanding capability (e.g. you are a multimodal model), use it directly to analyze the example icon. Extract: overall style, color palette, line characteristics, effects, composition. Then construct a style description and pass it via `--custom-style`.

### Step 2: Confirm Icon Requirements

Ask the user:
1. **What icon(s)** they need — the subject/semantic meaning (e.g. "growth", "team", "innovation", "rocket", "target"). Use `--list-subjects` for common suggestions:
   ```bash
   uv run generate_icon.py --list-subjects
   ```
2. **How many** variants (1-9, default 1)
3. **Background preference:**
   - Solid white (default, safest for PPT)
   - Transparent PNG (adds post-processing via `remove_bg.py`)
   - Other solid color (specify)

### Step 3: Generate the Icon(s)

**Using a preset style:**
```bash
uv run generate_icon.py \
  --prompt "growth arrow" \
  --style flat-color \
  -n 3 \
  --background white \
  --output ./output
```

**Using a custom style (from example analysis or user description):**
```bash
uv run generate_icon.py \
  --prompt "team collaboration" \
  --custom-style "isometric, pastel colors, soft shadow, rounded shapes" \
  -n 2 \
  --output ./output
```

**Generating transparent PNG icons:**
```bash
uv run generate_icon.py \
  --prompt "innovation lightbulb" \
  --style flat-color \
  --transparent \
  --output ./output
```
The `--transparent` flag automatically runs `remove_bg.py` on each generated image.

**Dry run (preview the prompt without calling the API):**
```bash
uv run generate_icon.py --prompt "growth" --style flat-color --dry-run
```

### Step 4: Review and Iterate

After generation, the script prints the saved file paths. **Review the generated icons** by reading the image files with your vision capability.

If the result is not satisfactory:
- **Wrong style?** Try a different `--style` key or adjust `--custom-style`
- **Too much/little detail?** Add terms like "minimal" or "detailed" to the prompt
- **Wrong colors?** Specify colors explicitly in the prompt, e.g. `--prompt "growth arrow in navy blue and gold"`
- **Background removal issues?** Adjust tolerance: `uv run remove_bg.py icon.png --tolerance 50`

### Step 5: Deliver

Present the generated icon paths to the user. If generating for a PPT, consider:
- The icons are 1024×1024 PNG by default — suitable for most slide layouts
- For transparent PNGs, the `_transparent.png` suffix is added
- Icons can be resized down in the PPT without quality loss (high-res source)

## Important Notes

- **API costs:** 0.025 CNY per image. Generating 9 icons costs ~0.225 CNY. Very affordable but not free.
- **Image format:** The API returns JPEG internally; `generate_icon.py` saves as `.png` (re-encoded). For true transparency, use `--transparent` which runs `remove_bg.py`.
- **No text in icons:** The prompt template includes "no text, no watermark" to prevent the model from adding text to icons.
- **Prompt optimization:** `prompt_optimizer: true` is enabled by default — the API will auto-enhance the prompt.
- **Reproducibility:** Use `--seed <int>` to get consistent results across runs.
- **Rate limits:** If you hit rate limits (status 1002), wait a few seconds and retry.

## Quick Reference

```bash
# List presets
uv run generate_icon.py --list-styles

# List common subjects
uv run generate_icon.py --list-subjects

# Generate 3 flat-color growth icons
uv run generate_icon.py -p "growth arrow" -s flat-color -n 3

# Generate with custom style from example
STYLE=$(uv run analyze_style.py example.png --output-style-only)
uv run generate_icon.py -p "target" --custom-style "$STYLE" -n 2

# Generate transparent background icon
uv run generate_icon.py -p "rocket" -s gradient --transparent

# Remove background from existing image
uv run remove_bg.py output/icon.png --tolerance 40
```
