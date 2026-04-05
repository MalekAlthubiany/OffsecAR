#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper

AMIRI_REG  = '/usr/share/fonts/opentype/fonts-hosny-amiri/Amiri-Regular.ttf'
AMIRI_BOLD = '/usr/share/fonts/opentype/fonts-hosny-amiri/Amiri-Bold.ttf'
DEJAVU     = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

CAT_COLORS = {
    "منهجية":"#e03c2a","تقنية":"#e8884e","أداة":"#4e9de8",
    "تحليل":"#7ec845","ثغرة حرجة":"#e03c2a","تقنية هجوم":"#e8884e",
    "تهديد متقدم":"#e8c44e","تحليل أخبار":"#7ec845",
    "الأمن الهجومي في الذكاء الاصطناعي":"#b44ee8",
    "Bug Bounty":"#4ee8b4",
}
SEV_COLORS = {"حرجة":"#e03c2a","عالية":"#e8884e","متوسطة":"#e8c44e"}

def gf(size, bold=False):
    p = AMIRI_BOLD if bold else AMIRI_REG
    if Path(p).exists():
        try: return ImageFont.truetype(p, size)
        except: pass
    for fb in ['/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf',DEJAVU]:
        if Path(fb).exists():
            try: return ImageFont.truetype(fb, size)
            except: pass
    return ImageFont.load_default()

def gmono(size):
    if Path(DEJAVU).exists(): return ImageFont.truetype(DEJAVU, size)
    return ImageFont.load_default()

def ar(text):
    try: return arabic_reshaper.reshape(str(text))
    except: return str(text)

def rtext(d, text, font, rx, y, fill):
    """رسم نص محاذٍ لليمين"""
    bb = d.textbbox((0,0), text, font=font)
    tw = bb[2] - bb[0]
    th = bb[3] - bb[1]
    d.text((rx - tw, y), text, font=font, fill=fill)
    return th

def wrap_words(text, n=4):
    words = text.split()
    return [' '.join(words[i:i+n]) for i in range(0, len(words), n)]

def make_card(title, category, severity, cvss, excerpt, date_str, W, H, accent, handle, out):
    img = Image.new('RGB', (W, H), '#0c0c0c')
    d = ImageDraw.Draw(img)
    P = max(44, W//22)

    # شبكة خفية
    for i in range(0, W, W//18):
        d.line([(i,0),(i,H)], fill='#0f0f0f')

    # شريط علوي
    d.rectangle([0,0,W,4], fill=accent)

    # فونتات حسب الحجم
    fs = gf(max(16, W//60))
    ft = gf(max(36, W//22), bold=True)
    fb = gf(max(20, W//46))
    fh = gf(max(14, W//68))
    fm = gmono(max(13, W//76))

    # لوقو OffsecAR
    logo_size = max(44, W//22)
    logo_path = Path('/home/runner/work/OffsecAR/OffsecAR/assets/images/logo.png')
    if not logo_path.exists():
        logo_path = Path('assets/images/logo.png')
    if logo_path.exists():
        try:
            logo = Image.open(logo_path).convert('RGBA').resize((logo_size, logo_size))
            img.paste(logo, (P, P-6), logo)
        except:
            pass
    tag_w = max(110, W//9)
    tag_h = max(28, H//34)
    d.text((P + logo_size + 10, P + tag_h//2 - 6), 'OffsecAR', font=fm, fill=accent)

    # تصنيف يمين
    rtext(d, ar(category), fs, W-P, P+2, '#3a3a3a')

    # فاصل
    sep_y = P + tag_h + 14
    d.rectangle([P, sep_y, W-P, sep_y+1], fill='#1a1a1a')

    # عنوان
    y = sep_y + 22
    words_per_line = 4 if W >= 1000 else 3
    for line in wrap_words(title, words_per_line)[:4]:
        h = rtext(d, ar(line), ft, W-P, y, '#f0ede8')
        y += h + max(18, H//54)

    # خط أكسنت
    d.rectangle([W-P-46, y+6, W-P, y+9], fill=accent)
    y += 30

    # ملخص
    words_body = 5 if W >= 1000 else 4
    for line in wrap_words(excerpt[:260], words_body)[:4]:
        h = rtext(d, ar(line), fb, W-P, y, '#555555')
        y += h + max(14, H//68)

    # خطورة
    if severity and severity not in ('','None'):
        sc = SEV_COLORS.get(severity, '#e8884e')
        sev_txt = ar(f'خطورة {severity}')
        if cvss and cvss not in ('','None'): sev_txt += f'  ·  CVSS {cvss}'
        sy = H - max(90, H//11)
        bw = max(220, W//4)
        bh = max(32, H//30)
        d.rounded_rectangle([P, sy, P+bw, sy+bh], radius=5, fill='#111111', outline=sc, width=1)
        d.ellipse([P+10, sy+bh//2-5, P+20, sy+bh//2+5], fill=sc)
        d.text((P+26, sy+bh//2), sev_txt, font=fh, fill=sc, anchor='lm')

    # فاصل + فوتر
    d.rectangle([P, H-46, W-P, H-45], fill='#151515')
    d.text((P, H-28), handle, font=fm, fill='#2a2a2a')
    rtext(d, date_str, fm, W-P, H-28, '#2a2a2a')

    img.save(out, 'PNG')
    return Path(out)


def make_twitter(title, category, severity, cvss, excerpt, date_str, out):
    accent = SEV_COLORS.get(severity, CAT_COLORS.get(category, '#e03c2a'))
    return make_card(title, category, severity, cvss, excerpt, date_str,
                     1080, 1080, accent, '@OffsecAR', out)

def make_linkedin(title, category, excerpt, date_str, out):
    accent = CAT_COLORS.get(category, '#4e9de8')
    return make_card(title, category, '', '', excerpt, date_str,
                     1200, 627, accent, 'linkedin.com/company/OffsecAR', out)

def make_whatsapp(title, category, excerpt, date_str, out):
    return make_card(title, category, '', '', excerpt, date_str,
                     800, 800, '#25d366', '@OffsecAR', out)

def create_blog_image_svg(title, category, slug, images_dir):
    images_dir = Path(images_dir)
    date_str = datetime.now(timezone.utc).strftime('%d %b %Y')
    make_twitter(title, category, '', '', title, date_str, images_dir/f'{slug}-tw.png')
    make_linkedin(title, category, title, date_str, images_dir/f'{slug}-li.png')
    make_whatsapp(title, category, title, date_str, images_dir/f'{slug}-wa.png')
    return images_dir/f'{slug}-tw.png'

def create_news_image_svg(headline, category, severity, cvss, images_dir, date_str):
    images_dir = Path(images_dir)
    make_twitter(headline, category, severity, cvss, headline, date_str, images_dir/f'{date_str}-tw.png')
    make_linkedin(headline, category, headline, date_str, images_dir/f'{date_str}-li.png')
    make_whatsapp(headline, category, headline, date_str, images_dir/f'{date_str}-wa.png')
    return images_dir/f'{date_str}-tw.png'
