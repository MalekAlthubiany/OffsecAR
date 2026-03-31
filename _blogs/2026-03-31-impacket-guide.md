---
layout: blog
title: "Impacket: السكاكين السويسرية للـ Red Team في بيئات Active Directory"
date: 2026-03-31T06:17:37Z
category: "أداة"
excerpt: "في عالم الـ Offensive Security، تُعتبر Impacket من أكثر المكتبات قيمة عند اختبار بيئات Windows و Active Directory. مجموعة أدوات Python توفر لك كل ما تحتاجه لتنفيذ هجمات متقدمة بدون الحاجة لرفع ملفات تنفيذية على الهدف. دعنا نغوص في تفاصيل هذه الأداة التي لا غنى عنها لأي Red Teamer محترف."
read_time: 8
tags: ["Impacket", "Active Directory", "Red Team", "Lateral Movement", "Kerberos"]
slug: "impacket-guide"
---

## ما هي Impacket ولماذا تهم؟

Impacket هي مجموعة من Python classes للعمل مع network protocols. طورها SecureAuth Corporation وأصبحت المرجع الأول عند التعامل مع بروتوكولات Windows. ما يميزها أنها pure Python implementation، مما يعني أنك لا تحتاج لرفع binaries مشبوهة على النظام المستهدف.

الأداة تدعم بروتوكولات حيوية مثل SMB، MSRPC، NTLM، Kerberos، وغيرها. هذا يفتح أمامك إمكانيات هائلة: من credential dumping إلى lateral movement، مرورًا بـ privilege escalation. كل هذا بأدوات جاهزة ومُختبرة في عمليات حقيقية.

## الأدوات الأساسية في ترسانة Impacket

### psexec.py: البوابة الكلاسيكية

أداة psexec هي النسخة المطورة من PsExec الشهيرة. تسمح لك بتنفيذ commands على أنظمة بعيدة باستخدام credentials صالحة:

```bash
psexec.py domain/user:password@target
```

ما يميزها أنها تدعم Pass-the-Hash مباشرة:

```bash
psexec.py -hashes :NTHASH domain/user@target
```

لا حاجة لمعرفة الـ plaintext password. فقط الـ NTLM hash يكفي.

### secretsdump.py: منجم الذهب

هذه الأداة تستخرج credentials من أنظمة Windows بطرق متعددة. يمكنها dump الـ SAM database، LSA secrets، وحتى NTDS.dit من Domain Controllers:

```bash
secretsdump.py domain/user:password@dc-ip
```

الناتج يعطيك NTLM hashes لجميع حسابات الـ domain. في عمليات Red Team، هذه اللحظة تُعتبر game changer. من هنا يبدأ lateral movement الحقيقي.

### GetNPUsers.py: AS-REP Roasting

تستغل هذه الأداة حسابات الـ domain التي لا تتطلب Kerberos pre-authentication:

```bash
GetNPUsers.py domain/ -usersfile users.txt -dc-ip 10.10.10.10
```

أي حساب بخاصية "DONT_REQ_PREAUTH" سيُعيد TGT يمكن cracking-ه offline. غالبًا ما تجد service accounts قديمة بهذا الإعداد.

### GetUserSPNs.py: Kerberoasting المُتقن

Kerberoasting من أشهر تقنيات credential theft في بيئات Active Directory:

```bash
GetUserSPNs.py domain/user:password -dc-ip 10.10.10.10 -request
```

الأداة تطلب Service Tickets لحسابات بـ SPNs مُسجلة، ثم تحفظها بصيغة hashcat-ready. service accounts عادة تملك passwords قوية، لكن ليس دائمًا.

## سيناريوهات عملية من الميدان

### السيناريو الأول: من User عادي إلى Domain Admin

تخيل أنك حصلت على credentials لـ user عادي في الـ domain. الخطوة الأولى: enumeration.

```bash
# استخراج قائمة المستخدمين
lookupsid.py domain/user:password@dc-ip

# البحث عن SPNs قابلة للـ Kerberoast
GetUserSPNs.py domain/user:password -dc-ip dc-ip

# Crack الـ hash
hashcat -m 13100 spn.hash wordlist.txt
```

بمجرد حصولك على service account credentials، استخدم secretsdump:

```bash
secretsdump.py domain/serviceaccount:password@dc-ip
```

إذا كان الـ service account يملك صلاحيات replication (DCSync)، ستحصل على كل hashes الـ domain بما فيها Administrator.

### السيناريو الثاني: Pass-the-Hash Relay

عندما لا تستطيع crack الـ hash، استخدمه مباشرة:

```bash
# استخدام wmiexec بدلاً من psexec (أقل noise)
wmiexec.py -hashes :NTHASH domain/user@target
```

أداة wmiexec تستخدم WMI للتنفيذ، مما يُقلل من IOCs المُسجلة في Event Logs.

## نصائح OPSEC والتخفي

رغم قوة Impacket، استخدامها يترك آثارًا. بعض النصائح:

**1. استخدم smbexec بدلاً من psexec عند الحاجة**

smbexec لا يرفع service جديد، بل يستخدم scheduled tasks. أقل وضوحًا في الـ logs.

**2. تجنب secretsdump على production DCs**

استخدم DCSync بدلاً من volume shadow copies عندما يكون ممكنًا:

```bash
secretsdump.py -just-dc-ntlm domain/user@dc-ip
```

الـ flag `-just-dc-ntlm` يُقلل من الـ noise.

**3. استخدم الـ Kerberos authentication بدلاً من NTLM**

مع الـ flag `-k`، تستخدم Impacket Kerberos tickets بدلاً من NTLM:

```bash
psexec.py -k -no-pass domain/user@target.domain.local
```

هذا يتطلب إعداد DNS و `/etc/hosts` بشكل صحيح، لكنه أقل إثارة للشبهات.

## الخلاصة: لماذا Impacket ضرورية؟

في كل engagement تقريبًا على بيئة Windows/AD، ستجد نفسك تعود لـ Impacket. مرونتها، استقرارها، ودعمها لتقنيات متقدمة يجعلها أداة لا غنى عنها.

الجمال في Impacket أنها أكثر من مجرد exploitation tools. إنها تعليمية أيضًا. قراءة الـ source code يعلمك كيف تعمل Windows protocols من الداخل. هذا الفهم العميق هو ما يُميز Red Teamer محترف عن script kiddie.

ابدأ بالأدوات الأساسية، افهم كيف تعمل، ثم استكشف الـ 30+ أداة الأخرى في المجموعة. كل واحدة منها حل لمشكلة محددة ستواجهها في الميدان.
