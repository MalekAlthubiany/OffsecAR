#!/usr/bin/env python3
"""
OffsecAR — مرسل التيليقرام
يرسل يومياً محتوى منسق وجاهز للنسخ واللصق
"""

import os, re, requests
from pathlib import Path
from datetime import datetime, timezone

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID   = os.environ["TELEGRAM_CHAT_ID"]
POSTS_DIR  = Path("_posts")
BLOGS_DIR  = Path("_blogs")
SITE_URL   = "https://malekalthubiany.github.io/OffsecAR"


def tg(text: str):
    """يرسل رسالة تيليقرام"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    r = requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    })
    if not r.ok:
        print(f"⚠️ {r.text[:200]}")


def parse_fm(path: Path) -> dict:
    """يقرأ front matter"""
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---"):
        return {}
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {}
    fm = {}
    for line in parts[1].strip().split("\n"):
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"').strip("'")
    fm["_body"] = parts[2].strip()
    return fm


def get_todays_files():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    posts = sorted(POSTS_DIR.glob(f"{today}-*.md")) if POSTS_DIR.exists() else []
    blogs = sorted(BLOGS_DIR.glob(f"{today}-*.md")) if BLOGS_DIR.exists() else []
    return posts, blogs, today


def post_site_url(date_str: str, stem: str) -> str:
    slug = stem[11:] if len(stem) > 11 else stem
    y, m, d = date_str.split("-")
    return f"{SITE_URL}/{y}/{m}/{d}/{slug}/"


def blog_site_url(slug: str) -> str:
    return f"{SITE_URL}/blogs/{slug}/"


def send_news(fm: dict, date_str: str, stem: str, idx: int, total: int):
    title      = fm.get("title", "")
    category   = fm.get("category", "")
    severity   = fm.get("severity", "")
    cvss       = fm.get("cvss", "")
    source_url = fm.get("source_url", "")
    source     = fm.get("source", "")
    body       = fm.get("_body", "")
    excerpt    = body[:350].replace("<", "&lt;").replace(">", "&gt;")
    site_url   = post_site_url(date_str, stem)

    sev_line = ""
    if severity and severity not in ("", "None"):
        sev_line = f"⚠️ خطورة {severity}"
        if cvss and cvss not in ("", "None"):
            sev_line += f"  ·  CVSS {cvss}"

    # ── رسالة الخبر الكاملة ──
    msg = (
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📰 <b>خبر {idx}/{total}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>{title}</b>\n\n"
        f"🗂 {category}"
        + (f"\n{sev_line}" if sev_line else "")
        + f"\n\n{excerpt}{'...' if len(body) > 350 else ''}\n\n"
        + (f"🌐 المصدر: {source_url}\n" if source_url and source_url not in ("", "None") else "")
        + f"🔗 موقعنا: {site_url}"
    )
    tg(msg)

    # ── نص تويتر ──
    sev_icon = {"حرجة": "🔴", "عالية": "🟠", "متوسطة": "🟡"}.get(severity, "🔵")
    tw = (
        f"{'🔴' if sev_line else '📌'} {title}\n\n"
        + (f"{sev_line}\n\n" if sev_line else "")
        + f"{body[:200]}...\n\n"
        f"🔗 {site_url}\n\n"
        f"#أمن_المعلومات #OffsecAR #RedTeam #Cybersecurity"
    )
    tg(f"🐦 <b>Twitter / X — انسخ والصق:</b>\n\n<code>{tw[:900]}</code>")

    # ── نص لينكدإن ──
    li = (
        f"📢 {title}\n\n"
        f"{body[:400]}{'...' if len(body) > 400 else ''}\n\n"
        + (f"التصنيف: {category}\n" if category else "")
        + f"🔗 التحليل الكامل: {site_url}\n\n"
        f"OffsecAR — أخبار الأمن الهجومي بالعربي يومياً\n"
        f"#أمن_المعلومات #OffsecAR #CyberSecurity #RedTeam"
    )
    tg(f"💼 <b>LinkedIn — انسخ والصق:</b>\n\n<code>{li[:1000]}</code>")

    # ── نص واتساب ──
    wa = (
        f"*{title}*\n\n"
        f"{body[:300]}{'...' if len(body) > 300 else ''}\n\n"
        f"📎 {site_url}\n\n"
        f"_OffsecAR — يومية الأمن الهجومي بالعربي_"
    )
    tg(f"💬 <b>WhatsApp — انسخ والصق:</b>\n\n<code>{wa[:800]}</code>")


def send_blog(fm: dict, idx: int, total: int):
    title     = fm.get("title", "")
    category  = fm.get("category", "")
    read_time = fm.get("read_time", "")
    excerpt   = fm.get("excerpt", "")
    slug      = fm.get("slug", "")
    body      = fm.get("_body", "")
    text      = excerpt if excerpt else body[:350]
    site_url  = blog_site_url(slug)

    # ── رسالة المقالة الكاملة ──
    msg = (
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 <b>مقالة {idx}/{total}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>{title}</b>\n\n"
        f"🗂 {category}"
        + (f"  ·  ⏱ {read_time} دقائق" if read_time else "")
        + f"\n\n{text[:400]}{'...' if len(text) > 400 else ''}\n\n"
        f"🔗 {site_url}"
    )
    tg(msg)

    # ── نص تويتر ──
    tw = (
        f"📌 {title}\n\n"
        f"{text[:200]}...\n\n"
        f"🔗 {site_url}\n\n"
        f"#أمن_المعلومات #OffsecAR #RedTeam"
    )
    tg(f"🐦 <b>Twitter / X — انسخ والصق:</b>\n\n<code>{tw[:900]}</code>")

    # ── نص لينكدإن ──
    li = (
        f"📢 {title}\n\n"
        f"{text[:400]}{'...' if len(text) > 400 else ''}\n\n"
        f"التصنيف: {category}\n"
        f"🔗 اقرأ المقالة كاملة: {site_url}\n\n"
        f"OffsecAR — أخبار الأمن الهجومي بالعربي يومياً\n"
        f"#أمن_المعلومات #OffsecAR #CyberSecurity"
    )
    tg(f"💼 <b>LinkedIn — انسخ والصق:</b>\n\n<code>{li[:1000]}</code>")

    # ── نص واتساب ──
    wa = (
        f"*{title}*\n\n"
        f"{text[:300]}{'...' if len(text) > 300 else ''}\n\n"
        f"📎 {site_url}\n\n"
        f"_OffsecAR — يومية الأمن الهجومي بالعربي_"
    )
    tg(f"💬 <b>WhatsApp — انسخ والصق:</b>\n\n<code>{wa[:800]}</code>")


def main():
    posts, blogs, today = get_todays_files()

    if not posts and not blogs:
        tg(f"⚠️ لا يوجد محتوى جديد اليوم ({today})")
        return

    # ── رسالة الترحيب ──
    tg(
        f"🌅 <b>OffsecAR · {today}</b>\n\n"
        f"📰 أخبار اليوم: {len(posts)}\n"
        f"📝 مقالات اليوم: {len(blogs)}\n\n"
        f"انسخ أي نص والصقه مباشرة 👇"
    )

    # ── الأخبار ──
    if posts:
        for i, p in enumerate(posts, 1):
            fm = parse_fm(p)
            if fm:
                send_news(fm, today, p.stem, i, len(posts))

    # ── المقالات ──
    if blogs:
        for i, b in enumerate(blogs, 1):
            fm = parse_fm(b)
            if fm:
                send_blog(fm, i, len(blogs))

    tg(f"✅ <b>انتهى محتوى اليوم</b>\n🔗 {SITE_URL}")
    print("✅ تم!")


if __name__ == "__main__":
    main()
