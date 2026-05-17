#!/usr/bin/env python3
"""Generate a terminal-style animated SVG profile from config."""

import json
import os
import urllib.request
import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "profile-config.yml")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "terminal.svg")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

COLORS = {
    "bg": "#0a0a0a",
    "fg": "#b5e853",
    "dim": "#4a7c59",
    "prompt": "#7ee787",
    "cmd": "#e6edf3",
    "link": "#58a6ff",
    "red": "#ff4444",
    "yellow": "#ffd700",
    "white": "#c9d1d9",
    "grey": "#484f58",
    "bar_bg": "#1a1a1a",
    "bar_dot_red": "#ff5f56",
    "bar_dot_yellow": "#ffbd2e",
    "bar_dot_green": "#27c93f",
}

FONT = "ui-monospace, 'Cascadia Code', 'SF Mono', 'Fira Code', Consolas, monospace"
LINE_HEIGHT = 22
FONT_SIZE = 13
CHAR_WIDTH = 7.8
PADDING_X = 20
PADDING_Y = 16
TITLE_BAR_H = 36
WIDTH = 800


def fetch_stars(repo: str) -> int:
    if not GITHUB_TOKEN:
        return 0
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}",
            headers={
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return data.get("stargazers_count", 0)
    except Exception:
        return 0


def escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(config: dict) -> str:
    lines: list[dict] = []
    delays: list[float] = []
    current_delay = 0.5

    def add_line(parts: list[tuple[str, str]], delay_add: float = 0.08):
        nonlocal current_delay
        lines.append({"parts": parts, "delay": current_delay})
        current_delay += delay_add

    def add_blank(delay_add: float = 0.04):
        nonlocal current_delay
        lines.append({"parts": [("", COLORS["fg"])], "delay": current_delay})
        current_delay += delay_add

    add_line([
        ("$ ", COLORS["prompt"]),
        ("whoami", COLORS["cmd"]),
    ], 0.3)

    add_line([
        (config["name"], COLORS["white"]),
    ], 0.15)

    add_line([
        (config["tagline"], COLORS["dim"]),
    ], 0.15)

    add_line([
        (config["role"], COLORS["grey"]),
    ], 0.2)

    add_blank()

    add_line([
        ("$ ", COLORS["prompt"]),
        ("cat links.txt", COLORS["cmd"]),
    ], 0.3)

    link_parts = []
    for i, (key, url) in enumerate(config["links"].items()):
        if i > 0:
            link_parts.append((" | ", COLORS["grey"]))
        link_parts.append((key, COLORS["link"]))
    add_line(link_parts, 0.3)

    add_blank()

    # shipped
    add_line([
        ("$ ", COLORS["prompt"]),
        ("ls shipped/", COLORS["cmd"]),
    ], 0.3)

    for proj in config["shipped"]:
        stars = fetch_stars(proj["repo"])
        star_str = f"★ {stars}" if stars > 0 else ""
        name_padded = proj["name"].ljust(18)
        parts = [
            ("  ", COLORS["fg"]),
            (name_padded, COLORS["white"]),
            (proj["desc"], COLORS["dim"]),
        ]
        if star_str:
            parts.append(("__STAR__" + star_str, COLORS["yellow"]))
        add_line(parts)

    add_blank()

    # building
    add_line([
        ("$ ", COLORS["prompt"]),
        ("ls building/", COLORS["cmd"]),
    ], 0.3)

    for proj in config["building"]:
        name_padded = proj["name"].ljust(18)
        add_line([
            ("  ", COLORS["fg"]),
            (name_padded, COLORS["white"]),
            (proj["desc"], COLORS["dim"]),
        ])

    add_blank()

    # upstream
    add_line([
        ("$ ", COLORS["prompt"]),
        ("git log --oneline upstream/", COLORS["cmd"]),
    ], 0.3)

    upstream_parts = [("  merged -> ", COLORS["dim"])]
    for i, up in enumerate(config["upstream"]):
        if i > 0:
            upstream_parts.append((" · ", COLORS["grey"]))
        upstream_parts.append((up["name"], COLORS["link"]))
    add_line(upstream_parts, 0.3)

    add_blank()

    # cursor line
    add_line([
        ("$ ", COLORS["prompt"]),
        ("█", COLORS["fg"]),
    ], 0.0)

    total_lines = len(lines)
    content_h = total_lines * LINE_HEIGHT + PADDING_Y * 2
    total_h = TITLE_BAR_H + content_h
    total_anim_time = current_delay + 0.5

    # scanline overlay
    scanline_h = total_h

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{total_h}" viewBox="0 0 {WIDTH} {total_h}">',
        "<defs>",
        f'  <pattern id="scanlines" width="4" height="4" patternUnits="userSpaceOnUse">',
        f'    <rect width="4" height="2" fill="{COLORS["bg"]}"/>',
        f'    <rect y="2" width="4" height="2" fill="rgba(255,255,255,0.015)"/>',
        "  </pattern>",
        "</defs>",
        "<style>",
        f"  text {{ font-family: {FONT}; font-size: {FONT_SIZE}px; }}",
        "  .line { opacity: 0; animation: appear 0.01s forwards; }",
        f"  @keyframes appear {{ to {{ opacity: 1; }} }}",
        f"  @keyframes blink {{ 0%,50% {{ opacity:1 }} 51%,100% {{ opacity:0 }} }}",
        "  .cursor { animation: blink 1s step-end infinite; }",
        "</style>",

        # background
        f'<rect width="{WIDTH}" height="{total_h}" rx="8" fill="{COLORS["bg"]}"/>',

        # title bar
        f'<rect width="{WIDTH}" height="{TITLE_BAR_H}" rx="8" fill="{COLORS["bar_bg"]}"/>',
        f'<rect y="{TITLE_BAR_H - 8}" width="{WIDTH}" height="8" fill="{COLORS["bar_bg"]}"/>',
        f'<circle cx="16" cy="18" r="6" fill="{COLORS["bar_dot_red"]}"/>',
        f'<circle cx="34" cy="18" r="6" fill="{COLORS["bar_dot_yellow"]}"/>',
        f'<circle cx="52" cy="18" r="6" fill="{COLORS["bar_dot_green"]}"/>',
        f'<text x="{WIDTH // 2}" y="22" text-anchor="middle" fill="{COLORS["grey"]}" font-size="12">chiruu12 — zsh</text>',

        '<g>',
    ]

    for i, line_data in enumerate(lines):
        y = TITLE_BAR_H + PADDING_Y + (i + 1) * LINE_HEIGHT
        delay = line_data["delay"]

        is_cursor_line = i == total_lines - 1
        cursor_class = ' class="cursor"' if is_cursor_line else ""

        svg_parts.append(
            f'  <g class="line" style="animation-delay: {delay:.2f}s">'
        )

        x = PADDING_X
        for text, color in line_data["parts"]:
            if not text:
                continue
            if text.startswith("__STAR__"):
                star_text = text[8:]
                escaped = escape(star_text)
                svg_parts.append(
                    f'    <text x="{WIDTH - PADDING_X}" y="{y}" fill="{color}" text-anchor="end">{escaped}</text>'
                )
            else:
                escaped = escape(text)
                svg_parts.append(
                    f'    <text x="{x}" y="{y}" fill="{color}"{cursor_class}>{escaped}</text>'
                )
                x += len(text) * CHAR_WIDTH

        svg_parts.append("  </g>")

    svg_parts.extend([
        "</g>",
        # scanline overlay (subtle)
        f'<rect width="{WIDTH}" height="{total_h}" rx="8" fill="url(#scanlines)" opacity="0.2"/>',
        "</svg>",
    ])

    return "\n".join(svg_parts)


def main():
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    svg = build_svg(config)

    with open(OUTPUT_PATH, "w") as f:
        f.write(svg)

    print(f"Generated {OUTPUT_PATH} ({len(svg)} bytes, {len(svg.splitlines())} lines)")


if __name__ == "__main__":
    main()
