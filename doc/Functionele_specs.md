Funksionele Spesifikasie (FS) — Clipboard JSON Logger

Weergawe: v0.1.1
Datum: 11 Februarie 2026
Primêre platform (MVP): macOS 26 (Mac mini M4)
Primêre doel: 1 klik (of hotkey) → genereer ’n dagboek-“chatlog entry” in jou loose formaat (Modus A) met ID + role + prompt + datumtyd → kopieer na klembord vir direkte plak in jou tekseditor/online dagboek.

⸻

1) Probleemstelling

Jy skryf gereeld teks in jou online dagboek en plak chat-berigte/inskrywings in ’n gestruktureerde formaat. Elke inskrywing het:
	•	’n unieke id (jy genereer dit nou handmatig),
	•	role (user/system),
	•	prompt,
	•	en ’n datum/timestamp veld.

Handmatige ID + datumtyd kos tyd en breek jou vloei. Jy wil ’n klein desktop hulpmiddel hê wat altyd beskikbaar is, en hierdie entry met 1 aksie vir jou genereer en na die klembord stuur.

⸻

2) Scope

2.1 In scope (FS v0.1.x)
	•	Genereer ’n nuwe chatlog entry volgens Modus A (loose/dagboek-formaat).
	•	Kopieer die gegenereerde entry na die klembord.
	•	UX gefokus op spoed:
	•	1 klik of globale hotkey → klaar
	•	Klein UI (MVP):
	•	menu bar app met “Generate Entry”
	•	opsionele “Generate with Prompt…” mini-venster
	•	eenvoudige Settings
	•	Instellings vir:
	•	default role
	•	ID-strategie (UUID of short id)
	•	datumtyd-strategie (YYYYMMDD)
	•	output mode (Modus A nou; Modus B later)

2.2 Buite scope (nou nie)
	•	Outomatiese stoor na lêer / cloud sync
	•	Volwaardige dagboek/notes app
	•	Parsing / import van bestaande chats
	•	Volledige “floating bubble overlay” as MVP (dit kan later as v2)

⸻

3) UX-opsies op macOS

Jy vra vir ’n “knoppie wat op die desktop sweef”. Dit is moontlik, maar tipies meer kompleks (overlay/permissions/gedrag).

FS besluit vir MVP:
	•	MVP = Menu bar app + globale hotkey (stabiel, lae friksie, altyd beskikbaar)
	•	v2 = Swewende knoppie (opsioneel later)

⸻

4) Chatlog Entry Formaat (normatief vir v0.1.1)

4.1 Output Mode — Modus A (loose/dagboek-formaat) (DEFAULT)

Die app moet entries kan uitstuur in dieselfde styl as jou dagboekvoorbeelde (nie streng JSON nie).

Voorbeeld (Modus A — loose):
```
{'id': 'efeqer3fr', role: 'system', prompt: """,
datumtijd: "20260214"
"""
},
```

Modus A reëls (must-have):
	•	Verpligte velde in elke entry:
	•	id
	•	role
	•	prompt
	•	datumtijd
	•	datumtijd formaat: YYYYMMDD (bv. "20260214").
	•	role minimum waardes: user en system (uitbreibaar later na assistant).
	•	prompt:
	•	kan leeg wees
	•	moet multi-line teks kan dra (loose styl)
	•	Entry word na klembord gekopieer as ’n teksblok.

Let wel: Modus A is doelbewus “loose” vir jou copy/paste workflow; dit is nie bedoel as JSON wat deur ’n validator moet gaan nie.

4.2 Output Mode — Modus B (Strict JSON) (LATER / NIE MVP)

Die FS moet die pad ooplaat vir ’n latere implementasie van streng JSON.

Voorbeeld (Modus B — strict JSON):
```json
{
  "id": "efeqer3fr",
  "role": "system",
  "prompt": "",
  "datumtijd": "20260214"
}
```

Modus B reëls (later):
	•	Dubbel-aanhalingstekens vir keys en strings
	•	Geen losse keys nie (alles gesiteer)
	•	prompt multi-line deur \n of ’n multi-line string, maar steeds valide JSON

⸻

5) Kerngebruikersvloei

Vloei A — Instant Generate (0 invoer)
	1.	Jy klik menu bar item Generate Entry (of druk hotkey)
	2.	App genereer ’n nuwe entry met:
	•	id (volgens huidige ID strategy)
	•	role (default role)
	•	prompt (leeg)
	•	datumtijd (vandag, YYYYMMDD)
	3.	App kopieer die entry na die klembord
	4.	App wys ’n subtiele bevestiging:
	•	“Copied entry (role=user)” of “Copied entry (role=system)”

Vloei B — Generate with Prompt…
	1.	Jy kies Generate with Prompt…
	2.	Mini popup met:
	•	role dropdown
	•	teksveld vir prompt
	•	knoppie “Copy Entry”
	3.	Klik “Copy Entry” → entry word genereer + klembord

Vloei C — Hotkey
	•	’n Globale hotkey (configurable) doen Vloei A onmiddellik.

⸻

6) Settings / Konfigurasie (v0.1.1)

6.1 Default Role
	•	user (default)
	•	system
	•	(opsioneel later) assistant

6.2 ID Strategy
	•	short_id (bv. 8–10 alfanumeriese chars, soos efeqer3fr) of
	•	uuid4 (standaard UUID v4 formaat)

FS vereiste: Die app moet albei kan, en jy kies ’n default in Settings.

6.3 Datum/Tyd Strategy
	•	date_yyyymmdd (default) → bv. "20260214"
	•	(opsioneel later) iso_datetime_local (as jy later tyd + offset wil hê)

6.4 Output Mode
	•	loose_diary (Modus A) (default)
	•	strict_json (Modus B) (later implementering)

6.5 Hotkey
	•	Enable/disable
	•	Stel key combo (konflik-detect moet foutboodskap gee)

⸻

7) UI vereistes (MVP)

7.1 Menu bar UI
	•	Status icon in menu bar
	•	Menu items:
	•	Generate Entry (kopieer na klembord)
	•	Generate with Prompt…
	•	Role → (radio: user / system / (later assistant))
	•	Settings…
	•	Quit

7.2 v2: Floating bubble (opsioneel later)
	•	Always-on-top mini-knoppie
	•	Sleepbaar
	•	Klik = Generate Entry
	•	Regsklik = menu (role/settings)

⸻

8) Nie-funksionele vereistes
	•	Latency: klik → klembord < 100ms (gevoelensmatig onmiddellik)
	•	Betroubaarheid: geen crashes; herprobeer op interne fout
	•	Privaatheid: geen netwerk; geen data stoor op disk (tensy later eksplisiet gevra)
	•	Distribusie: moet as ’n klein app kan run (ideaal .app); dev run mag via Python
	•	Onderhoudbaarheid: modulêr, class-based; (verkieslik) alles in 1 lêer vir redistribusie

⸻

9) Functional Handleiding (gebruikerskant)

Doel-werkvloei (bedoelde eindtoestand)
	1.	App start saam met macOS (opsioneel)
	2.	Jy werk in jou editor / dagboek
	3.	Wanneer jy ’n nuwe inskrywing wil maak:
	•	hotkey of menu bar → Generate Entry
	4.	Plak (Cmd+V) in jou editor
	5.	Tik jou inhoud in prompt (of gebruik “Generate with Prompt…”)

⸻

10) Foutafhandeling
	•	Clipboard nie beskikbaar → “Clipboard error – try again”
	•	Hotkey registrasie faal (konflik) → “Hotkey conflict – change shortcut”
	•	ID/datumtyd generasie faal (onwaarskynlik) → “Internal error – regenerated”

⸻

11) Ontwikkelproses en navigasie tussen fases

Hierdie projek werk in fases; jy kan altyd terugstap:

Stap 1 — FS (hierdie dokument)

Opsies:
	•	(1) Verfyn FS
	•	(2) Gaan aan na TS

Stap 2 — TS (volgende)

TS moet elke FS-item “trace” na implementasie: modules, classes, UI, clipboard, hotkey, packaging, logging.

Einde-van-TS opsies (moet altyd aangebied word):
	•	(A) Maak README (publiek/recruiter-proof)
	•	(B) Bou direk die kode (MVP)
	•	(C) Terug na FS
	•	(D) Voeg ekstra verfynings by (bv. Modus B strict JSON, floating bubble, templates, ens.)

⸻

Volgende stap: TS

Jy het FS v0.1.1 aanvaar, insluitend Modus A as default en Modus B later.

Ek gaan nou aan na die Tegniese Spesifikasie (TS) en ek gaan dit so skryf dat dit:
	•	class-based is,
	•	modulêr is,
	•	en mik na “alles-in-een-lêer” kode vir die MVP.
