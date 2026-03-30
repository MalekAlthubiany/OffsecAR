---
layout: blog
title: "Burp Suite: ميزات متقدمة لا يستخدمها معظم محللي الثغرات الأمنية"
date: 2026-03-30T06:29:51Z
category: "أداة"
excerpt: "Burp Suite ليس مجرد Proxy للاعتراض. معظم المختصين يستخدمون 20% فقط من قدراته الحقيقية. في هذه المقالة، نكشف ميزات متقدمة تحول Burp من أداة Interception بسيطة إلى منصة متكاملة للـ Offensive Security، من Macro Automation إلى Turbo Intruder والـ Collaborator Client."
read_time: 7
tags: ["Burp Suite", "Web Security", "Penetration Testing", "OWASP", "Bug Bounty"]
slug: "burp-suite-advanced"
---

## Burp Macros: أتمتة الـ Multi-Step Attacks

أحد أكبر التحديات في Web Pentesting هو التعامل مع التطبيقات التي تتطلب خطوات متعددة قبل الوصول للـ Endpoint المستهدف. الـ Macros في Burp تحل هذه المشكلة بأناقة.

الـ Macro يسمح لك بتسجيل سلسلة من الـ Requests وإعادة تشغيلها تلقائيًا. مثلاً، إذا كان التطبيق يتطلب CSRF token جديد مع كل Request، يمكنك إنشاء Macro يستخرج الـ Token من صفحة معينة ويحقنه تلقائيًا.

لإنشاء Macro فعّال:
1. اذهب إلى `Settings > Sessions > Session Handling Rules`
2. أضف Rule جديدة واختر `Run a macro`
3. سجل الـ Requests المطلوبة (Login + Token fetch مثلاً)
4. استخدم `Custom parameter locations` لاستخراج القيم الديناميكية
5. حدد الـ Scope الذي تنطبق عليه القاعدة

هذه الميزة أساسية عند استخدام Intruder أو Repeater ضد تطبيقات معقدة. بدلاً من التحديث اليدوي للـ Tokens، يعمل Burp بشكل مستقل تماماً.

## Turbo Intruder: السرعة الخارقة للـ Race Conditions

الـ Intruder المدمج في Burp بطيء بشكل مقصود في النسخة المجانية. لكن Turbo Intruder Extension يغير قواعد اللعبة.

هذه الأداة مكتوبة بـ Python وتستخدم HTTP/2 Connection Pooling لإرسال آلاف الـ Requests في ثوانٍ. مثالية لاكتشاف Race Conditions والـ Rate Limit Bypasses.

مثال عملي لاختبار Race Condition في Coupon Code:

```python
def queueRequests(target, wordlists):
    engine = RequestEngine(endpoint=target.endpoint,
                          concurrentConnections=50,
                          requestsPerConnection=100,
                          pipeline=False)
    
    # إرسال 500 Request متزامن
    for i in range(500):
        engine.queue(target.req, gate='race1')
    
    # تحرير الـ Requests دفعة واحدة
    engine.openGate('race1')

def handleResponse(req, interesting):
    if '"success":true' in req.response:
        table.add(req)
```

هذا الكود يرسل 500 Request في نفس اللحظة تقريباً، مما يزيد فرص استغلال Race Conditions بشكل كبير.

## Collaborator Client: الكشف عن Out-of-Band Vulnerabilities

الـ Burp Collaborator ليس فقط للـ SSRF البسيط. معظم المختصين لا يستخدمون Collaborator Client للتحليل المتقدم.

افتح Collaborator Client من `Burp > Burp Collaborator client` واحصل على Payload. لكن الميزة الخفية هي Polling API:

```python
import requests
import time

# استخدم Collaborator من خلال API
collaborator_url = "https://your-subdomain.burpcollaborator.net"

while True:
    # حقن الـ Payload في أماكن مختلفة
    # مثلاً في Headers, JSON, XML
    
    time.sleep(30)
    # افحص الـ Interactions
    # HTTP requests, DNS lookups, SMTP connections
```

يمكنك استخدام هذا لكشف:
- Blind SSRF في Background Jobs
- XML External Entity (XXE) في Async Processing
- Server-Side Template Injection مع Delayed Execution
- Log4Shell والـ JNDI Injection

الميزة الذهبية: Collaborator يسجل DNS, HTTP, SMTP interactions، مما يعني اكتشاف ثغرات لا تظهر في الـ Response مباشرة.

## Match and Replace: التلاعب الذكي بالـ Traffic

هذه الميزة في `Settings > Match and Replace` تسمح بتعديل تلقائي لكل Request أو Response يمر عبر Burp.

حالات استخدام قوية:

**1. Bypassing WAF Headers:**
```
Type: Request header
Match: ^$
Replace: X-Forwarded-For: 127.0.0.1
```

**2. Automatic Header Injection:**
```
Type: Request header
Match: ^$
Replace: X-Custom-IP-Authorization: 127.0.0.1
```

**3. Content-Type Manipulation:**
```
Type: Request header
Match: Content-Type: application/json
Replace: Content-Type: application/xml
```

**4. Response Modification للـ Client-Side Bypasses:**
```
Type: Response body
Match: role":"user"
Replace: role":"admin"
```

هذا يحول Burp إلى MITM Proxy ذكي يطبق Transformations معقدة بشكل تلقائي، موفراً ساعات من العمل اليدوي.

## Logger++: التحليل المتقدم للـ HTTP Traffic

Logger++ Extension يتجاوز بكثير الـ HTTP History المدمج. يوفر Filtering متقدم، Regular Expressions، وتصدير بصيغ متعددة.

أهم الميزات:
- **Regex Filters**: ابحث عن Patterns معقدة في Requests/Responses
- **Custom Columns**: أضف عمود يستخرج JWT Claims مثلاً
- **Export to SQLite**: حلل الـ Traffic باستخدام SQL queries
- **Color Coding**: ميز الـ Requests حسب Status Codes أو Content Types

مثال Filter متقدم:
```
Request.Path CONTAINS "api" 
AND Response.Body CONTAINS_REGEX "[a-zA-Z0-9]{40}"
AND Response.Status == 200
```

هذا يكشف API Endpoints التي قد تسرب Tokens أو Secrets في Responses.

## الخلاصة

Burp Suite منجم ذهب من الميزات المخفية. Macros للأتمتة، Turbo Intruder للسرعة، Collaborator للـ Out-of-Band Detection، Match and Replace للتلاعب الذكي، وLogger++ للتحليل العميق.

الفرق بين Pentester مبتدئ ومتقدم ليس في الأدوات، بل في معرفة كل زاوية فيها. استثمر وقتاً في استكشاف هذه الميزات، وستجد نفسك تكتشف ثغرات كانت مخفية عن الآخرين.
