# Functional Specification (FS) — Clipboard JSON Logger
**Version:** 0.4 (FS v0.4.0)  
**Date:** 2026-02-18  
**Platform:** macOS (menu bar app)  
**Primary user:** single-user local workflow (Michiel)  
**Core promise:** 1 action → generate a “chatlog entry” snippet → copied to clipboard → paste into editor

---

## 0. Sanity check (FS v0.4 completeness)
Hier is die **volledige FS v0.4** as een dokument (geen weggelate afdelings).  
FS v0.4 **behou alle v0.2/v0.3 funksies** en voeg **Overlay Bubble (Floating Button)** by.

### Funksies wat ingesluit is (moet alles in hierdie FS wees)
- Menu bar app (LSUIElement; geen Dock icon)
- Clipboard copy van gegenereerde entry
- Entry velde: `id`, `role`, `prompt`, `datumtijd`
- ID strategie: `short_id` (default) of `uuid4`
- `datumtijd` formaat: `YYYYMMDD` (timezone-aware best-effort; default Europe/Amsterdam)
- Output modes:
  - Modus A (Loose diary / “loose JSON-ish diary format”) **default**
  - Modus B (Strict JSON) **toggle**
  - Modus B “pretty JSON” **toggle**
- Rol: default role `user`/`system` + quick switch
- Prompt panel: multiline prompt invoer + role override
- Notifications (best-effort) + policy: **All / Hotkey only / Off**
- Global hotkey (best-effort Carbon) + **hotkey capture UI** + enable/disable + reset
- Settings panel vir: hotkey enabled, hotkey capture/apply/reset, notifications mode, pretty JSON toggle
- Overlay Bubble (v0.4):
  - enable/disable
  - draggable + position persistence
  - always-on-top
  - click action: generate blank **of** open prompt panel
  - right-click context menu
  - show on all Spaces toggle
  - hide in fullscreen toggle

✅ Alles hierbo word **spesifiek** in hierdie FS v0.4 gedek.

---

## 1. Scope
### 1.1 In scope (v0.4)
’n macOS menu bar utility wat:
1) ’n entry-model genereer met standaard velde,  
2) dit formateer (Modus A of B),  
3) dit na die macOS clipboard skryf,  
4) opsioneel ’n notification wys,  
5) opsioneel via hotkey trigger,  
6) opsioneel via Overlay Bubble trigger.

### 1.2 Out of scope (v0.4)
- Sync na cloud / iCloud / Dropbox
- Outbox / history / browsing van vorige entries
- Multi-user accounts
- Enkripsie of secrets vault
- Editor integrasies (Obsidian/Notion API) — slegs clipboard
- Auto-detect van “role” uit bronteks
- Parsing of validasie van jou dagboekformaat buite Modus B strict JSON

---

## 2. Goals & non-goals
### 2.1 Goals
- Minimal friction: **1 klik** of **1 hotkey** → clipboard entry gereed.
- Betroubaarheid: geen crashes as optional frameworks ontbreek nie (Carbon / UserNotifications).
- Persistent settings: gebruikersvoorkeure bly oor herstarts.
- Vinnig: “generate + copy” in < 100ms tipies.
- Modus A bly default; Modus B is ’n toggle (strict JSON).

### 2.2 Non-goals
- Kompleks UI (tabbed preferences, multi-window flows) — hou klein.
- “Perfect” JSON vir Modus A — Modus A is doelbewus los/diary-agtig.
- 100% perfekte hotkey support op alle macOS weergawes — best-effort.

---

## 3. User workflow (happy paths)
### 3.1 Menu bar → Generate Entry
1. User klik status item in menu bar.
2. Kies **Generate Entry**.
3. App genereer entry met default role + blank prompt.
4. App kopieer output na clipboard.
5. Opsioneel notification volgens policy.

### 3.2 Menu bar → Generate with Prompt…
1. User kies **Generate with Prompt…**
2. Multiline panel open (role dropdown + text input).
3. User tik prompt, kies role (optional).
4. Klik **Copy Entry**
5. App kopieer output na clipboard + opsioneel notification.

### 3.3 Hotkey → Generate Entry
1. User druk global hotkey.
2. App genereer blank prompt entry.
3. App kopieer output na clipboard.
4. Notification policy “Hotkey only” moet dit wys; “Off” nie.

### 3.4 Overlay Bubble → Primary click
1. Overlay is enabled.
2. User klik bubble.
3. Action volgens instelling:
   - Generate blank entry **of**
   - Open prompt panel
4. Clipboard word gevul; notification volgens policy.

### 3.5 Overlay Bubble → Drag
1. User drag bubble.
2. Bubble beweeg en snap nie noodwendig (v0.4).
3. Op mouse-up: posisie word gestoor.

---

## 4. Data model
### 4.1 Entry model fields
Elke entry bestaan uit:
- `id` (string)  
- `role` (string: `"user"` of `"system"`)  
- `prompt` (string; kan multiline wees)  
- `datumtijd` (string: `"YYYYMMDD"`)

### 4.2 Default values
- default role: `"user"`
- default output mode: Modus A (loose diary)
- default ID strategy: short_id (length ~9)
- default timezone: `"Europe/Amsterdam"`
- default notifications policy: `"hotkey_only"`
- default hotkey: Ctrl+Opt+Cmd+J (best-effort)

---

## 5. Output formats
### 5.1 Modus A — Loose diary format (default)
- Doel: mens-leesbaar, pas by jou dagboekstyle.
- Nie noodwendig geldige JSON nie.
- Vorm (voorbeeld):

```text
{'id': 'efeqer3fr', role: 'system', prompt: """
Hello
multi-line
"""
,
datumtijd: "20260214"
},

5.2 Modus B — Strict JSON format (toggle)
	•	Doel: geldige JSON vir tooling / parsing.
	•	Opsioneel “pretty” indent.
	•	Vorm (voorbeeld):

{
  "id": "efeqer3fr",
  "role": "system",
  "prompt": "Hello\nmulti-line",
  "datumtijd": "20260214"
}


⸻

6. Settings & persistence

6.1 Storage
	•	Alle settings word lokaal gestoor via macOS user defaults (NSUserDefaults).
	•	Geen netwerk calls.
	•	Geen telemetrie.

6.2 Settings list (functional)

Core
	•	Default role: user|system
	•	Output mode: loose_diary|strict_json
	•	Strict JSON pretty: true|false
	•	ID strategy: short_id|uuid4
	•	datumtijd strategy: (v0.4: date_yyyymmdd)

Notifications
	•	Notifications policy: all|hotkey_only|off

Hotkey
	•	Hotkey enabled: true|false
	•	Hotkey keycode + modifiers (Carbon mask) (best-effort)

Overlay Bubble (v0.4)
	•	Overlay enabled: true|false
	•	Overlay click action: generate_blank|open_prompt_panel
	•	Show on all Spaces: true|false
	•	Hide in fullscreen: true|false
	•	Saved position: x,y (+ optional screen index best-effort)

⸻

7. UI requirements

7.1 Menu bar item
	•	Status bar icon/text minimal (bv { }).
	•	Menu items:
	•	Generate Entry
	•	Generate with Prompt…
	•	Role submenu: user/system (checkmark)
	•	Output mode submenu: Mode A / Mode B (checkmark)
	•	Notifications submenu: All / Hotkey only / Off (checkmark)
	•	Overlay submenu (v0.4):
	•	Overlay enabled (checkmark)
	•	Click action: Generate blank / Open prompt panel (checkmark)
	•	Show on all Spaces (checkmark)
	•	Hide in fullscreen (checkmark)
	•	Settings…
	•	Hotkey enabled toggle
	•	Quit

7.2 Prompt panel
	•	Multiline text view.
	•	Role dropdown.
	•	Buttons: Copy Entry, Cancel.
	•	Cancel doen niks.

7.3 Settings panel (v0.3+)
	•	Hotkey enabled switch
	•	Hotkey capture:
	•	Capture Hotkey… (user presses combo)
	•	Validate: minstens 1 modifier
	•	Apply / reject (conflict/unavailable)
	•	Reset na default
	•	Notifications dropdown: All / Hotkey only / Off
	•	Pretty JSON toggle (Mode B)
	•	Status label vir feedback (“Hotkey applied”, “Rejected: add modifier”, ens.)

7.4 Overlay Bubble (v0.4)
	•	’n klein floating knop/bubble (bv { })
	•	Always-on-top
	•	Draggable
	•	Left click:
	•	action per setting (blank generate of prompt panel)
	•	Right click:
	•	Context menu met:
	•	Generate Entry
	•	Generate with Prompt…
	•	Mode A
	•	Mode B
	•	Open Settings…
	•	Hide Overlay
	•	Quit
	•	Position persistence: op drag release word posisie gestoor.
	•	Multi-screen: restore best-effort; clamp binne screen visible frame.

⸻

8. Notification behavior
	•	Best-effort via UserNotifications framework.
	•	Permission request:
	•	attempt on launch as policy ≠ off (idempotent, async).
	•	When to show:
	•	policy all: show for menu + hotkey + overlay
	•	policy hotkey_only: show only when source == hotkey
	•	policy off: never show
	•	Failure:
	•	If framework missing / permission denied → silently degrade (no crash).

⸻

9. Error handling & resilience

9.1 Clipboard errors
	•	If pasteboard write fails:
	•	Show critical alert “Clipboard error”
	•	App should remain running

9.2 Optional framework absence
	•	Carbon missing → hotkey features disabled gracefully:
	•	menu bar still works
	•	settings panel shows meaningful status
	•	UserNotifications missing → no notifications, no crash

9.3 Settings corruption
	•	On invalid / missing defaults:
	•	fall back to sane defaults
	•	app continues

⸻

10. Privacy & security
	•	No network.
	•	No logging of prompt content to disk (buiten NSUserDefaults metadata).
	•	Clipboard contains the generated entry (expected).
	•	App doesn’t store prompt history (v0.4).

⸻

11. Performance requirements
	•	“Generate & copy” should feel instant (< 100ms typical).
	•	UI should open within 200ms typical (prompt panel/settings).

⸻

12. Compatibility
	•	Python 3.12 compatible.
	•	macOS 26 target (best-effort downwards).
	•	PyObjC required; py2app used for packaging.

⸻

13. Deliverables (repo artifacts)
	•	src/clipboard_json_logger.py single-file, class-based modular codebase
	•	README.md recruiter-proof
	•	CHANGELOG.md with incremental versions
	•	setup.py (py2app)
	•	LICENSE (MIT)

⸻

14. Acceptance criteria (v0.4)
	1.	Menu bar app runs; “Generate Entry” copies output to clipboard.
	2.	Output includes id/role/prompt/datumtijd.
	3.	Modus A default output matches loose diary style.
	4.	Modus B produces valid JSON (pretty toggle works).
	5.	Role toggle persists.
	6.	Hotkey works when Carbon available; capture UI can set a new hotkey.
	7.	Notifications policy works; “hotkey_only” only notifies on hotkey.
	8.	Prompt panel accepts multiline prompt and copies correctly.
	9.	Overlay bubble can be enabled/disabled from menu.
	10.	Overlay bubble drag persists position; restores on relaunch.
	11.	Overlay click action works (blank generate OR prompt panel).
	12.	Overlay show-all-spaces and hide-in-fullscreen toggles apply.

⸻

15. Roadmap (ideas beyond v0.4)
	•	v0.5: overlay snap-to-edge + opacity/size sliders
	•	v0.5: auto-start at login toggle
	•	v0.6: entry templates (custom fields) / additional roles
	•	v0.6: “copy + auto-paste” optional (dangerous; needs guardrails)
	•	v0.7: history list (last N entries) + quick re-copy

⸻

16. Development cycle rules (process)

Vanaf nou word die ontwikkelsiklus as volg hanteer:
	1.	FS → FS review
	2.	Build plan → build plan review
	3.	TS bywerk met nuwe funksies
	4.	TS bugfixes implement
	5.	TS review
	6.	Code bou (commit-ready)

By elke stap moet die user die opsie kry om:
	•	direk na code generation te spring, en
	•	later terug te keer na die siklus-stap waar hy was.

---

## Volgende opsies (kies net ’n nommer)
1) **Build plan v0.4** skryf (stap-vir-stap + smoke tests + release checklist)  
2) **TS v0.4** skryf (tegniese detail vir overlay: window behaviors, persistence, menu wiring, edge cases)  
3) **Direk na code patching**: ek gee ’n klein v0.4.1 patch vir tipiese overlay issues (fullscreen/spaces quirks, right-click position, sizing)  
4) **App verbeter idees**: kies 1 verbeterpunt (snap-to-edge / auto-start / opacity slider / size slider / template fields) en ek werk FS+TS daarvoor uit
