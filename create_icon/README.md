# Create Icon Skill

Generate professional icons for PPT/presentation slides using the MiniMax `image-01` multimodal image generation model.

## Quick Start

### Prerequisites

1. Install [uv](https://docs.astral.sh/uv/):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Set your MiniMax API key:
   ```bash
   export MINIMAX_API_KEY="your-api-key-here"
   ```
   Get a key from https://platform.minimaxi.com/user-center/basic-information/interface-key

### Generate Your First Icon

```bash
uv run generate_icon.py --prompt "growth arrow" --style flat-color
```

Output is saved to `./output/`.

---

## Deploy as an Opencode Skill

This directory is a self-contained opencode skill. After deployment, the agent auto-discovers it and triggers when you ask for PPT/presentation icon generation.

### Step 1: Install the Skill

**Option A — Global install (available in all projects):**

```bash
cp -r create_icon ~/.config/opencode/skills/create-icon
```

**Option B — Project-level install (available in this project only):**

```bash
mkdir -p .opencode/skills
cp -r create_icon .opencode/skills/create-icon
```

> **Important:** The skill directory name **must** match the `name` field in `SKILL.md`.
> This skill uses `name: create-icon`, so the directory must be `create-icon`.

### Step 2: Configure Environment

The skill scripts need `MINIMAX_API_KEY` to call the MiniMax image generation API. There are three ways to provide it:

#### Method 1: Shell environment variable (recommended)

Add to your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
export MINIMAX_API_KEY="sk-cp-your-key-here"
export MINIMAX_API_HOST="https://api.minimaxi.com"  # optional, has default
```

Then reload: `source ~/.zshrc`

This makes the key available to all scripts run by the agent via bash.

#### Method 2: `.env` file in the skill directory (self-contained)

The scripts auto-load a `.env` file from the skill directory as a fallback:

```bash
cd ~/.config/opencode/skills/create-icon   # or your project .opencode/skills/create-icon
cp .env.example .env
# Edit .env and fill in your real key
```

```env
MINIMAX_API_KEY=sk-cp-your-key-here
MINIMAX_API_HOST=https://api.minimaxi.com
```

> **Security:** The `.gitignore` file already excludes `.env` from version control.

#### Method 3: Both (belt and suspenders)

Set the key in your shell profile **and** create a `.env` file. Shell env takes precedence; the `.env` file is a fallback.

### Step 3: Verify

Start opencode and ask it to generate an icon:

```
> Generate a flat-color "growth arrow" icon for my PPT, make 3 variants with transparent background
```

The agent should:
1. Load the `create-icon` skill automatically
2. Run `uv run generate_icon.py --prompt "growth arrow" --style flat-color -n 3 --transparent`
3. Save icons to `./output/` and report the file paths

### Other Agent Tools (Claude, etc.)

This skill also works with Claude and other agent tools that support the `SKILL.md` convention:

```bash
# Claude-compatible
cp -r create_icon ~/.claude/skills/create-icon

# Generic agent-compatible
cp -r create_icon ~/.agents/skills/create-icon
```

---

## Scripts

All scripts use **PEP 723 inline metadata** — `uv run` handles dependencies automatically, no manual installation needed.

### `generate_icon.py` — Main Icon Generator

Calls the MiniMax `image-01` API to generate icons from text prompts.

```bash
# List available preset styles
uv run generate_icon.py --list-styles

# Generate a single flat-color icon
uv run generate_icon.py --prompt "team collaboration" --style flat-color

# Generate 3 variants of a line icon
uv run generate_icon.py --prompt "innovation" --style line-monochrome -n 3

# Generate with transparent background (auto post-processing)
uv run generate_icon.py --prompt "rocket" --style gradient --transparent

# Generate with custom style description
uv run generate_icon.py --prompt "target" --custom-style "3D isometric, pastel colors, soft shadows"

# Preview the prompt without calling the API
uv run generate_icon.py --prompt "growth" --style flat-color --dry-run

# Use a seed for reproducibility
uv run generate_icon.py --prompt "shield" --style 3d-render --seed 42
```

**Options:**

| Flag | Description |
|------|-------------|
| `--prompt, -p` | Icon subject description (required) |
| `--style, -s` | Preset style key (see `--list-styles`) |
| `--custom-style` | Custom style description (overrides `--style`) |
| `-n` | Number of images (1-9, default 1) |
| `--aspect-ratio` | Aspect ratio (default `1:1` = 1024×1024) |
| `--background` | Background preset: `white`, `light-gray`, `dark`, `transparent-friendly` |
| `--transparent` | Remove background to create transparent PNG |
| `--output, -o` | Output directory (default `./output`) |
| `--name` | Base filename (default: slugified prompt) |
| `--seed` | Random seed for reproducibility |
| `--api-key` | API key (or set `MINIMAX_API_KEY` env) |
| `--dry-run` | Print constructed prompt without calling API |

### `analyze_style.py` — Style Analysis from Example

Uses the MiniMax Vision Language Model to analyze an example icon and extract its style.

```bash
# Analyze a local image file
uv run analyze_style.py path/to/example_icon.png

# Analyze from URL
uv run analyze_style.py https://example.com/icon.png

# Output only the style prompt (for scripting)
uv run analyze_style.py example.png --output-style-only > style.txt

# Use the extracted style to generate matching icons
uv run generate_icon.py -p "growth" --custom-style "$(cat style.txt)"
```

### `remove_bg.py` — Background Removal

Removes a solid background from an icon to create a transparent PNG.

```bash
# Auto-detect background color
uv run remove_bg.py output/icon.png

# Specify output path
uv run remove_bg.py icon.png --output icon_transparent.png

# Adjust tolerance for better results
uv run remove_bg.py icon.png --tolerance 50

# Force specific background color
uv run remove_bg.py icon.png --bg-color "240,240,240"
```

**Options:**

| Flag | Description |
|------|-------------|
| `--output, -o` | Output path (default: `*_transparent.png`) |
| `--tolerance, -t` | Color distance tolerance 0-100 (default 30, higher = more pixels removed) |
| `--feather, -f` | Edge feather radius in pixels (default 1) |
| `--bg-color` | Force background as `R,G,B` (e.g. `255,255,255`) |

---

## Preset Styles

| Key | Name | Description |
|-----|------|-------------|
| `flat-color` | Flat Color | Solid vibrant colors, no gradients/shadows |
| `line-monochrome` | Line Monochrome | Single-color thin lines, minimalist |
| `line-color` | Line Color | Outlined with accent color fills |
| `3d-render` | 3D Render | Soft shadows, depth, glossy |
| `duotone` | Duotone | Two-tone color scheme |
| `filled-color` | Filled Color | Bold solid filled shapes |
| `isometric` | Isometric | 30-degree angle 3D projection |
| `hand-drawn` | Hand Drawn | Organic, sketch-like quality |
| `gradient` | Gradient | Smooth color gradients, vibrant |
| `minimal-solid` | Minimal Solid | High-contrast solid silhouette |

---

## Environment Variables

| Variable | Description | Default | Source |
|----------|-------------|---------|--------|
| `MINIMAX_API_KEY` | MiniMax API key (required) | — | Shell env or `.env` file |
| `MINIMAX_API_HOST` | API host | `https://api.minimaxi.com` | Shell env or `.env` file |

**Precedence:** Shell environment variable > `.env` file > built-in default.

The coding-plan key (`sk-cp-...`) works for image generation. Get a key from:
https://platform.minimaxi.com/user-center/basic-information/interface-key

---

## Pricing

- **0.025 CNY per image** (~0.0035 USD)
- Generating 9 icons costs ~0.225 CNY
- See https://platform.minimaxi.com/docs/guides/pricing-paygo for details

---

## How It Works

1. `generate_icon.py` constructs a prompt from the user's subject + style template
2. Calls `POST https://api.minimaxi.com/v1/image_generation` with model `image-01`
3. Decodes the base64 response and saves as PNG
4. (Optional) `remove_bg.py` post-processes to create transparent background
5. (Optional) `analyze_style.py` uses VLM to learn style from example icons

---

## File Structure

```
create_icon/
├── SKILL.md           # Skill definition for agent integration
├── generate_icon.py   # Main icon generation script (PEP 723)
├── analyze_style.py   # Style analysis from example image (PEP 723)
├── remove_bg.py       # Background removal utility (PEP 723)
├── styles.json        # Preset style templates
├── README.md          # This file
├── .env.example       # Environment variable template
├── .gitignore         # Excludes .env and output/ from version control
└── output/            # Generated icons (auto-created, gitignored)
```
