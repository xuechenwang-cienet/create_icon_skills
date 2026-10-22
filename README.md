> **已归档（2026-10-22）**：`create-icon` / `icon-finder` 已迁入 [`zenanswer/agent-skills`](https://github.com/zenanswer/agent-skills)，改用官方 skills CLI 安装与更新：
>
> ```bash
> npx -y skills@latest add zenanswer/agent-skills -g -s create-icon icon-finder -a opencode claude-code -y
> ```
>
> 本仓库仅作历史留存，不再更新。

# Icon Skills for Presentations

Two complementary opencode skills for getting icons into your PPT slides:

| Skill | What it does | When to use |
|-------|-------------|-------------|
| **[icon-finder](icon-finder/)** | Search and download existing brand/technology logos (AWS, Kubernetes, React, etc.) | You need a specific company/product logo |
| **[create-icon](create_icon/)** | Generate custom icons from text prompts using AI (growth arrow, team, innovation, etc.) | You need a conceptual/custom icon that doesn't exist as a brand logo |

## When to use which?

```
Need an icon for a slide?
│
├── Is it a known brand/product? (AWS, Docker, GitHub, DeepSeek...)
│   └── Use icon-finder → search → download SVG+PNG
│
└── Is it a concept/abstract idea? (growth, team, innovation, security...)
    └── Use create-icon → describe → AI generates PNG
```

## Quick Start

### icon-finder (free, no API key)

```bash
# Install dependencies
python3 -m venv .venv
.venv/bin/pip install -r icon-finder/scripts/requirements.txt

# Search for a logo
.venv/bin/python icon-finder/scripts/search_icons.py "k8s"

# Download as SVG + PNG (transparent background)
.venv/bin/python icon-finder/scripts/fetch_icon.py "iconify:logos:kubernetes" --out ./logos --size 512
```

Sources: Iconify (~1900 colored official logos) + Simple Icons (~3400 monochrome brand icons). Both free, no auth.

### create-icon (requires MiniMax API key)

```bash
# Set API key
export MINIMAX_API_KEY="sk-cp-your-key-here"

# Generate an icon (uv handles deps automatically)
uv run create_icon/generate_icon.py --prompt "growth arrow" --style flat-color -n 3
```

10 preset styles (flat, line, 3D, gradient, isometric, etc.) or learn style from an example image. ~0.025 CNY per image.

See individual READMEs for full details:
- [icon-finder/README.md](icon-finder/README.md)
- [create_icon/README.md](create_icon/README.md)

## Deploy to opencode

Both skills follow the opencode skill convention (a directory with `SKILL.md`). Install them to `~/.config/opencode/skills/skills/`:

```bash
# Option 1: Symlink (recommended - stays in sync with this repo)
ln -s "$(pwd)/icon-finder"  ~/.config/opencode/skills/skills/icon-finder
ln -s "$(pwd)/create_icon"  ~/.config/opencode/skills/skills/create-icon

# Option 2: Copy (standalone, disconnected from repo)
cp -r icon-finder  ~/.config/opencode/skills/skills/icon-finder
cp -r create_icon  ~/.config/opencode/skills/skills/create-icon
```

> **Note:** The skill directory name must match the `name` field in `SKILL.md`.
> - `icon-finder` -> directory `icon-finder`
> - `create-icon` -> directory `create-icon` (note the hyphen, not underscore)

After installing, restart opencode and test:

```
> 帮我找 AWS 和 Kubernetes 的 logo                    ← triggers icon-finder
> 给我的 PPT 生成一个"团队协作"的图标，扁平风格，3个变体    ← triggers create-icon
```

## Project Structure

```
create_icon_skills/
├── README.md              # This file
├── icon-finder/           # Search & download existing brand logos
│   ├── SKILL.md
│   ├── README.md
│   └── scripts/
│       ├── search_icons.py
│       ├── fetch_icon.py
│       └── requirements.txt
└── create_icon/           # Generate custom icons via AI
    ├── SKILL.md
    ├── README.md
    ├── generate_icon.py
    ├── analyze_style.py
    ├── remove_bg.py
    └── styles.json
```

## Proxy

If you're behind a proxy (corporate network, etc.), set environment variables before running scripts:

```bash
export HTTPS_PROXY=http://your-proxy-host:port
export HTTP_PROXY=http://your-proxy-host:port
```

- **icon-finder** reads these directly (all API requests go through the proxy)
- **create-icon** calls the MiniMax API which also respects these env vars
