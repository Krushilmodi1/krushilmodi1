#!/usr/bin/env python3
"""
Generate dark & light Liquid Glass SVG analytics cards for Krushil Modi's
GitHub Profile README using verified public GitHub & LeetCode API data.

Note: Explicitly excludes friend/external repositories (e.g., Finance-hub)
from personal repository language byte distribution.
"""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

GITHUB_USER = "Krushilmodi1"
LEETCODE_USER = "krushilModi"
EXCLUDED_REPOS = {"Finance-hub", "krushilmodi1", "mern-estate"}

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "assets" / "analytics"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def fetch_json(url: str, method: str = "GET", body: bytes | None = None, extra_headers: dict[str, str] | None = None) -> dict | list:
    headers = {"User-Agent": "KrushilProfileStatsGenerator/1.0"}
    token = os.environ.get("GITHUB_TOKEN")
    if token and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {token}"
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_theme(mode: str) -> dict[str, str]:
    if mode == "dark":
        return {
            "bg": "#0B1322",
            "card": "#142137",
            "border": "#78D4FF",
            "border_op": "0.24",
            "track": "#1C2D47",
            "text": "#EDF4FF",
            "muted": "#9CAECA",
            "accent1": "#78D4FF",
            "accent2": "#A99BFF",
            "bar_colors": ["#78D4FF", "#A99BFF", "#38BDF8", "#60A5FA", "#34D399", "#94A3B8"],
        }
    return {
        "bg": "#FFFFFF",
        "card": "#F5F8FC",
        "border": "#2563EB",
        "border_op": "0.22",
        "track": "#E1E8F4",
        "text": "#17243A",
        "muted": "#52627A",
        "accent1": "#2563EB",
        "accent2": "#6554C0",
        "bar_colors": ["#2563EB", "#6554C0", "#0284C7", "#0EA5E9", "#059669", "#64748B"],
    }


def render_overview_svg(mode: str, stats: dict) -> str:
    t = get_theme(mode)
    return f'''<svg width="680" height="260" viewBox="0 0 680 260" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="GitHub and LeetCode verified activity overview">
  <rect x="2" y="2" width="676" height="256" rx="22" fill="{t['bg']}" stroke="{t['border']}" stroke-opacity="{t['border_op']}" stroke-width="1.4"/>
  <text x="28" y="38" fill="{t['accent1']}" font-family="'Inter', sans-serif" font-size="11" font-weight="700" letter-spacing="1">VERIFIED PROFILE TELEMETRY</text>
  <text x="28" y="62" fill="{t['text']}" font-family="'Plus Jakarta Sans', 'Inter', sans-serif" font-size="19" font-weight="700">GitHub (@{GITHUB_USER}) &amp; LeetCode (@{LEETCODE_USER})</text>

  <!-- 3 GitHub Stat Tiles -->
  <rect x="28" y="84" width="196" height="74" rx="14" fill="{t['card']}" stroke="{t['border']}" stroke-opacity="0.16"/>
  <text x="44" y="114" fill="{t['accent1']}" font-family="'Plus Jakarta Sans', sans-serif" font-size="24" font-weight="800">{stats['personal_repos']} / {stats['public_repos']}</text>
  <text x="44" y="138" fill="{t['muted']}" font-family="'Inter', sans-serif" font-size="11.5">Personal Code / Public Repos</text>

  <rect x="242" y="84" width="196" height="74" rx="14" fill="{t['card']}" stroke="{t['border']}" stroke-opacity="0.16"/>
  <text x="258" y="114" fill="{t['accent2']}" font-family="'Plus Jakarta Sans', sans-serif" font-size="24" font-weight="800">{stats['followers']} / {stats['following']}</text>
  <text x="258" y="138" fill="{t['muted']}" font-family="'Inter', sans-serif" font-size="11.5">Followers / Following</text>

  <rect x="456" y="84" width="196" height="74" rx="14" fill="{t['card']}" stroke="{t['border']}" stroke-opacity="0.16"/>
  <text x="472" y="114" fill="{t['accent1']}" font-family="'Plus Jakarta Sans', sans-serif" font-size="24" font-weight="800">{stats['stars']}</text>
  <text x="472" y="138" fill="{t['muted']}" font-family="'Inter', sans-serif" font-size="11.5">Total Stars (Public Repos)</text>

  <!-- LeetCode Verified Strip -->
  <rect x="28" y="174" width="624" height="62" rx="14" fill="{t['card']}" stroke="{t['border']}" stroke-opacity="0.16"/>
  <text x="44" y="200" fill="{t['text']}" font-family="'Inter', sans-serif" font-size="13" font-weight="700">LeetCode Problem Solving (@{LEETCODE_USER})</text>
  <text x="44" y="220" fill="{t['muted']}" font-family="'Inter', sans-serif" font-size="12">Total Solved: {stats['lc_all']}  &#183;  Easy: {stats['lc_easy']}  &#183;  Medium: {stats['lc_medium']}  &#183;  Hard: {stats['lc_hard']}</text>
</svg>
'''


def render_languages_svg(mode: str, lang_rows: list[tuple[str, int, float]]) -> str:
    t = get_theme(mode)
    # Build stacked horizontal bar
    bar_x = 28
    bar_w = 624
    stacked = []
    cur_x = float(bar_x)
    for idx, (name, _b, pct) in enumerate(lang_rows[:6]):
        seg_w = max(4.0, (pct / 100.0) * bar_w)
        col = t["bar_colors"][idx % len(t["bar_colors"])]
        stacked.append(f'<rect x="{cur_x:.1f}" y="86" width="{seg_w:.1f}" height="14" rx="4" fill="{col}"/>')
        cur_x += seg_w

    rows_svg = []
    for idx, (name, _b, pct) in enumerate(lang_rows[:6]):
        col = t["bar_colors"][idx % len(t["bar_colors"])]
        col_x = 28 if idx < 3 else 356
        row_y = 132 + (idx % 3) * 34
        rows_svg.append(
            f'<circle cx="{col_x + 6}" cy="{row_y - 4}" r="5" fill="{col}"/>'
            f'<text x="{col_x + 20}" y="{row_y}" fill="{t["text"]}" font-family="\'Inter\', sans-serif" font-size="13" font-weight="600">{name}</text>'
            f'<text x="{col_x + 276}" y="{row_y}" text-anchor="end" fill="{t["muted"]}" font-family="\'Inter\', sans-serif" font-size="12.5">{pct:.1f}%</text>'
        )

    return f'''<svg width="680" height="260" viewBox="0 0 680 260" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Personal repository language distribution by byte share">
  <rect x="2" y="2" width="676" height="256" rx="22" fill="{t['bg']}" stroke="{t['border']}" stroke-opacity="{t['border_op']}" stroke-width="1.4"/>
  <text x="28" y="38" fill="{t['accent2']}" font-family="'Inter', sans-serif" font-size="11" font-weight="700" letter-spacing="1">REPOSITORY LANGUAGE DISTRIBUTION</text>
  <text x="28" y="62" fill="{t['text']}" font-family="'Plus Jakarta Sans', 'Inter', sans-serif" font-size="18.5" font-weight="700">Personal Public Codebases (Byte Share)</text>

  <rect x="{bar_x}" y="86" width="{bar_w}" height="14" rx="7" fill="{t['track']}"/>
  {''.join(stacked)}
  {''.join(rows_svg)}

  <text x="28" y="238" fill="{t['muted']}" font-family="'Inter', sans-serif" font-size="11">Measured across Krushil&apos;s own code repositories via GitHub REST API (excludes forks &amp; friend repos).</text>
</svg>
'''


def main() -> None:
    user = fetch_json(f"https://api.github.com/users/{GITHUB_USER}")
    repos = fetch_json(f"https://api.github.com/users/{GITHUB_USER}/repos?per_page=100")

    stars = sum(int(r.get("stargazers_count", 0)) for r in repos if isinstance(repos, list))
    personal = [r for r in repos if not r.get("fork") and r.get("name") not in EXCLUDED_REPOS]

    lang_totals: dict[str, int] = {}
    for r in personal:
        langs = fetch_json(f"https://api.github.com/repos/{GITHUB_USER}/{r['name']}/languages")
        if isinstance(langs, dict):
            for k, v in langs.items():
                lang_totals[k] = lang_totals.get(k, 0) + int(v)

    total_bytes = max(1, sum(lang_totals.values()))
    lang_rows = sorted(
        [(k, v, round((v / total_bytes) * 100, 1)) for k, v in lang_totals.items()],
        key=lambda x: x[1],
        reverse=True,
    )

    lc_all = lc_easy = lc_med = lc_hard = 0
    try:
        lc_payload = json.dumps({
            "query": f'query {{ matchedUser(username: "{LEETCODE_USER}") {{ submitStats {{ acSubmissionNum {{ difficulty count }} }} }} }}'
        }).encode("utf-8")
        lc = fetch_json("https://leetcode.com/graphql", method="POST", body=lc_payload, extra_headers={"Content-Type": "application/json"})
        counts = {item["difficulty"]: int(item["count"]) for item in lc["data"]["matchedUser"]["submitStats"]["acSubmissionNum"]}
        lc_all = counts.get("All", 0)
        lc_easy = counts.get("Easy", 0)
        lc_med = counts.get("Medium", 0)
        lc_hard = counts.get("Hard", 0)
    except Exception:
        pass

    stats = {
        "public_repos": int(user.get("public_repos", 0)),
        "personal_repos": len(personal),
        "followers": int(user.get("followers", 0)),
        "following": int(user.get("following", 0)),
        "stars": stars,
        "lc_all": lc_all,
        "lc_easy": lc_easy,
        "lc_medium": lc_med,
        "lc_hard": lc_hard,
    }

    for mode in ("dark", "light"):
        (OUT_DIR / f"github-overview-{mode}.svg").write_text(render_overview_svg(mode, stats), encoding="utf-8")
        (OUT_DIR / f"language-distribution-{mode}.svg").write_text(render_languages_svg(mode, lang_rows), encoding="utf-8")

    print("Generated analytics SVGs cleanly:", stats)
    print("Languages:", lang_rows)


if __name__ == "__main__":
    main()
