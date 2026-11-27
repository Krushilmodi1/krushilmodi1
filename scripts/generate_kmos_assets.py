"""Generate KM OS dual-theme atmospheric Liquid Glass hero, footer, module headers, and academic architecture assets."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
HERO_DIR = ASSETS / "hero"
MOD_DIR = ASSETS / "modules"
EDU_DIR = ASSETS / "education"

WALLPAPERS = {
    "dark": Path(r"C:\Users\Aryan\.gemini\antigravity\brain\38c9bc11-0f09-4f4d-85f0-72df4684ac07\kmos_midnight_atmosphere_1795813762838.jpg"),
    "light": Path(r"C:\Users\Aryan\.gemini\antigravity\brain\38c9bc11-0f09-4f4d-85f0-72df4684ac07\kmos_pearl_atmosphere_1795813764667.jpg"),
}

FONT_PATHS = {
    "bold": r"C:\Windows\Fonts\segoeuib.ttf",
    "semi": r"C:\Windows\Fonts\seguisb.ttf",
    "regular": r"C:\Windows\Fonts\segoeui.ttf",
    "light": r"C:\Windows\Fonts\segoeuisl.ttf",
    "italic": r"C:\Windows\Fonts\segoeuii.ttf",
    "mono": r"C:\Windows\Fonts\consola.ttf",
}

SVG_FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
SVG_MONO = "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"


def load_font(style: str, size: int) -> ImageFont.FreeTypeFont:
    p = Path(FONT_PATHS.get(style, FONT_PATHS["regular"]))
    if not p.exists():
        p = Path(FONT_PATHS["regular"])
    return ImageFont.truetype(str(p), size=size)


def cover_resize(img: Image.Image, target_w: int, target_h: int, anchor_y: float = 0.55) -> Image.Image:
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    nw, nh = int(round(src_w * scale)), int(round(src_h * scale))
    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = max(0, (nw - target_w) // 2)
    top = max(0, min(nh - target_h, int((nh - target_h) * anchor_y)))
    return resized.crop((left, top, left + target_w, top + target_h)).convert("RGBA")


def draw_liquid_glass(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    radius: int,
    theme: str,
    blur_radius: int = 38,
    fill_opacity: int | None = None,
) -> Image.Image:
    """Composite physical frosted Liquid Glass card with Gaussian blur, upper specular highlight, and rim gradient."""
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1

    # 1. Soft elevation shadow
    shadow_pad = 36
    shadow = Image.new("RGBA", (w + shadow_pad * 2, h + shadow_pad * 2), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    s_alpha = 95 if theme == "dark" else 34
    sd.rounded_rectangle(
        (shadow_pad, shadow_pad + 10, w + shadow_pad, h + shadow_pad + 10),
        radius=radius,
        fill=(4, 9, 20, s_alpha),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(20))
    canvas.alpha_composite(shadow, (x1 - shadow_pad, y1 - shadow_pad))

    # 2. Extract underlying wallpaper region & apply frosted optical blur
    bg_crop = canvas.crop((x1, y1, x2, y2)).filter(ImageFilter.GaussianBlur(blur_radius))
    if theme == "dark":
        alpha = 142 if fill_opacity is None else fill_opacity
        tint = Image.new("RGBA", (w, h), (13, 23, 42, alpha))
    else:
        alpha = 176 if fill_opacity is None else fill_opacity
        tint = Image.new("RGBA", (w, h), (255, 255, 255, alpha))
    frosted = Image.alpha_composite(bg_crop, tint)

    # 3. Diagonal subtle specular sheen inside upper-left glass edge
    sheen = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh_draw = ImageDraw.Draw(sheen)
    for row in range(h // 2):
        frac = 1.0 - (row / max(1, h // 2))
        s_a = int((26 if theme == "dark" else 55) * (frac ** 2.2))
        if s_a > 0:
            sh_draw.line([(0, row), (w, row)], fill=(255, 255, 255, s_a))
    frosted = Image.alpha_composite(frosted, sheen)

    # 4. Rounded mask
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=255)
    canvas.paste(frosted, (x1, y1), mask)

    # 5. Crisp seamless directional glass rim border (smooth vertical specular falloff)
    rim = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rim)
    rim_bot = (130, 170, 230, 34) if theme == "dark" else (148, 163, 184, 82)
    rd.rounded_rectangle((1, 1, w - 2, h - 2), radius=radius, outline=rim_bot, width=2)

    spec_full = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd_spec = ImageDraw.Draw(spec_full)
    rim_top = (224, 240, 255, 118) if theme == "dark" else (255, 255, 255, 245)
    sd_spec.rounded_rectangle((1, 1, w - 2, h - 2), radius=radius, outline=rim_top, width=2)
    alpha_mask = Image.new("L", (w, h), 0)
    ad = ImageDraw.Draw(alpha_mask)
    fade_h = max(1, int(h * 0.52))
    for row in range(fade_h):
        val = int(255 * ((1.0 - row / fade_h) ** 1.6))
        ad.line([(0, row), (w, row)], fill=val)
    spec_r, spec_g, spec_b, spec_a = spec_full.split()
    scaled_a = Image.composite(spec_a, Image.new("L", (w, h), 0), alpha_mask)
    # Multiply spec_a with alpha_mask smoothly
    from PIL import ImageChops
    final_spec_a = ImageChops.multiply(spec_a, alpha_mask)
    spec_full.putalpha(final_spec_a)
    rim = Image.alpha_composite(rim, spec_full)
    canvas.alpha_composite(rim, (x1, y1))
    return canvas


def draw_km_monogram_pil(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int, theme: str):
    """Draw original interlocking geometric KM monogram + subtle orbital halo."""
    r = size // 2
    accent = (140, 200, 255, 248) if theme == "dark" else (29, 78, 216, 248)
    primary = (248, 250, 252, 255) if theme == "dark" else (15, 23, 42, 255)
    halo = (196, 181, 253, 130) if theme == "dark" else (79, 70, 229, 105)

    # Subtle broken orbital ring + satellite dot (subtle cosmic/explorer nod)
    draw.arc((cx - r, cy - r, cx + r, cy + r), start=38, end=308, fill=halo, width=3)
    dot_x = cx + int(r * 0.78)
    dot_y = cy - int(r * 0.62)
    draw.ellipse((dot_x - 3, dot_y - 3, dot_x + 3, dot_y + 3), fill=accent)

    # Interlocking geometric K + M peaks cleanly proportioned inside the halo
    s = int(size * 0.21)
    w_line = max(3, int(size * 0.08))
    kx = cx - int(s * 1.1)
    draw.line([(kx, cy - s), (kx, cy + s)], fill=primary, width=w_line)
    pts = [
        (kx + w_line // 2, cy + 1),
        (cx - int(s * 0.25), cy - s + 1),
        (cx + int(s * 0.20), cy + int(s * 0.28)),
        (cx + int(s * 0.75), cy - s + 1),
        (cx + int(s * 1.05), cy + s),
    ]
    draw.line(pts, fill=accent, width=w_line, joint="curve")
    draw.line([(kx + w_line // 2, cy - 1), (cx - int(s * 0.25), cy + s)], fill=primary, width=w_line)


def build_hero(theme: str):
    W, H = 2880, 1000  # 2x supersampled -> saved as 1440x500
    base = cover_resize(Image.open(WALLPAPERS[theme]), W, H, anchor_y=0.58)

    # Subtle contrast scrim on left text zone so typography stays ultra crisp over sky/horizon
    scrim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    for col in range(1600):
        frac = 1.0 - (col / 1600)
        a = int((75 if theme == "dark" else 68) * (frac ** 1.5))
        c = (5, 9, 18, a) if theme == "dark" else (246, 249, 253, a)
        sd.line([(col, 0), (col, H)], fill=c)
    base = Image.alpha_composite(base, scrim)

    # Top OS status pill
    draw_liquid_glass(base, (112, 72, 1050, 156), radius=42, theme=theme, blur_radius=28)

    # 3 staggered right-hand frosted Liquid Glass telemetry cards
    cards = [
        ((1790, 118, 2768, 344), "RESEARCH & MODELING", "Spatial Climate AI & Fraud Risk", "PyTorch 2D Thermal PINN · XGBoost · K-Means & LDA"),
        ((1716, 384, 2768, 610), "CORE ARCHITECTURE", "Full-Stack ML & Engineering", "Python · Scikit-Learn · React · TypeScript · SQL"),
        ((1790, 650, 2768, 876), "VERIFIED SIGNAL", "6 Original Repos · 24 LeetCode", "3.3 MB Public Code · Kaggle, Credly & Udemy"),
    ]
    for box, *_ in cards:
        draw_liquid_glass(base, box, radius=44, theme=theme, blur_radius=36)

    # Bottom subtle focus pill on left
    draw_liquid_glass(base, (112, 796, 1210, 878), radius=41, theme=theme, blur_radius=28)

    # Draw vector typography & KM monogram
    d = ImageDraw.Draw(base)
    fg_main = (248, 250, 252, 255) if theme == "dark" else (15, 23, 42, 255)
    fg_sub = (212, 224, 240, 245) if theme == "dark" else (51, 65, 85, 255)
    fg_muted = (148, 168, 194, 235) if theme == "dark" else (71, 85, 105, 245)
    accent = (140, 200, 255, 255) if theme == "dark" else (29, 78, 216, 255)
    accent_alt = (196, 181, 253, 245) if theme == "dark" else (79, 70, 229, 245)

    # Top status bar text + monogram
    draw_km_monogram_pil(d, 168, 114, 54, theme)
    f_pill_b = load_font("bold", 30)
    f_pill_r = load_font("regular", 28)
    d.text((222, 95), "KM OS", font=f_pill_b, fill=accent)
    d.text((346, 97), "·   Personal Workspace   ·   M.Sc. Big Data Analysis", font=f_pill_r, fill=fg_sub)

    # Left hero focal identity
    f_eyebrow = load_font("semi", 26)
    f_name = load_font("bold", 152)
    f_role = load_font("semi", 42)
    f_quote = load_font("italic", 36)
    f_loc = load_font("regular", 28)

    d.text((118, 248), "DATA SCIENCE   ·   AI & ML   ·   SOFTWARE ENGINEERING", font=f_eyebrow, fill=accent)
    d.text((112, 294), "Krushil Modi", font=f_name, fill=fg_main)
    d.text((118, 488), "St. Xavier's College, Ahmedabad   ·   AI / ML & Analytics Builder", font=f_role, fill=fg_sub)
    d.text((118, 568), "“Exploring intelligence. Engineering possibilities.”", font=f_quote, fill=accent_alt)

    # Left bottom horizon capsule
    dot_c = (52, 211, 153, 255) if theme == "dark" else (5, 150, 105, 255)
    d.ellipse((152, 829, 170, 847), fill=dot_c)
    d.text((196, 820), "Urban Climate PINN   ·   UPI FraudGuard   ·   Full-Stack Web Systems", font=f_loc, fill=fg_sub)

    # Right Liquid Glass card typography
    f_card_k = load_font("semi", 24)
    f_card_t = load_font("bold", 40)
    f_card_d = load_font("regular", 28)
    for (x1, y1, x2, y2), kicker, title, detail in cards:
        px = x1 + 48
        d.text((px, y1 + 36), kicker, font=f_card_k, fill=accent)
        d.text((px, y1 + 78), title, font=f_card_t, fill=fg_main)
        d.text((px, y1 + 144), detail, font=f_card_d, fill=fg_muted)

    out = base.resize((1440, 500), Image.Resampling.LANCZOS).convert("RGB")
    dest = HERO_DIR / f"kmos-hero-{theme}.png"
    out.save(dest, format="PNG", optimize=True)
    print(f"Generated {dest.name}: {dest.stat().st_size // 1024} KB")


def build_footer(theme: str):
    W, H = 2880, 340
    base = cover_resize(Image.open(WALLPAPERS[theme]), W, H, anchor_y=0.92)
    draw_liquid_glass(base, (440, 68, 2440, 272), radius=54, theme=theme, blur_radius=34)

    d = ImageDraw.Draw(base)
    fg_main = (248, 250, 252, 255) if theme == "dark" else (15, 23, 42, 255)
    fg_muted = (175, 194, 220, 240) if theme == "dark" else (71, 85, 105, 245)
    accent = (140, 200, 255, 255) if theme == "dark" else (29, 78, 216, 255)

    draw_km_monogram_pil(d, 560, 170, 74, theme)
    f_title = load_font("bold", 42)
    f_sub = load_font("regular", 30)
    d.text((642, 118), "KM OS   ·   Krushil Modi", font=f_title, fill=fg_main)
    d.text((642, 180), "Exploring intelligence. Engineering possibilities.   ·   Ahmedabad, India", font=f_sub, fill=fg_muted)
    d.text((2344, 170), "github.com/Krushilmodi1", font=load_font("semi", 30), fill=accent, anchor="rm")

    out = base.resize((1440, 170), Image.Resampling.LANCZOS).convert("RGB")
    dest = HERO_DIR / f"kmos-footer-{theme}.png"
    out.save(dest, format="PNG", optimize=True)
    print(f"Generated {dest.name}: {dest.stat().st_size // 1024} KB")


def module_glyph_svg(kind: str, stroke: str, accent: str) -> str:
    if kind == "data-studio":
        return f"""
        <rect x="24" y="21" width="12" height="12" rx="3" fill="{accent}" fill-opacity="0.88"/>
        <rect x="39" y="21" width="12" height="12" rx="3" fill="{stroke}" fill-opacity="0.32"/>
        <rect x="24" y="36" width="12" height="12" rx="3" fill="{stroke}" fill-opacity="0.32"/>
        <rect x="39" y="36" width="12" height="12" rx="3" fill="{accent}" fill-opacity="0.55"/>"""
    if kind == "intelligence-lab":
        return f"""
        <circle cx="29" cy="35" r="4.5" fill="{accent}"/>
        <circle cx="46" cy="25" r="4" fill="{stroke}" fill-opacity="0.72"/>
        <circle cx="46" cy="45" r="4" fill="{accent}" fill-opacity="0.75"/>
        <path d="M33 33 L42 27 M33 37 L42 43" stroke="{stroke}" stroke-width="1.8" stroke-opacity="0.55"/>"""
    if kind == "dev-workspace":
        return f"""
        <rect x="23" y="22" width="28" height="24" rx="5" fill="none" stroke="{stroke}" stroke-width="1.8" stroke-opacity="0.65"/>
        <path d="M23 30 H51" stroke="{stroke}" stroke-width="1.5" stroke-opacity="0.35"/>
        <circle cx="28.5" cy="26" r="1.5" fill="{accent}"/>
        <path d="M31 36 L35 39 L31 42 M38 42 H44" stroke="{accent}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" fill="none"/>"""
    if kind == "academic-journey":
        return f"""
        <circle cx="37" cy="35" r="12" fill="none" stroke="{stroke}" stroke-width="1.5" stroke-opacity="0.38" stroke-dasharray="4 3"/>
        <circle cx="37" cy="35" r="4.5" fill="{accent}"/>
        <circle cx="46" cy="26" r="2.8" fill="{stroke}" fill-opacity="0.85"/>"""
    return f"""
    <path d="M23 41 L30 33 L36 38 L44 25 L51 31" fill="none" stroke="{accent}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="44" cy="25" r="2.6" fill="{stroke}"/>"""


def build_module_headers():
    modules = [
        ("data-studio", "01", "Data Studio", "Spatial Climate Modeling · Statistical Behavioral Analytics"),
        ("intelligence-lab", "02", "Intelligence Lab", "XGBoost Fraud Risk Pipeline · End-to-End Inference UI"),
        ("dev-workspace", "03", "Dev Workspace", "Full-Stack TypeScript, React &amp; Algorithmic Systems"),
        ("academic-journey", "04", "Academic Journey", "B.C.A. Foundation · M.Sc. Big Data Analysis · Verified Credentials"),
        ("activity-center", "05", "Activity Center", "Live GitHub Telemetry · Contribution Calendar · Codebase Mix"),
    ]
    themes = {
        "dark": {
            "bg1": "#0D1626", "bg2": "#13213A", "stroke": "#94B8E8", "stroke_op": "0.24",
            "title": "#F8FAFC", "sub": "#94A3B8", "accent": "#8CC8FF", "pill_bg": "#172947",
            "glyph_str": "#CBD5E1",
        },
        "light": {
            "bg1": "#F8FBFF", "bg2": "#EDF3FC", "stroke": "#94A3B8", "stroke_op": "0.32",
            "title": "#0F172A", "sub": "#475569", "accent": "#1D4ED8", "pill_bg": "#E0EAFC",
            "glyph_str": "#1E293B",
        },
    }
    for slug, idx, title, sub in modules:
        for theme, c in themes.items():
            svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="70" viewBox="0 0 1200 70" role="img" aria-label="{title}">
  <defs>
    <linearGradient id="mbg-{slug}-{theme}" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{c['bg1']}"/>
      <stop offset="100%" stop-color="{c['bg2']}"/>
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="1198" height="68" rx="18" fill="url(#mbg-{slug}-{theme})" stroke="{c['stroke']}" stroke-opacity="{c['stroke_op']}" stroke-width="1.2"/>
  <rect x="14" y="12" width="46" height="46" rx="13" fill="{c['pill_bg']}" stroke="{c['accent']}" stroke-opacity="0.28" stroke-width="1"/>
  {module_glyph_svg(slug, c['glyph_str'], c['accent'])}
  <text x="76" y="30" fill="{c['accent']}" font-family="{SVG_MONO}" font-size="11" font-weight="600" letter-spacing="1.6">MODULE {idx}</text>
  <text x="76" y="51" fill="{c['title']}" font-family="{SVG_FONT}" font-size="21" font-weight="700">{title}</text>
  <text x="1172" y="40" text-anchor="end" fill="{c['sub']}" font-family="{SVG_FONT}" font-size="13.5" font-weight="500">{sub}</text>
</svg>
"""
            (MOD_DIR / f"{slug}-{theme}.svg").write_text(svg.strip() + "\n", encoding="utf-8")


def build_academic_svg():
    themes = {
        "dark": {
            "bg1": "#0A1220", "bg2": "#111D33", "card": "#14223B", "stroke": "#8CB4EC", "stroke_op": "0.22",
            "title": "#F8FAFC", "sub": "#CBD5E1", "muted": "#94A3B8", "accent": "#8CC8FF", "purple": "#C4B5FD", "emerald": "#34D399",
            "chip_bg": "#1B2E4E", "chip_study": "#231E42",
        },
        "light": {
            "bg1": "#F7FAFE", "bg2": "#ECF2FA", "card": "#FFFFFF", "stroke": "#94A3B8", "stroke_op": "0.28",
            "title": "#0F172A", "sub": "#334155", "muted": "#64748B", "accent": "#1D4ED8", "purple": "#6D28D9", "emerald": "#059669",
            "chip_bg": "#E8F0FE", "chip_study": "#F3EEFF",
        },
    }
    for theme, c in themes.items():
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="310" viewBox="0 0 1200 310" role="img" aria-label="Academic Journey and Capability Architecture">
  <defs>
    <linearGradient id="edubg-{theme}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{c['bg1']}"/>
      <stop offset="100%" stop-color="{c['bg2']}"/>
    </linearGradient>
    <linearGradient id="pathgrad-{theme}" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{c['accent']}" stop-opacity="0.35"/>
      <stop offset="50%" stop-color="{c['accent']}" stop-opacity="0.95"/>
      <stop offset="100%" stop-color="{c['purple']}" stop-opacity="0.75"/>
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="1198" height="308" rx="22" fill="url(#edubg-{theme})" stroke="{c['stroke']}" stroke-opacity="{c['stroke_op']}" stroke-width="1.2"/>

  <!-- Left: Trajectory Timeline -->
  <path d="M44 102 H520" stroke="url(#pathgrad-{theme})" stroke-width="2" stroke-dasharray="5 5"/>
  <circle cx="44" cy="102" r="6" fill="{c['accent']}"/>
  <circle cx="300" cy="102" r="7" fill="{c['emerald']}"/>
  <circle cx="520" cy="102" r="5" fill="{c['purple']}"/>

  <!-- Milestone 1 -->
  <rect x="28" y="24" width="252" height="106" rx="16" fill="{c['card']}" fill-opacity="0.88" stroke="{c['stroke']}" stroke-opacity="{c['stroke_op']}"/>
  <text x="46" y="49" fill="{c['accent']}" font-family="{SVG_MONO}" font-size="11" font-weight="600" letter-spacing="1.2">UNDERGRADUATE · COMPLETED</text>
  <text x="46" y="75" fill="{c['title']}" font-family="{SVG_FONT}" font-size="18" font-weight="700">B.C.A.</text>
  <text x="46" y="96" fill="{c['sub']}" font-family="{SVG_FONT}" font-size="12.5">Bachelor of Computer Applications</text>
  <text x="46" y="115" fill="{c['muted']}" font-family="{SVG_FONT}" font-size="11.5">Algorithms · DBMS · OOP · Web</text>

  <!-- Milestone 2 -->
  <rect x="296" y="24" width="264" height="106" rx="16" fill="{c['card']}" fill-opacity="0.94" stroke="{c['emerald']}" stroke-opacity="0.45"/>
  <text x="314" y="49" fill="{c['emerald']}" font-family="{SVG_MONO}" font-size="11" font-weight="600" letter-spacing="1.2">POSTGRADUATE · IN PROGRESS</text>
  <text x="314" y="75" fill="{c['title']}" font-family="{SVG_FONT}" font-size="18" font-weight="700">M.Sc. Big Data Analysis</text>
  <text x="314" y="96" fill="{c['sub']}" font-family="{SVG_FONT}" font-size="12.5">St. Xavier's College, Ahmedabad</text>
  <text x="314" y="115" fill="{c['muted']}" font-family="{SVG_FONT}" font-size="11.5">ML · Statistical Inference · Deep Learning</text>

  <!-- Lower Left: Research & Curriculum Study -->
  <rect x="28" y="148" width="532" height="136" rx="16" fill="{c['card']}" fill-opacity="0.82" stroke="{c['purple']}" stroke-opacity="0.28"/>
  <text x="46" y="174" fill="{c['purple']}" font-family="{SVG_MONO}" font-size="11" font-weight="600" letter-spacing="1.2">ACADEMIC STUDY &amp; CURRICULUM FOUNDATIONS</text>
  <text x="46" y="196" fill="{c['muted']}" font-family="{SVG_FONT}" font-size="12">Coursework concepts &amp; theory studied alongside applied builds (distinct from shipped repos):</text>

  <rect x="46" y="211" width="128" height="27" rx="8" fill="{c['chip_study']}"/><text x="110" y="229" text-anchor="middle" fill="{c['purple']}" font-family="{SVG_FONT}" font-size="12" font-weight="600">CNN · RNN · LSTM</text>
  <rect x="184" y="211" width="152" height="27" rx="8" fill="{c['chip_study']}"/><text x="260" y="229" text-anchor="middle" fill="{c['purple']}" font-family="{SVG_FONT}" font-size="12" font-weight="600">GRU &amp; Transformers</text>
  <rect x="346" y="211" width="194" height="27" rx="8" fill="{c['chip_study']}"/><text x="443" y="229" text-anchor="middle" fill="{c['purple']}" font-family="{SVG_FONT}" font-size="12" font-weight="600">Attention Mechanisms</text>
  <rect x="46" y="246" width="174" height="27" rx="8" fill="{c['chip_study']}"/><text x="133" y="264" text-anchor="middle" fill="{c['purple']}" font-family="{SVG_FONT}" font-size="12" font-weight="600">Reinforcement Learning</text>
  <rect x="230" y="246" width="180" height="27" rx="8" fill="{c['chip_study']}"/><text x="320" y="264" text-anchor="middle" fill="{c['purple']}" font-family="{SVG_FONT}" font-size="12" font-weight="600">Econometrics &amp; Time Series</text>
  <rect x="420" y="246" width="120" height="27" rx="8" fill="{c['chip_study']}"/><text x="480" y="264" text-anchor="middle" fill="{c['purple']}" font-family="{SVG_FONT}" font-size="12" font-weight="600">Power BI (2025)</text>

  <!-- Right Panel: Verified Project-Applied Engineering Matrix -->
  <rect x="582" y="24" width="590" height="260" rx="18" fill="{c['card']}" fill-opacity="0.90" stroke="{c['stroke']}" stroke-opacity="{c['stroke_op']}"/>
  <text x="606" y="52" fill="{c['accent']}" font-family="{SVG_MONO}" font-size="11" font-weight="600" letter-spacing="1.2">PROJECT-PROVEN SYSTEMS STACK</text>
  <text x="606" y="75" fill="{c['title']}" font-family="{SVG_FONT}" font-size="16.5" font-weight="700">Verified Technologies Applied in Public Repositories</text>

  <text x="606" y="108" fill="{c['muted']}" font-family="{SVG_MONO}" font-size="11">DATA &amp; ML MODELING</text>
  <rect x="606" y="118" width="84" height="27" rx="8" fill="{c['chip_bg']}"/><text x="648" y="136" text-anchor="middle" fill="{c['accent']}" font-family="{SVG_FONT}" font-size="12" font-weight="600">Python</text>
  <rect x="698" y="118" width="90" height="27" rx="8" fill="{c['chip_bg']}"/><text x="743" y="136" text-anchor="middle" fill="{c['accent']}" font-family="{SVG_FONT}" font-size="12" font-weight="600">PyTorch</text>
  <rect x="796" y="118" width="94" height="27" rx="8" fill="{c['chip_bg']}"/><text x="843" y="136" text-anchor="middle" fill="{c['accent']}" font-family="{SVG_FONT}" font-size="12" font-weight="600">XGBoost</text>
  <rect x="898" y="118" width="114" height="27" rx="8" fill="{c['chip_bg']}"/><text x="955" y="136" text-anchor="middle" fill="{c['accent']}" font-family="{SVG_FONT}" font-size="12" font-weight="600">Scikit-Learn</text>
  <rect x="1020" y="118" width="128" height="27" rx="8" fill="{c['chip_bg']}"/><text x="1084" y="136" text-anchor="middle" fill="{c['accent']}" font-family="{SVG_FONT}" font-size="12" font-weight="600">Pandas · SciPy</text>

  <text x="606" y="172" fill="{c['muted']}" font-family="{SVG_MONO}" font-size="11">ANALYTICS &amp; GEOSPATIAL</text>
  <rect x="606" y="182" width="124" height="27" rx="8" fill="{c['chip_bg']}"/><text x="668" y="200" text-anchor="middle" fill="{c['title']}" font-family="{SVG_FONT}" font-size="12" font-weight="600">GeoPandas · GEE</text>
  <rect x="738" y="182" width="134" height="27" rx="8" fill="{c['chip_bg']}"/><text x="805" y="200" text-anchor="middle" fill="{c['title']}" font-family="{SVG_FONT}" font-size="12" font-weight="600">Leaflet · Chart.js</text>
  <rect x="880" y="182" width="142" height="27" rx="8" fill="{c['chip_bg']}"/><text x="951" y="200" text-anchor="middle" fill="{c['title']}" font-family="{SVG_FONT}" font-size="12" font-weight="600">K-Means · LDA</text>
  <rect x="1030" y="182" width="118" height="27" rx="8" fill="{c['chip_bg']}"/><text x="1089" y="200" text-anchor="middle" fill="{c['title']}" font-family="{SVG_FONT}" font-size="12" font-weight="600">ANOVA · Moran's I</text>

  <text x="606" y="236" fill="{c['muted']}" font-family="{SVG_MONO}" font-size="11">ENGINEERING &amp; WEB SYSTEMS</text>
  <rect x="606" y="246" width="106" height="27" rx="8" fill="{c['chip_bg']}"/><text x="659" y="264" text-anchor="middle" fill="{c['title']}" font-family="{SVG_FONT}" font-size="12" font-weight="600">TypeScript</text>
  <rect x="720" y="246" width="118" height="27" rx="8" fill="{c['chip_bg']}"/><text x="779" y="264" text-anchor="middle" fill="{c['title']}" font-family="{SVG_FONT}" font-size="12" font-weight="600">React · Vite</text>
  <rect x="846" y="246" width="146" height="27" rx="8" fill="{c['chip_bg']}"/><text x="919" y="264" text-anchor="middle" fill="{c['title']}" font-family="{SVG_FONT}" font-size="12" font-weight="600">Tailwind · shadcn/ui</text>
  <rect x="1000" y="246" width="148" height="27" rx="8" fill="{c['chip_bg']}"/><text x="1074" y="264" text-anchor="middle" fill="{c['title']}" font-family="{SVG_FONT}" font-size="12" font-weight="600">PostgreSQL · Supabase</text>
</svg>
"""
        (EDU_DIR / f"academic-journey-{theme}.svg").write_text(svg.strip() + "\n", encoding="utf-8")


def main():
    HERO_DIR.mkdir(parents=True, exist_ok=True)
    MOD_DIR.mkdir(parents=True, exist_ok=True)
    EDU_DIR.mkdir(parents=True, exist_ok=True)
    for t in ("dark", "light"):
        build_hero(t)
        build_footer(t)
    build_module_headers()
    build_academic_svg()
    print("All KM OS static & atmospheric assets generated cleanly.")


if __name__ == "__main__":
    main()
