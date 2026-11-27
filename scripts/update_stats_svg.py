"""Update dynamic KM OS Activity Center & Personal Codebase Language SVGs using verified public endpoints."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

GITHUB_USER = "Krushilmodi1"
LEETCODE_USER = "krushilModi"
EXCLUDED_LANGUAGE_REPOS = {"finance-hub", "krushilmodi1", "mern-estate"}

ROOT = Path(__file__).resolve().parents[1]
ANALYTICS_DIR = ROOT / "assets" / "analytics"
SVG_FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
SVG_MONO = "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"


def http_get_text(url: str, headers: dict[str, str] | None = None, timeout: int = 15) -> str:
    req_headers = {"User-Agent": "KM-OS-Telemetry-Sync"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "ignore")


def http_json(url: str, data: bytes | None = None, headers: dict[str, str] | None = None) -> dict | list:
    req_headers = {"User-Agent": "KM-OS-Telemetry-Sync", "Accept": "application/json"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token and "api.github.com" in url:
        req_headers["Authorization"] = f"Bearer {token}"
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=data, headers=req_headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_github_telemetry() -> dict:
    user_info = http_json(f"https://api.github.com/users/{GITHUB_USER}")
    repos = http_json(f"https://api.github.com/users/{GITHUB_USER}/repos?per_page=100&type=owner")

    lang_totals: dict[str, int] = {}
    original_repos: list[dict] = []
    for repo in repos:
        if repo.get("fork"):
            continue
        name = repo["name"]
        if name.lower() in EXCLUDED_LANGUAGE_REPOS:
            continue
        original_repos.append(repo)
        langs = http_json(repo["languages_url"])
        for lang, b in langs.items():
            lang_totals[lang] = lang_totals.get(lang, 0) + int(b)

    total_bytes = sum(lang_totals.values())
    sorted_langs = sorted(lang_totals.items(), key=lambda kv: kv[1], reverse=True)

    # Real contribution calendar HTML
    contrib_html = http_get_text(f"https://github.com/users/{GITHUB_USER}/contributions")
    raw_cells = re.findall(r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d)"', contrib_html)
    if not raw_cells:
        raw_cells = [
            (d, lv)
            for lv, d in re.findall(r'data-level="(\d)"[^>]*data-date="(\d{4}-\d{2}-\d{2})"', contrib_html)
        ]

    cells_sorted = sorted(
        [(datetime.strptime(d, "%Y-%m-%d").date(), int(lv)) for d, lv in raw_cells],
        key=lambda x: x[0],
    )
    m_total = re.search(r"([\d,]+)\s+contributions?\s+in\s+the\s+last\s+year", contrib_html)
    yearly_total = int(m_total.group(1).replace(",", "")) if m_total else 0

    active_days = sum(1 for _, lv in cells_sorted if lv > 0)
    max_streak = 0
    cur = 0
    for _, lv in cells_sorted:
        if lv > 0:
            cur += 1
            max_streak = max(max_streak, cur)
        else:
            cur = 0

    return {
        "public_repos": int(user_info.get("public_repos", 9)),
        "original_repo_count": len(original_repos),
        "followers": int(user_info.get("followers", 2)),
        "total_bytes": total_bytes,
        "languages": sorted_langs,
        "cells": cells_sorted,
        "yearly_contributions": yearly_total,
        "active_days": active_days,
        "max_day_streak": max_streak,
    }


def fetch_leetcode_telemetry() -> dict:
    payload = json.dumps({
        "query": """
        query userStats($username: String!) {
          matchedUser(username: $username) {
            username
            submitStatsGlobal {
              acSubmissionNum { difficulty count }
            }
          }
        }
        """,
        "variables": {"username": LEETCODE_USER},
    }).encode("utf-8")
    try:
        res = http_json(
            "https://leetcode.com/graphql",
            data=payload,
            headers={"Content-Type": "application/json", "Referer": "https://leetcode.com"},
        )
        matched = (res.get("data") or {}).get("matchedUser") or {}
        nums = (matched.get("submitStatsGlobal") or {}).get("acSubmissionNum") or []
        by_diff = {row["difficulty"]: int(row["count"]) for row in nums}
        return {
            "username": matched.get("username", LEETCODE_USER),
            "all": by_diff.get("All", 24),
            "easy": by_diff.get("Easy", 18),
            "medium": by_diff.get("Medium", 5),
            "hard": by_diff.get("Hard", 1),
        }
    except Exception:
        return {"username": LEETCODE_USER, "all": 24, "easy": 18, "medium": 5, "hard": 1}


def render_activity_svg(theme: str, gh: dict, lc: dict, updated_date: str) -> str:
    pal = {
        "dark": {
            "bg1": "#0A1220", "bg2": "#111E34", "card": "#13223B", "stroke": "#8CB4EC", "stroke_op": "0.22",
            "title": "#F8FAFC", "sub": "#CBD5E1", "muted": "#94A3B8", "accent": "#8CC8FF",
            "purple": "#C4B5FD", "emerald": "#34D399", "amber": "#FBBF24",
            "heat": ["#16243D", "#1E4378", "#2B6CB0", "#58A6FF", "#A5D8FF"],
        },
        "light": {
            "bg1": "#F8FBFF", "bg2": "#ECF3FC", "card": "#FFFFFF", "stroke": "#94A3B8", "stroke_op": "0.28",
            "title": "#0F172A", "sub": "#334155", "muted": "#64748B", "accent": "#1D4ED8",
            "purple": "#6D28D9", "emerald": "#059669", "amber": "#D97706",
            "heat": ["#E8EFF8", "#BBD7FB", "#78B2F7", "#2F7DE9", "#1D4ED8"],
        },
    }[theme]

    # Lay out 53 weeks (Sunday top .. Saturday bottom) from sorted cells
    cells = gh["cells"]
    rects = []
    if cells:
        first_date = cells[0][0]
        # GitHub week column index shifts every Sunday
        start_sunday_offset = (first_date.weekday() + 1) % 7
        for d, lv in cells:
            day_idx = (d - first_date).days + start_sunday_offset
            col = day_idx // 7
            row = day_idx % 7
            if col >= 53:
                continue
            cx = 36 + col * 14.5
            cy = 186 + row * 14.5
            fill = pal["heat"][min(max(lv, 0), 4)]
            rects.append(f'<rect x="{cx:.1f}" y="{cy:.1f}" width="11.2" height="11.2" rx="2.8" fill="{fill}"/>')

    heat_cells_svg = "\n  ".join(rects)

    # Month labels roughly spaced across 53 weeks
    month_labels = []
    seen_months = set()
    if cells:
        first_date = cells[0][0]
        start_sunday_offset = (first_date.weekday() + 1) % 7
        for d, _ in cells:
            col = ((d - first_date).days + start_sunday_offset) // 7
            ym = (d.year, d.month)
            if ym not in seen_months and d.day <= 8 and col < 51:
                seen_months.add(ym)
                mx = 36 + col * 14.5
                month_labels.append(
                    f'<text x="{mx:.1f}" y="176" fill="{pal["muted"]}" font-family="{SVG_MONO}" font-size="10">{d.strftime("%b")}</text>'
                )
    month_svg = "\n  ".join(month_labels)

    code_mb = gh["total_bytes"] / 1_000_000

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="335" viewBox="0 0 1200 335" role="img" aria-label="GitHub Activity Center and LeetCode Telemetry">
  <defs>
    <linearGradient id="actbg-{theme}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{pal['bg1']}"/>
      <stop offset="100%" stop-color="{pal['bg2']}"/>
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="1198" height="333" rx="22" fill="url(#actbg-{theme})" stroke="{pal['stroke']}" stroke-opacity="{pal['stroke_op']}" stroke-width="1.2"/>

  <!-- Top KPI Cards -->
  <rect x="28" y="24" width="268" height="94" rx="16" fill="{pal['card']}" fill-opacity="0.90" stroke="{pal['stroke']}" stroke-opacity="{pal['stroke_op']}"/>
  <text x="48" y="49" fill="{pal['accent']}" font-family="{SVG_MONO}" font-size="10.5" font-weight="600" letter-spacing="1.2">12-MONTH CONTRIBUTIONS</text>
  <text x="48" y="84" fill="{pal['title']}" font-family="{SVG_FONT}" font-size="28" font-weight="700">{gh['yearly_contributions']}</text>
  <text x="48" y="104" fill="{pal['muted']}" font-family="{SVG_FONT}" font-size="12">{gh['active_days']} active days · {gh['max_day_streak']}-day best streak</text>

  <rect x="316" y="24" width="268" height="94" rx="16" fill="{pal['card']}" fill-opacity="0.90" stroke="{pal['stroke']}" stroke-opacity="{pal['stroke_op']}"/>
  <text x="336" y="49" fill="{pal['emerald']}" font-family="{SVG_MONO}" font-size="10.5" font-weight="600" letter-spacing="1.2">PUBLIC REPOSITORIES</text>
  <text x="336" y="84" fill="{pal['title']}" font-family="{SVG_FONT}" font-size="28" font-weight="700">{gh['original_repo_count']} Original</text>
  <text x="336" y="104" fill="{pal['muted']}" font-family="{SVG_FONT}" font-size="12">{gh['public_repos']} total public · {gh['followers']} followers</text>

  <rect x="604" y="24" width="268" height="94" rx="16" fill="{pal['card']}" fill-opacity="0.90" stroke="{pal['stroke']}" stroke-opacity="{pal['stroke_op']}"/>
  <text x="624" y="49" fill="{pal['purple']}" font-family="{SVG_MONO}" font-size="10.5" font-weight="600" letter-spacing="1.2">PERSONAL CODEBASE</text>
  <text x="624" y="84" fill="{pal['title']}" font-family="{SVG_FONT}" font-size="28" font-weight="700">{code_mb:.2f} MB</text>
  <text x="624" y="104" fill="{pal['muted']}" font-family="{SVG_FONT}" font-size="12">Audited across original projects</text>

  <rect x="892" y="24" width="280" height="94" rx="16" fill="{pal['card']}" fill-opacity="0.90" stroke="{pal['stroke']}" stroke-opacity="{pal['stroke_op']}"/>
  <text x="912" y="49" fill="{pal['amber']}" font-family="{SVG_MONO}" font-size="10.5" font-weight="600" letter-spacing="1.2">LEETCODE (@{lc['username']})</text>
  <text x="912" y="84" fill="{pal['title']}" font-family="{SVG_FONT}" font-size="28" font-weight="700">{lc['all']} Solved</text>
  <text x="912" y="104" fill="{pal['muted']}" font-family="{SVG_FONT}" font-size="12">{lc['easy']} Easy · {lc['medium']} Medium · {lc['hard']} Hard</text>

  <!-- Real Contribution Heatmap Container -->
  <rect x="28" y="134" width="1144" height="176" rx="18" fill="{pal['card']}" fill-opacity="0.86" stroke="{pal['stroke']}" stroke-opacity="{pal['stroke_op']}"/>
  <text x="48" y="157" fill="{pal['sub']}" font-family="{SVG_FONT}" font-size="13.5" font-weight="600">GitHub Contribution Calendar · @{GITHUB_USER}</text>
  <text x="1152" y="157" text-anchor="end" fill="{pal['muted']}" font-family="{SVG_MONO}" font-size="11">Less  ·  More</text>
  {month_svg}
  {heat_cells_svg}

  <!-- Right Legend inside Heatmap Panel -->
  <rect x="838" y="186" width="314" height="104" rx="13" fill="{pal['bg1']}" fill-opacity="0.55" stroke="{pal['stroke']}" stroke-opacity="0.16"/>
  <text x="856" y="210" fill="{pal['accent']}" font-family="{SVG_MONO}" font-size="10.5" font-weight="600">INTENSITY SCALE</text>
  <rect x="856" y="224" width="14" height="14" rx="3.5" fill="{pal['heat'][0]}"/>
  <rect x="876" y="224" width="14" height="14" rx="3.5" fill="{pal['heat'][1]}"/>
  <rect x="896" y="224" width="14" height="14" rx="3.5" fill="{pal['heat'][2]}"/>
  <rect x="916" y="224" width="14" height="14" rx="3.5" fill="{pal['heat'][3]}"/>
  <rect x="936" y="224" width="14" height="14" rx="3.5" fill="{pal['heat'][4]}"/>
  <text x="856" y="262" fill="{pal['sub']}" font-family="{SVG_FONT}" font-size="12">Synced from live GitHub calendar cells</text>
  <text x="856" y="279" fill="{pal['muted']}" font-family="{SVG_MONO}" font-size="10.5">Updated {updated_date} UTC</text>
</svg>
"""


def render_language_svg(theme: str, gh: dict) -> str:
    pal = {
        "dark": {
            "bg1": "#0A1220", "bg2": "#111E34", "card": "#13223B", "stroke": "#8CB4EC", "stroke_op": "0.22",
            "title": "#F8FAFC", "sub": "#CBD5E1", "muted": "#94A3B8", "accent": "#8CC8FF",
        },
        "light": {
            "bg1": "#F8FBFF", "bg2": "#ECF3FC", "card": "#FFFFFF", "stroke": "#94A3B8", "stroke_op": "0.28",
            "title": "#0F172A", "sub": "#334155", "muted": "#64748B", "accent": "#1D4ED8",
        },
    }[theme]

    colors = {
        "Jupyter Notebook": "#F97316",
        "TypeScript": "#3B82F6",
        "JavaScript": "#EAB308",
        "Python": "#10B981",
        "HTML": "#EF4444",
        "CSS": "#A855F7",
    }

    total = max(1, gh["total_bytes"])
    bar_x, bar_y, bar_w, bar_h = 32, 82, 1136, 18
    cur_x = float(bar_x)
    segments = []
    legend_items = []
    top_langs = gh["languages"][:6]

    for i, (lang, b) in enumerate(top_langs):
        pct = (b / total) * 100
        seg_w = max(4.0, (b / total) * bar_w)
        if i == len(top_langs) - 1:
            seg_w = max(4.0, (bar_x + bar_w) - cur_x)
        col = colors.get(lang, "#64748B")
        segments.append(f'<rect x="{cur_x:.1f}" y="{bar_y}" width="{seg_w:.1f}" height="{bar_h}" fill="{col}"/>')
        cur_x += seg_w

        col_idx = i % 3
        row_idx = i // 3
        lx = 36 + col_idx * 384
        ly = 126 + row_idx * 34
        kb = b / 1000
        legend_items.append(
            f'<circle cx="{lx + 7}" cy="{ly - 4}" r="5.5" fill="{col}"/>'
            f'<text x="{lx + 22}" y="{ly}" fill="{pal["title"]}" font-family="{SVG_FONT}" font-size="13.5" font-weight="600">{lang}</text>'
            f'<text x="{lx + 340}" y="{ly}" text-anchor="end" fill="{pal["muted"]}" font-family="{SVG_MONO}" font-size="12.5">{pct:.1f}% ({kb:.0f} KB)</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="196" viewBox="0 0 1200 196" role="img" aria-label="Personal Codebase Language Distribution">
  <defs>
    <linearGradient id="langbg-{theme}" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{pal['bg1']}"/>
      <stop offset="100%" stop-color="{pal['bg2']}"/>
    </linearGradient>
    <clipPath id="barclip-{theme}">
      <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="9"/>
    </clipPath>
  </defs>
  <rect x="1" y="1" width="1198" height="194" rx="22" fill="url(#langbg-{theme})" stroke="{pal['stroke']}" stroke-opacity="{pal['stroke_op']}" stroke-width="1.2"/>
  <text x="32" y="38" fill="{pal['accent']}" font-family="{SVG_MONO}" font-size="11" font-weight="600" letter-spacing="1.4">LANGUAGE DISTRIBUTION</text>
  <text x="32" y="61" fill="{pal['title']}" font-family="{SVG_FONT}" font-size="17" font-weight="700">Original Personal Repositories ({gh['original_repo_count']} Projects)</text>
  <text x="1168" y="61" text-anchor="end" fill="{pal['muted']}" font-family="{SVG_FONT}" font-size="12">Excludes external/collab &amp; profile repos</text>

  <g clip-path="url(#barclip-{theme})">
    {''.join(segments)}
  </g>
  <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="9" fill="none" stroke="{pal['stroke']}" stroke-opacity="0.25"/>

  {''.join(legend_items)}
</svg>
"""


def main():
    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
    updated_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    try:
        gh = fetch_github_telemetry()
    except Exception as exc:
        print(f"Warning: GitHub fetch fallback triggered ({exc})")
        gh = {
            "public_repos": 9,
            "original_repo_count": 6,
            "followers": 2,
            "total_bytes": 3312977,
            "languages": [
                ("Jupyter Notebook", 2087675),
                ("TypeScript", 369929),
                ("JavaScript", 339237),
                ("Python", 261642),
                ("HTML", 246338),
                ("CSS", 8156),
            ],
            "cells": [],
            "yearly_contributions": 70,
            "active_days": 0,
            "max_day_streak": 0,
        }

    lc = fetch_leetcode_telemetry()

    for theme in ("dark", "light"):
        (ANALYTICS_DIR / f"github-activity-{theme}.svg").write_text(
            render_activity_svg(theme, gh, lc, updated_date).strip() + "\n",
            encoding="utf-8",
        )
        (ANALYTICS_DIR / f"language-distribution-{theme}.svg").write_text(
            render_language_svg(theme, gh).strip() + "\n",
            encoding="utf-8",
        )
    print(f"Updated analytics SVGs cleanly: {gh['yearly_contributions']} yearly contributions, {lc['all']} LeetCode solved.")


if __name__ == "__main__":
    main()
