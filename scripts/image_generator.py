#!/usr/bin/env python3
"""
مولّد الصور - يستخدم HTML/CSS ويحوّلها لـ PNG عبر محاكي المتصفح
أو SVG مباشرة مع دعم عربي صحيح
"""

from pathlib import Path
from datetime import datetime, timezone
import re

def create_blog_image_svg(title: str, category: str, slug: str, images_dir: Path) -> Path:
    """يصمم صورة hero بأسلوب ثمانية — SVG مع دعم عربي كامل"""
    
    cat_colors = {
        "منهجية":      "#e03c2a",
        "تقنية":       "#e8884e", 
        "أداة":        "#4e9de8",
        "تحليل":       "#9de84e",
        "AI Red Team": "#b44ee8",
    }
    cat_color = cat_colors.get(category, "#e03c2a")
    date_str = datetime.now(timezone.utc).strftime("%d %b %Y")
    
    # اقتصر العنوان إن كان طويلاً
    words = title.split()
    if len(words) > 8:
        line1 = " ".join(words[:5])
        line2 = " ".join(words[5:10])
        line3 = " ".join(words[10:]) if len(words) > 10 else ""
    elif len(words) > 4:
        line1 = " ".join(words[:4])
        line2 = " ".join(words[4:])
        line3 = ""
    else:
        line1 = title
        line2 = ""
        line3 = ""

    # احسب y للعنوان حسب عدد الأسطر
    title_y1 = 280
    title_y2 = 360
    title_y3 = 440
    line_after_title = title_y3 + 60 if line3 else (title_y2 + 60 if line2 else title_y1 + 80)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Noto+Naskh+Arabic:wght@700&amp;family=Noto+Sans+Arabic:wght@400;500&amp;display=swap');
      .title {{ font-family: "Noto Naskh Arabic", serif; font-size: 52px; font-weight: 700; fill: #f0ede8; }}
      .cat   {{ font-family: "Noto Sans Arabic", sans-serif; font-size: 20px; font-weight: 500; fill: {cat_color}; }}
      .brand {{ font-family: "Noto Sans Arabic", sans-serif; font-size: 18px; fill: #444; }}
      .date  {{ font-family: monospace; font-size: 16px; fill: #444; }}
    </style>
  </defs>
  
  <!-- خلفية -->
  <rect width="1200" height="630" fill="#0d0d0d"/>
  
  <!-- خطوط الشبكة الخفية -->
  {''.join(f'<line x1="{i}" y1="0" x2="{i}" y2="630" stroke="#111" stroke-width="1"/>' for i in range(0, 1200, 60))}
  
  <!-- شريط علوي -->
  <rect x="0" y="0" width="1200" height="5" fill="{cat_color}"/>
  
  <!-- شريط سفلي -->
  <rect x="0" y="625" width="1200" height="5" fill="#1a1a1a"/>
  
  <!-- تاق التصنيف -->
  <rect x="54" y="40" width="180" height="40" rx="6" fill="#1a0804" stroke="{cat_color}" stroke-width="1"/>
  <text x="144" y="65" class="cat" text-anchor="middle">{category}</text>
  
  <!-- العنوان -->
  <text x="1140" y="{title_y1}" class="title" text-anchor="end" direction="rtl">{line1}</text>
  {f'<text x="1140" y="{title_y2}" class="title" text-anchor="end" direction="rtl">{line2}</text>' if line2 else ''}
  {f'<text x="1140" y="{title_y3}" class="title" text-anchor="end" direction="rtl">{line3}</text>' if line3 else ''}
  
  <!-- خط أحمر فاصل -->
  <rect x="54" y="{line_after_title}" width="80" height="4" fill="{cat_color}" rx="2"/>
  
  <!-- شعار وتاريخ -->
  <text x="60" y="600" class="brand">OffsecAR</text>
  <text x="1140" y="600" class="date" text-anchor="end">{date_str}</text>
</svg>'''

    out_path = images_dir / f"{slug}.svg"
    out_path.write_text(svg, encoding="utf-8")
    return out_path


def create_news_image_svg(headline: str, category: str, severity: str, cvss: str, images_dir: Path, date_str: str) -> Path:
    """يصمم صورة خبر يومي بأسلوب ثمانية"""
    
    sev_colors = {"حرجة": "#e03c2a", "عالية": "#e8884e", "متوسطة": "#e8c44e"}
    sev_col = sev_colors.get(severity, "#e8884e")
    
    words = headline.split()
    if len(words) > 7:
        line1 = " ".join(words[:5])
        line2 = " ".join(words[5:10])
        line3 = " ".join(words[10:]) if len(words) > 10 else ""
    elif len(words) > 4:
        line1 = " ".join(words[:4])
        line2 = " ".join(words[4:])
        line3 = ""
    else:
        line1 = headline
        line2 = ""
        line3 = ""

    cvss_text = f"CVSS {cvss}" if cvss and cvss != "None" else ""
    title_y1 = 260
    title_y2 = 340
    title_y3 = 420

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1080" viewBox="0 0 1080 1080">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Noto+Naskh+Arabic:wght@700&amp;family=Noto+Sans+Arabic:wght@400;500&amp;display=swap');
      .title {{ font-family: "Noto Naskh Arabic", serif; font-size: 50px; font-weight: 700; fill: #f5f5f5; }}
      .cat   {{ font-family: "Noto Sans Arabic", sans-serif; font-size: 20px; fill: #888; }}
      .tag   {{ font-family: monospace; font-size: 18px; fill: #e03c2a; letter-spacing: 2px; }}
      .sev   {{ font-family: "Noto Sans Arabic", sans-serif; font-size: 20px; fill: {sev_col}; }}
      .brand {{ font-family: "Noto Sans Arabic", sans-serif; font-size: 20px; fill: #555; }}
    </style>
  </defs>
  
  <rect width="1080" height="1080" fill="#0d0d0d"/>
  {''.join(f'<line x1="{i}" y1="0" x2="{i}" y2="1080" stroke="#111" stroke-width="1"/>' for i in range(0, 1080, 60))}
  <rect x="0" y="0" width="1080" height="6" fill="#e03c2a"/>
  
  <!-- تاق OffsecAR -->
  <rect x="54" y="28" width="200" height="38" rx="6" fill="#1a0804" stroke="#e03c2a" stroke-width="1"/>
  <text x="154" y="52" class="tag" text-anchor="middle">OffsecAR</text>
  
  <!-- التصنيف -->
  <text x="1020" y="110" class="cat" text-anchor="end" direction="rtl">{category}</text>
  
  <!-- فاصل -->
  <rect x="54" y="160" width="972" height="1" fill="#2a2a2a"/>
  
  <!-- العنوان -->
  <text x="1010" y="{title_y1}" class="title" text-anchor="end" direction="rtl">{line1}</text>
  {f'<text x="1010" y="{title_y2}" class="title" text-anchor="end" direction="rtl">{line2}</text>' if line2 else ''}
  {f'<text x="1010" y="{title_y3}" class="title" text-anchor="end" direction="rtl">{line3}</text>' if line3 else ''}
  
  <!-- خط أحمر -->
  <rect x="54" y="480" width="60" height="4" fill="#e03c2a" rx="2"/>
  
  <!-- درجة الخطورة -->
  <rect x="54" y="920" width="260" height="44" rx="8" fill="#1a1a1a" stroke="{sev_col}" stroke-width="1"/>
  <circle cx="80" cy="942" r="7" fill="{sev_col}"/>
  <text x="96" y="948" class="sev">خطورة {severity}{f"  ·  {cvss_text}" if cvss_text else ""}</text>
  
  <!-- فاصل سفلي -->
  <rect x="54" y="984" width="972" height="1" fill="#2a2a2a"/>
  
  <!-- الشعار والتاريخ -->
  <text x="60" y="1012" class="brand">@OffsecARE</text>
  <text x="1020" y="1012" class="brand" text-anchor="end">malekalthubiany.github.io/OffsecAR</text>
</svg>'''

    out_path = images_dir / f"{date_str}-post.svg"
    out_path.write_text(svg, encoding="utf-8")
    return out_path
