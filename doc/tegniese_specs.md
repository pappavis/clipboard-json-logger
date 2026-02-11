# Tegniese Spesifikasie (TS) — Clipboard JSON Logger

Weergawe: v0.1.0
Datum: 11 Februarie 2026
Teikenplatform (MVP): macOS 26
Taal: Python 3.x + PyObjC
Uitsetmodus (MVP): Modus A (loose/dagboek-formaat)
Latere uitbreiding: Modus B (strict JSON)

⸻

0) Doel en beginsels

Bou ’n menu bar app wat:
	•	altyd beskikbaar is,
	•	1 klik / hotkey → genereer entry → kopieer na klembord,
	•	minimal UI, maksimum spoed,
	•	class-based, modulêr, verkieslik alles in 1 lêer vir maklike hergebruik.

⸻

1) Tegnologie-keuse

1.1 Core stack
	•	Python 3.x
	•	PyObjC om native macOS API’s te gebruik:
	•	Menu bar item: NSStatusBar / NSStatusItem
	•	Clipboard: NSPasteboard
	•	Settings: NSUserDefaults (of ’n klein JSON config op disk—maar default is NSUserDefaults)

1.2 Globale hotkey

Ons bind ’n globale hotkey via Carbon se hotkey API, beskikbaar in PyObjC se Carbon bindings.  ￼

Prakties:
	•	RegisterEventHotKey() / UnregisterEventHotKey()
	•	InstallApplicationEventHandler() vir event callback
	•	Hotkey trigger roep dieselfde “Generate Entry” aksie as die menu item.

(Alternatief later: ’n klein third-party binding soos quickmachotkey, maar MVP kan net PyObjC+Carbon doen.)  ￼

1.3 Packaging
	•	Dev-run: python app.py
	•	Build .app: py2app (klassieke pad vir PyObjC apps). PyObjC docs verwys steeds na py2app in tutorial konteks.  ￼

⸻

2) Hoëvlak-argitektuur

Een lêer (bv. clipboard_json_logger.py) met duidelike afdelings:
	1.	AppConfig (defaults + load/save)
	2.	EntryFormatter (Modus A generator)
	3.	IdService (uuid4 of short_id)
	4.	DateTimeService (YYYYMMDD)
	5.	ClipboardService (NSPasteboard write)
	6.	HotkeyService (Carbon register/unregister)
	7.	MenuBarUI (NSStatusBar menu)
	8.	AppController (orkestreer vloei, state, errors)
	9.	main() bootstrap + version banner

Belangrike beginsel: UI triggers roep altyd dieselfde controller-metode:
	•	AppController.generate_entry(copy_to_clipboard=True, with_prompt=None|str, role_override=None|str)

⸻

3) Datamodel en formate

3.1 Interne model (Python)

Gebruik ’n eenvoudige dataclass of plain class:

EntryModel velde:
	•	id: str
	•	role: str  (user / system / later assistant)
	•	prompt: str
	•	datumtijd: str (YYYYMMDD)

3.2 Uitset (MVP): Modus A (loose)

EntryFormatter.format_loose(entry: EntryModel) -> str gee ’n string wat jou dagboekstyl volg.

Normatief (MVP):
	•	Die output moet lyk soos:
	•	{'id': '...', role: 'system', prompt: """\n... \n""",\ndatumtijd: "YYYYMMDD"\n"""\n},
	•	Prompt in Modus A word altyd as “triple quote blok” uitgeskryf (selfs al is dit leeg), sodat jy altyd dieselfde struktuur het.

3.3 Modus B (later)

Hou plek in code/TS vir:
	•	EntryFormatter.format_strict_json(entry) -> str (valide JSON)
	•	Setting flag output_mode = loose_diary | strict_json

⸻

4) Konfigurasie & state

4.1 Stoorplek

Gebruik NSUserDefaults (deur Foundation.NSUserDefaults), sodat settings “net werk” sonder files.

4.2 Settings keys (NSUserDefaults)
	•	default_role: "user" (default)
	•	id_strategy: "short_id" of "uuid4"
	•	datumtijd_strategy: "date_yyyymmdd"
	•	output_mode: "loose_diary" (MVP) / "strict_json" (later)
	•	hotkey_enabled: true/false
	•	hotkey_keycode: int (virtual key code, bv. kVK_ANSI_J)
	•	hotkey_modifiers: int mask (cmd/ctrl/opt/shift)

4.3 Startup defaults

As geen defaults bestaan nie, stel:
	•	role = user
	•	id_strategy = short_id
	•	output_mode = loose_diary
	•	hotkey_enabled = true
	•	hotkey default combo: bv. ⌃⌥⌘J (kan jy later verander)

⸻

5) Dienste en implementasie-detail

5.1 ClipboardService
	•	Gebruik NSPasteboard.generalPasteboard()
	•	Clear + set string type (text)
	•	Foutafhandeling: as write fail → exception → UI notification/toast.

Verwysingspunt: PyObjC NSPasteboard setString/declareTypes is standaard patroon.  ￼

5.2 IdService

short_id
	•	Lengte: default 9 (kan 8–10 wees)
	•	Charset: abcdefghijklmnopqrstuvwxyz0123456789
	•	Generator:
	•	secrets.choice(chars) in loop
	•	Opsioneel collision-check: nie nodig vir jou dagboek, maar kan (later) ’n “recent id cache” byhou.

uuid4
	•	uuid.uuid4() string.

5.3 DateTimeService
	•	datumtijd = datetime.now(ZoneInfo("Europe/Amsterdam")).strftime("%Y%m%d")
	•	As ZoneInfo nie beskikbaar/issue: fallback datetime.now().strftime("%Y%m%d") (maar macOS 26 + Python 3.9+ behoort ZoneInfo te hê).

5.4 HotkeyService (Carbon)
	•	Register hotkey by app launch (as enabled)
	•	Unregister by exit/disable
	•	Callback roep AppController.generate_entry() (vloei A)

PyObjC Carbon API notes bevestig RegisterEventHotKey beskikbaar.  ￼
PyObjC changelog noem ook ’n HotKeyPython voorbeeld met Carbon hotkeys in AppKit context.  ￼

⸻

6) UI ontwerp (Menu bar)

6.1 NSStatusItem
	•	NSStatusBar.systemStatusBar().statusItemWithLength_(...)
	•	Set title of icon (bv. {"} of ’n klein glyph) — minimal.

6.2 Menu items en handlers

Menu:
	•	Generate Entry
	•	Generate with Prompt…
	•	Separator
	•	Role → radio items (user/system/(later assistant))
	•	Settings… (MVP kan eenvoudige dialog wees of “sub-menu” vir toggles)
	•	Quit

6.3 Prompt popup (MVP)

Eenvoudigste implementasie:
	•	NSAlert met accessory NSTextField (multi-line is meer moeite; vir MVP kan single-line of small text view)
	•	Buttons: Copy / Cancel
	•	On Copy: generate entry met prompt teks.

(As jy multi-line prompt-invoer wil van dag 1 af: gebruik NSPanel + NSTextView.)

⸻

7) Logging & Debug

7.1 Runtime debug
	•	Logger met levels: INFO/WARN/ERROR
	•	Default: INFO
	•	Logs na stdout (dev). In .app kan dit in Console app beland.
	•	Elke generate aksie log:
	•	role, id_strategy, datumtijd, output_mode

7.2 Version banner

Boonste konstantes:
	•	APP_NAME
	•	APP_VERSION
	•	APP_BUILD_DATE

⸻

8) Foutscenario’s en hantering
	•	Clipboard write fail → toon NSAlert “Clipboard error – try again”
	•	Hotkey register fail (konflik/permission) → disable hotkey en waarsku: “Hotkey conflict – change shortcut”
	•	Unexpected exception → toon generiese fout + log stack trace (dev)

⸻

9) Testing (smoke test plan)

9.1 Handmatige smoke tests
	1.	Launch app → status icon verskyn
	2.	Click “Generate Entry” → paste in editor → format korrek
	3.	Role toggle → generate → output role verander
	4.	Prompt popup → generate → prompt word in triple-quote blok geplaas
	5.	Hotkey press → clipboard updated
	6.	Quit → app exit clean (hotkey unregistered)

9.2 Output validations
	•	datumtijd is 8 chars en digits
	•	id non-empty
	•	role in allowlist
	•	Output string bevat verwagte scaffolding (bv. {'id': en datumtijd:)

⸻

10) Build & Deploy (py2app)

10.1 Dev
	•	python clipboard_json_logger.py

10.2 Build .app (hoëvlak)
	•	pip install pyobjc py2app
	•	python setup.py py2app
	•	Output: dist/ClipboardJsonLogger.app

(Die presiese setup.py inhoud skryf ek in die kodefase neer sodat jy dit 1:1 kan copy/paste.)

⸻

11) Sekuriteit & privaatheid
	•	Geen netwerk calls
	•	Geen telemetry
	•	Settings net lokaal (NSUserDefaults)
	•	Geen prompt/entries word permanent gestoor nie (net clipboard)

⸻

12) Backlog / vNext

v0.2.x
	•	Modus B strict JSON output toggle
	•	“Pretty/compact” variants
	•	Multi-line prompt editor UI (NSTextView panel)
	•	Template support (bv. ekstra velde)
	•	“Floating bubble” overlay (v2 UI)

⸻

Volgende stap opsies (kies 1)

A) Direk na kode (MVP): Ek genereer die volledige single-file Python app (class-based) met:
	•	menu bar UI,
	•	clipboard write,
	•	Modus A formatter,
	•	short_id + datumtijd,
	•	Carbon hotkey,
	•	basic settings.

B) README eerst (recruiter-proof) + daarna kode.

C) Terug na FS (as jy nog iets wil verander).

Sê net A, B, of C. (My voorstel: A — jy wil vinnig iets hê wat jy 100x per dag kan gebruik.)

# instructie.
Gaan direk na kode (MVP)
