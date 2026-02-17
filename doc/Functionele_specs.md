# Functional Specification (FS) — Clipboard JSON Logger
**Version:** 0.5 (FS v0.5.0)  
**Date:** 2026-02-18  
**Platform:** macOS (menu bar app)  
**Primary user:** single-user local workflow  
**Core promise:** 1 action → generate “chatlog entry”(s) → copied to clipboard → paste into editor

---

## 0. Sanity check (FS v0.5 completeness)
Hierdie **FS v0.5** is ’n verfyning van v0.4 met **geen verlies** van bestaande funksionaliteit.

### Behou (van v0.4 en vroeër)
- Menu bar app (geen Dock icon)
- Clipboard copy van gegenereerde entry
- Entry velde: `id`, `role`, `prompt`, `datumtijd`
- ID strategie: `short_id` (default) of `uuid4`
- `datumtijd` formaat: `YYYYMMDD` (timezone-aware best-effort; default Europe/Amsterdam)
- Output modes:
  - Modus A (Loose diary) **default**
  - Modus B (Strict JSON) **toggle**
  - Modus B “pretty JSON” **toggle**
- Rol: quick switch (menu) + persist
- Prompt panel: multiline prompt invoer + role override
- Notifications (best-effort) + policy: **All / Hotkey only / Off**
- Global hotkey (best-effort Carbon) + hotkey capture UI + enable/disable + reset
- Settings panel vir: hotkey enabled, hotkey capture/apply/reset, notifications mode, pretty JSON toggle
- Overlay Bubble (Floating Button):
  - enable/disable
  - draggable + position persistence
  - always-on-top
  - click action (generate blank OR open prompt panel)
  - right-click context menu
  - show on all Spaces toggle
  - hide in fullscreen toggle

### Nuut in v0.5
1) Role uitbreiding: **User + system** (twee blokke met dieselfde `id`)  
2) App UI taal: **Afrikaans default**, runtime taalwissel **sonder restart**  
3) Config export/import: defaults & settings kan na ’n **lokale JSON config** geskryf word; by opstart word config gelees en toegepas

---

## 1. Scope
### 1.1 In scope (v0.5)
’n macOS menu bar utility wat:
1) een of twee entry-modelle genereer (afhangend van role),  
2) dit formateer (Modus A of B),  
3) dit na die macOS clipboard skryf,  
4) opsioneel ’n notification wys,  
5) opsioneel via hotkey trigger,  
6) opsioneel via Overlay Bubble trigger,  
7) UI taal live kan verander,  
8) settings kan export/import via JSON config file.

### 1.2 Out of scope (v0.5)
- Sync na cloud / iCloud / Dropbox
- Entry history / browsing
- Multi-user accounts
- Editor integrasies (Obsidian/Notion API)
- Auto-parse van bestaande dagboek logs
- Template engine (beyond simple settings export/import)

---

## 2. Goals & non-goals
### 2.1 Goals
- Minimal friction: 1 klik of 1 hotkey → clipboard gereed.
- Betroubaarheid: geen crashes as optional frameworks ontbreek nie.
- Persistent settings: bly oor herstarts.
- Default taal: **Afrikaans**.
- Taal kan verander **sonder app restart**.

### 2.2 Non-goals
- “Perfect” JSON in Modus A (dis doelbewus los).
- 100% perfekte hotkey support oral (best-effort).
- Kompleks config UI (v0.5 fokus op minimum bruikbare config).

---

## 3. User workflow (happy paths)
### 3.1 Menu bar → Generate Entry
1. User open menu bar menu.
2. Kies **Genereer Inskrywing**.
3. App genereer entry/entries:
   - Role = `user` → 1 entry
   - Role = `system` → 1 entry
   - Role = `User + system` → **2 entries met dieselfde `id`**
4. App kopieer output na clipboard.
5. Opsioneel notification volgens policy.

### 3.2 Menu bar → Generate with Prompt…
1. Kies **Genereer met Prompt…**
2. Multiline panel open.
3. User tik prompt + kies role.
4. Klik **Kopieer**
5. App genereer 1 of 2 entries (soos bo), kopieer na clipboard.

### 3.3 Hotkey → Generate Entry
- Soos v0.4, maar respekteer nou ook `User + system` (dus 2 entries).

### 3.4 Overlay Bubble → Primary click
- Soos v0.4, maar respekteer nou ook role selection en taal.

### 3.5 Settings → Language change (no restart)
1. User open **Instellings…**
2. Kies taal (bv Afrikaans / Nederlands / English)
3. UI teks in menu + panels update onmiddellik.

### 3.6 Config export/import
1. User kies **Skryf config na JSON** (export)
2. App skryf alle defaults/settings na ’n local JSON file.
3. By volgende app start:
   - App lees config file (as dit bestaan)
   - Pas settings toe
   - UI reflekteer settings

---

## 4. Data model
### 4.1 Entry model fields
Elke entry bestaan uit:
- `id` (string)
- `role` (string: `"user"`, `"system"`, `"UserAndSystem"`)
- `prompt` (string; kan multiline wees)
- `datumtijd` (string: `"YYYYMMDD"`)

**Nota:** `"UserAndSystem"` is ’n **role-keuse** (generator-mode). In output word dit **twee aparte entries** met role `"user"` en `"system"`.

### 4.2 Default values
- default role: `"user"`
- default output mode: Modus A (loose diary)
- default ID strategy: `short_id` (length ±9)
- default timezone: `"Europe/Amsterdam"`
- default notifications policy: `"hotkey_only"`
- default hotkey: Ctrl+Opt+Cmd+J (best-effort)
- default UI language: **Afrikaans**

---

## 5. Output formats
### 5.1 Modus A — Loose diary format (default)
- Mens-leesbaar, pas by dagboekstyle.
- Nie noodwendig geldige JSON nie.
- Enkel entry voorbeeld:

```text
{'id': 'efeqer3fr', role: 'system', prompt: """
Hello
"""
,
datumtijd: "20260214"
},

5.2 Modus B — Strict JSON format (toggle)
	•	Geldige JSON.
	•	Opsioneel “pretty”.

{
  "id": "efeqer3fr",
  "role": "system",
  "prompt": "Hello\n",
  "datumtijd": "20260214"
}

5.3 Output when Role = User + system

Wanneer role menu op User + system staan:
	•	App genereer 2 entries:
	1.	role "user"
	2.	role "system"
	•	Beide entries deel dieselfde unieke id en dieselfde datumtijd.
	•	prompt:
	•	By “Generate Entry” → blank prompt vir beide
	•	By “Generate with Prompt…” → dieselfde prompt tekst vir beide (tensy later verfyn)

Clipboard output layout:
	•	Twee blokke word na clipboard gekopieer, geskei deur ’n leë reël (vir leesbaarheid).
	•	In Modus B bly elke blok ’n afsonderlike geldige JSON object (nie as ’n array nie).

Voorbeeld (Modus B, “User + system”):

{
  "id": "abc123xyz",
  "role": "user",
  "prompt": "",
  "datumtijd": "20260218"
}

{
  "id": "abc123xyz",
  "role": "system",
  "prompt": "",
  "datumtijd": "20260218"
}


⸻

6. Settings & persistence

6.1 Storage
	•	Primary: macOS user defaults (NSUserDefaults).
	•	Add-on (v0.5): lokale JSON config file vir export/import.

6.2 Settings list (functional)

Core
	•	Default role: user | system | UserAndSystem
	•	Output mode: loose_diary | strict_json
	•	Strict JSON pretty: true|false
	•	ID strategy: short_id | uuid4
	•	datumtijd strategy: date_yyyymmdd
	•	UI language: Afrikaans | Nederlands | English | ... (extensible)

Notifications
	•	Notifications policy: all | hotkey_only | off

Hotkey
	•	Hotkey enabled: true|false
	•	Hotkey keycode + modifiers (best-effort)

Overlay Bubble
	•	Overlay enabled: true|false
	•	Overlay click action: generate_blank | open_prompt_panel
	•	Show on all Spaces: true|false
	•	Hide in fullscreen: true|false
	•	Saved position: x,y (+ optional screen hint)

Config file
	•	Config file path (fixed default + optional “choose file” later)
	•	Actions:
	•	Export settings to JSON
	•	Import/apply settings from JSON (on demand, plus at startup)

⸻

7. UI requirements

7.1 Menu bar item
	•	Status icon/text minimal.
	•	Menu items (Afrikaans default labels):
	•	Genereer Inskrywing
	•	Genereer met Prompt…
	•	Role submenu: user / system / User + system (checkmark)
	•	Output mode submenu: Mode A / Mode B (checkmark)
	•	Notifications submenu: All / Hotkey only / Off (checkmark)
	•	Overlay submenu (enable + click action + spaces + fullscreen)
	•	Instellings…
	•	Hotkey geaktiveer (toggle)
	•	Quit

7.2 Role submenu (updated)
	•	Role submenu: user / system / User + system (checkmark)

Behavior when “User + system”:
	•	“Generate Entry” en “Generate with Prompt…” moet 2 entries genereer,
	•	dieselfde unieke id,
	•	kopieer beide na clipboard (geskei deur leë reël).

7.3 Prompt panel
	•	Multiline prompt invoer.
	•	Role dropdown: user/system/User + system.
	•	Knoppies: Kopieer, Kanselleer.

7.4 Settings panel
	•	Soos v0.4, plus:
	•	Taalkeuse dropdown
	•	Config actions:
	•	Skryf config na JSON
	•	Lees config van JSON (Apply)

7.5 Overlay Bubble
	•	Soos v0.4, plus:
	•	respekteer taal (context menu labels) en role behavior.

⸻

8. Localization (v0.5)

8.1 Default language
	•	Default UI taal = Afrikaans.

8.2 Runtime language switching (no restart)
	•	Wanneer user taal verander:
	•	Menu titles/labels update onmiddellik
	•	Settings panel labels update onmiddellik
	•	Prompt panel labels update onmiddellik
	•	Overlay context menu update onmiddellik

8.3 Translation coverage
	•	Alle user-facing strings:
	•	menu items
	•	panel titles
	•	button labels
	•	status lines (settings feedback)
	•	alerts (clipboard errors, hotkey conflicts)
	•	Internal keys/values (bv output_mode) bly Engels/tech (net UI teks vertaal).

⸻

9. Local JSON config file (v0.5)

9.1 Export
	•	App kan alle settings/defaults skryf na ’n JSON file.
	•	JSON bevat net settings (geen prompt history).
	•	Skryf aksie moet óf:
	•	bestaande file overwrite (simple), óf
	•	write-atomic (preferred) — detail in TS.

9.2 Import at startup
	•	By app start:
	•	As config file bestaan → lees → apply settings → UI refresh.
	•	As file ontbreek of corrupt → ignore en gebruik defaults; app moet nie crash nie.

9.3 Manual import/apply
	•	Vanuit Settings: “Lees config van JSON” apply onmiddellik, sonder restart.

⸻

10. Error handling & resilience
	•	Clipboard write fail → NSAlert + app bly run.
	•	Optional frameworks missing → degrade gracefully.
	•	Config file invalid → ignore + warning status (non-fatal).

⸻

11. Privacy & security
	•	Geen netwerk.
	•	Geen storing van prompt content (behalwe clipboard).
	•	Config file bevat slegs settings.

⸻

12. Performance
	•	Generate+copy voel instant.
	•	Language switch moet onmiddellik UI refresh.

⸻

13. Deliverables (repo artifacts)
	•	src/clipboard_json_logger.py single-file, class-based
	•	README.md recruiter-proof
	•	CHANGELOG.md incremental
	•	setup.py (py2app)
	•	LICENSE (MIT)

⸻

14. Acceptance criteria (v0.5)
	1.	Role submenu het 3 opsies: user/system/User + system.
	2.	“User + system” genereer 2 entries met dieselfde id en datumtijd.
	3.	UI taal is Afrikaans by default.
	4.	Taal kan verander sonder app restart; alle UI teks update.
	5.	Export settings na JSON werk; file word geskryf.
	6.	Import by startup pas settings toe (as file bestaan).
	7.	Manual import/apply in Settings werk sonder restart.
	8.	Alle v0.4 funksies bly werk (hotkey, notifications, overlay, prompt panel).

⸻

15. Roadmap (behou + uitbrei)
	•	v0.6: overlay snap-to-edge + opacity/size sliders
	•	v0.6: auto-start at login
	•	v0.7: entry templates/presets (meer as net settings)
	•	v0.7: history (last N entries) + re-copy

⸻

# 16. Development cycle rules (process)

## Ontwikkelsiklus:
	1.	FS → FS review
	2.	Build plan → build plan review
	3.	TS bywerk met nuwe funksies
	4.	TS bugfixes implement
	5.	TS review
	6.	Code bou (commit-ready)

### By elke stap kan jy:
	•	direk na code generation spring, en
	•	later terugkeer na die stap waar jy was.

## Volgende opsies (kies net ’n nommer)
1) **Build plan v0.5** (incl config import/export + runtime i18n + UserAndSystem output)  
2) **TS v0.5** skryf (tegniese detail: runtime string refresh, config path strategy, output concatenation rules)  
3) **Direk na code**: commit-ready blokke vir v0.5 (Python + README + setup.py + CHANGELOG updates)  
4) **Verbeterings**: kies 1 fokus (snap-to-edge / auto-start at login / overlay opacity / templates) en ek werk FS+TS addendum uit

