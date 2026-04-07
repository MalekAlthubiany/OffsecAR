#!/usr/bin/env python3
"""OffsecAR — تيليقرام: نفس المحتوى كاملاً مع الصورة"""

import os, requests
from pathlib import Path
from datetime import datetime, timezone
from image_generator import make_advisory

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID   = os.environ["TELEGRAM_CHAT_ID"]
POSTS_DIR  = Path("_posts")
BLOGS_DIR  = Path("_blogs")
SITE_URL   = "https://malekalthubiany.github.io/OffsecAR"
TMP        = Path("/tmp/offsec_imgs")
TMP.mkdir(exist_ok=True)


def tg(text: str):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text,
              "parse_mode": "HTML", "disable_web_page_preview": True}
    )

def tg_photo(img_path: Path, caption: str = ""):
    if not img_path.exists():
        return
    with open(img_path, "rb") as f:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
            data={"chat_id": TELEGRAM_CHAT_ID,
                  "caption": caption[:1024] if caption else "",
                  "parse_mode": "HTML"},
            files={"photo": f}
        )

def tg_doc(img_path: Path):
    """يرسل الصورة بجودة كاملة كـ document"""
    if not img_path.exists():
        return
    with open(img_path, "rb") as f:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument",
            data={"chat_id": TELEGRAM_CHAT_ID},
            files={"document": f}
        )

def parse_fm(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---"): return {}
    parts = raw.split("---", 2)
    if len(parts) < 3: return {}
    fm = {}
    for line in parts[1].strip().split("\n"):
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"\'')
    fm["_body"] = parts[2].strip()
    return fm

def get_todays_files():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    posts = sorted(POSTS_DIR.glob(f"{today}-*.md")) if POSTS_DIR.exists() else []
    blogs = sorted(BLOGS_DIR.glob(f"{today}-*.md")) if BLOGS_DIR.exists() else []
    return posts, blogs, today

def post_url(date_str, stem):
    slug = stem[11:] if len(stem) > 11 else stem
    y, m, d = date_str.split("-")
    return f"{SITE_URL}/{y}/{m}/{d}/{slug}/"

def blog_url(slug):
    return f"{SITE_URL}/blogs/{slug}/"


def send_item(title, category, severity, cvss, cve, body,
              source_url, url, img_path, idx, total, kind="خبر"):
    """يرسل عنصراً واحداً — صورة + نص Twitter + LinkedIn + WhatsApp"""

    # ── توليد الصورة ──
    sev_val = severity if severity and severity not in ("","None") else "غير محددة"
    cvss_val = cvss if cvss and cvss not in ("","None") else ""
    try:
        make_advisory(
            title, category, sev_val, cvss_val, cve,
            body[:300],  # وصف مختصر في الحقل المخصص
            body,        # المحتوى الكامل في التفاصيل
            'آخر إصدار', 'تحديث فوري مطلوب',
            'تنفيذ أوامر', 'وصول غير مصرح',
            'الشبكة', 'بدون مصادقة',
            datetime.now(timezone.utc).strftime('%Y-%m-%d'),
            f"OFFSEC-{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            img_path
        )
    except Exception as e:
        print(f"   ⚠️ صورة: {e}")

    # ── فاصل ──
    tg(f"━━━━━━━━━━━━━━━━━━━━\n"
       f"{'📰' if kind == 'خبر' else '📝'} <b>{kind} {idx}/{total}</b>\n"
       f"━━━━━━━━━━━━━━━━━━━━")

    # ── ١. الصورة (جودة كاملة) ──
    tg_doc(img_path)

    # ── ٢. Twitter / X ──
    tw = (
        f"{title}\n\n"
        + (f"الخطورة: {sev_val}" + (f"  |  CVSS {cvss_val}" if cvss_val else "") + "\n\n" if sev_val != "غير محددة" else "")
        + body
        + (f"\n\nالمصدر: {source_url}" if source_url and source_url not in ("","None") else "")
        + f"\n\n{url}"
    )
    tg(f"<b>🐦 Twitter / X</b>\n\n<code>{tw[:4000]}</code>")

    # ── ٣. LinkedIn ──
    li = (
        f"{title}\n\n"
        + (f"الخطورة: {sev_val}" + (f"  |  CVSS {cvss_val}" if cvss_val else "") + "\n\n" if sev_val != "غير محددة" else "")
        + body
        + (f"\n\nالمصدر: {source_url}" if source_url and source_url not in ("","None") else "")
        + f"\n\n{url}"
        + "\n\nOffsecAR — الأمن الهجومي بالعربي"
    )
    tg(f"<b>💼 LinkedIn</b>\n\n<code>{li[:4000]}</code>")

    # ── ٤. WhatsApp ──
    wa = (
        f"*{title}*\n\n"
        + (f"الخطورة: {sev_val}" + (f"  |  CVSS {cvss_val}" if cvss_val else "") + "\n\n" if sev_val != "غير محددة" else "")
        + body
        + (f"\n\nالمصدر: {source_url}" if source_url and source_url not in ("","None") else "")
        + f"\n\n{url}"
        + "\n\nOffsecAR"
    )
    tg(f"<b>💬 WhatsApp</b>\n\n<code>{wa[:4000]}</code>")


def main():
    posts, blogs, today = get_todays_files()

    if not posts and not blogs:
        tg(f"⚠️ لا يوجد محتوى جديد اليوم ({today})")
        return

    tg(f"🌅 <b>OffsecAR · {today}</b>\n\n"
       f"📰 أخبار: {len(posts)}  |  📝 مقالات: {len(blogs)}")

    for i, p in enumerate(posts, 1):
        fm = parse_fm(p)
        if not fm: continue
        img = TMP / f"news_{i}.png"
        send_item(
            title      = fm.get("title",""),
            category   = fm.get("category",""),
            severity   = fm.get("severity",""),
            cvss       = fm.get("cvss",""),
            cve        = fm.get("cve",""),
            body       = fm.get("_body",""),
            source_url = fm.get("source_url",""),
            url        = post_url(today, p.stem),
            img_path   = img,
            idx=i, total=len(posts), kind="خبر"
        )

    for i, b in enumerate(blogs, 1):
        fm = parse_fm(b)
        if not fm: continue
        img = TMP / f"blog_{i}.png"
        send_item(
            title      = fm.get("title",""),
            category   = fm.get("category",""),
            severity   = "",
            cvss       = "",
            cve        = "",
            body       = fm.get("_body",""),
            source_url = "",
            url        = blog_url(fm.get("slug", b.stem)),
            img_path   = img,
            idx=i, total=len(blogs), kind="مقالة"
        )

    tg(f"✅ <b>انتهى محتوى اليوم</b>\n{SITE_URL}")
    print("✅ تم!")


if __name__ == "__main__":
    main()
