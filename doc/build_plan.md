Hier is ’n retro build-plan reeks vir v0.1, v0.2, v0.3 (met dieselfde styl as jou v0.4 plan). Ek baseer dit op wat ons in hierdie chat as features het (en jou 0.3.1 code). As jy ’n ou tag/commit-log het kan ons dit later 1:1 laat match.

⸻

# Build Plan v0.1 — Minimal Clipboard Generator

## Doel

’n Super klein macOS utility wat ’n entry genereer (id + role + prompt + datumtijd) en dit na clipboard kopieer — fokus op Mode A en menu bar.

## Features in scope
	•	Menu bar status item ({ })
	•	Menu action: Generate Entry
	•	Data model: id, role, prompt, datumtijd
	•	Default:
	•	role = user
	•	prompt = "" (leeg)
	•	datumtijd = YYYYMMDD
	•	id strategy = short id (eenvoudig)
	•	Clipboard copy
	•	Basic error handling (alert as clipboard fail)

## Build steps
```
	1.	Project skeleton
	•	src/clipboard_json_logger.py single-file
	•	README.md (wat doen dit + run instructions)
	2.	Domain
	•	EntryModel dataclass
	•	IdService (simple short id)
	•	DateTimeService (YYYYMMDD)
	•	EntryFormatter (Mode A only)
	3.	ClipboardService
	•	write text to pasteboard
	4.	Menu bar UI
	•	status item + menu met “Generate Entry” + “Quit”
	5.	Smoke tests
	•	Launch → status item visible
	•	Generate Entry → clipboard contains Mode A snippet
```

## Acceptance checklist v0.1
```
	•	Menu bar app run
	•	Generate Entry copies correct Mode A format
	•	No crash if clipboard fails (shows alert)
```
⸻

# Retro Build Plan v0.2 — Mode B + Instellings (NSUserDefaults)

## Doel

Maak die tool “regtig bruikbaar” vir jou dagboek flow deur:
```
	•	Mode A default + Mode B strict JSON toggle
	•	NSUserDefaults vir persistente settings
	•	Role selection + id strategy selection
```

Features in scope (add on v0.1)
```
	•	Mode B (strict JSON): valid JSON output
	•	Output mode toggle in menu:
	•	Loose diary (Mode A) default
	•	Strict JSON (Mode B)
	•	Role submenu in menu:
	•	user/system
	•	NSUserDefaults config:
	•	default_role
	•	output_mode
	•	id_strategy (short_id|uuid4)
	•	datumtijd_strategy (date_yyyymmdd)
	•	json_pretty (for Mode B)
	•	IdService supports uuid4
	•	DateTime timezone handling (Europe/Amsterdam via zoneinfo if available)
```

Build steps
```
	1.	Config layer
	•	AppConfig wrapper around NSUserDefaults
	•	ensure defaults on first run
	2.	Formatter uitbrei
	•	Mode A (loose)
	•	Mode B strict JSON (pretty toggle)
	3.	Menu uitbrei
	•	Role submenu (checkmarks)
	•	Output Mode submenu (checkmarks)
	4.	Core generate refactor
	•	generate_and_copy(...) uses config
	5.	Smoke tests
	•	Toggle role → affects output
	•	Toggle Mode B → output valid JSON
	•	Restart app → settings persist
```

Acceptance checklist v0.2
```
	•	Mode A default works
	•	Mode B emits valid JSON
	•	Role + mode persist across restarts
	•	id_strategy uuid4 works
```

⸻

# Retro Build Plan v0.3 — Prompt Panel + Notifications + Hotkey + Settings UI

## Doel

Maak dit “high frequency” en “low friction” met:
```
	•	Multiline prompt entry panel
	•	Global hotkey (best-effort)
	•	Notifications policy
	•	Settings panel (hotkey capture + notif settings + pretty json)
```

Features in scope (add on v0.2)
```
	•	Multiline Prompt Panel
	•	“Generate with Prompt…”
	•	role dropdown
	•	NSTextView multiline
	•	Copy/Cancel
	•	Notifications (best-effort)
	•	UserNotifications framework (as available)
	•	policy: all / hotkey_only / off
	•	request permission best-effort (non-blocking)
	•	Global hotkey (best-effort Carbon)
	•	enable toggle
	•	default Ctrl+Opt+Cmd+J
	•	capture UI
	•	reset button
	•	conflict/unavailable degrade
	•	Settings panel
	•	hotkey enabled
	•	capture/apply/reset
	•	notifications dropdown
	•	pretty JSON toggle
	•	status line feedback
	•	Menu items
	•	Settings…
	•	Hotkey Enabled toggle
	•	Notifications submenu
	•	Stability fix
	•	Avoid Foundation import collisions (prefer Cocoa/fallback)
```

Build steps
```
	1.	Prompt panel controller
	•	NSPanel + role popup + NSTextView + buttons
	•	callback → generate_and_copy(role, prompt)
	2.	NotificationService
	•	feature detect UserNotifications availability
	•	permission request (idempotent)
	•	send notification method
	•	integrate policy check in AppController
	3.	HotkeyService
	•	Carbon availability check
	•	RegisterEventHotKey + handler
	•	start/stop
	4.	Settings panel
	•	UI controls + callbacks into AppController
	•	hotkey capture view (first responder)
	•	apply candidate + revert if conflict
	5.	Menu integration
	•	add menu items/submenus
	•	refresh checkmarks function
	6.	Smoke tests
	•	Prompt panel multi-line copy
	•	Notifications policy behavior
	•	Hotkey trigger works (or graceful fail)
	•	Settings changes persist
```

Acceptance checklist v0.3
```
	•	Prompt panel works with multi-line
	•	Notifications policy works, no crash if denied/unavailable
	•	Hotkey works if Carbon available; else menu-only still works
	•	Settings panel applies and persists values
```

<img src="../img/app_demo1.png">

Hier is Build Plan v0.4 (menu bar app + bestaande v0.3.1 funksies + nuwe overlay bubble). Ek hou dit commit/implementasie-gefokus, met ’n kort toetsplan per stap.

⸻

# Build Plan v0.4 — Overlay Bubble vir Clipboard JSON Logger

0) Build doel

Voeg ’n Floating Overlay Bubble by die bestaande v0.3.1 menu bar app, met:
	•	enable/disable
	•	draggable + posisie persistence
	•	click action (generate blank vs open prompt panel)
	•	right-click context menu
	•	show on all Spaces + hide in fullscreen (defaults ON)
	•	geen polling, low CPU

Release target: 0.4.0
Branch voorstel: feature/overlay-bubble

⸻

1) Voorbereiding

1.1 Repo hygiene
```
	•	Maak seker APP_VERSION word bump na 0.4.0
	•	setup.py en CHANGELOG.md bump na 0.4.0
	•	README.md voeg overlay usage by

```
Toets: app run nog soos v0.3.1 (menu bar + prompt panel + settings).

1.2 Dependencies

Geen nuwe PyPI deps nodig; alles via PyObjC/AppKit.

Toets: python -c "from Cocoa import NSObject" werk in venv.

⸻

## 2) FS → Settings keys toevoeg (NSUserDefaults)

### 2.1 Voeg nuwe NSUserDefaults keys by

In jou config constants:
```
	•	K_OVERLAY_ENABLED = "overlay_enabled" default False
	•	K_OVERLAY_CLICK_ACTION = "overlay_click_action" default "generate_blank" of "open_prompt_panel"
	•	K_OVERLAY_SHOW_ALL_SPACES = "overlay_show_all_spaces" default True
	•	K_OVERLAY_HIDE_IN_FULLSCREEN = "overlay_hide_in_fullscreen" default True
	•	K_OVERLAY_POS_X = "overlay_pos_x" (float/int)
	•	K_OVERLAY_POS_Y = "overlay_pos_y" (float/int)
	•	K_OVERLAY_SCREEN_ID = "overlay_screen_id" (int/string) (optional)
```
### 2.2 AppConfig getters/setters
```
	•	overlay_enabled, overlay_click_action, overlay_show_all_spaces, overlay_hide_in_fullscreen
	•	setters vir elk
	•	methods om overlay pos te save/load
```
Toets: verander values, restart app, values bly.

⸻

## 3) UI: Overlay Bubble window bou

3.1 Nuwe klasse: OverlayBubbleController

Responsibility:
```
	•	skep ’n klein NSPanel of borderless NSWindow
	•	always-on-top (floating)
	•	bevat ’n NSButton (round)
	•	hanteer drag + save pos
	•	hanteer click action + right-click context menu
	•	apply “Spaces + fullscreen” gedrag

```

Implementasie riglyne:
```
	•	Window style:
	•	borderless utility-like
	•	ignore mouse events = NO (ons wil klik/drag)
	•	Window level:
	•	NSFloatingWindowLevel (of NSStatusWindowLevel as needed)
	•	Collection behavior (Spaces):
	•	as overlay_show_all_spaces:
	•	NSWindowCollectionBehaviorCanJoinAllSpaces
	•	anders:
	•	default
	•	Fullscreen hide:
	•	as overlay_hide_in_fullscreen:
	•	NSWindowCollectionBehaviorFullScreenAuxiliary af (of alternatiewe gedrag)
	•	en/of luister na active space fullscreen status (later)
	•	Pragmaties vir v0.4:
	•	stel behavior flags so overlay nie bo fullscreen sit nie (auxiliary off)
```
Toets: enable overlay → bubble verskyn bo ander windows; disable overlay → weg.

3.2 Dragging

Opsie A (simpel): maak ’n custom view/button subclass wat mouseDown_/mouseDragged_ hanteer en window move.

```
	•	On drag end → save pos (x,y) in NSUserDefaults
```

Toets: drag na hoek, restart app → selfde pos.

3.3 Clamp pos binne screen

By startup:
```	•	laai pos
	•	bepaal target screen visibleFrame
	•	clamp so bubble nie off-screen is nie
```

Toets: verander resolution/monitor → bubble bly visible.

⸻

# 4) Overlay interactions

4.1 Click action
```
	•	As overlay_click_action == "generate_blank":
	•	call AppController.generate_and_copy(source="overlay")
	•	As "open_prompt_panel":
	•	call onGenerateWithPrompt_ of direkte prompt_panel.show()
```

Toets: toggle click action in settings → bubble click gedrag verander.

4.2 Right-click context menu
```	•	Op right mouse click: pop NSMenu met:
	•	Generate Entry
	•	Generate with Prompt…
	•	Toggle Mode A/B
	•	Open Settings…
	•	Hide Overlay
	•	Quit
```

Toets: right-click wys menu; items werk.

⸻

# 5) Menu bar: overlay toggles integreer

5.1 Menu items

Voeg onder Settings:
```
	•	Overlay Bubble submenu of enkel toggle item:
	•	“Overlay Enabled” (checkbox)
	•	“Overlay Click Action → Generate blank / Prompt panel”
	•	“Show on all Spaces” toggle
	•	“Hide in fullscreen” toggle
```
Toets: toggles werk en reflect state (checkmarks).

5.2 Settings panel uitbrei (minimum)

Vir v0.4 kan jy kies:
```
	•	Minimum viable: net menu toggles (geen settings panel uitbreiding)
	•	Nice-to-have: voeg overlay section in Settings panel
```
Aanbeveling v0.4: minimum viable via menu, later UI polish.

⸻

6) Controller wiring in AppController

6.1 Instantiate overlay controller

In AppController.init():
```
	•	self.overlay = None
```

In applicationDidFinishLaunching_:
```
	•	if config.overlay_enabled: self._start_overlay()
```
6.2 Start/stop methods
```
	•	_start_overlay():
	•	create OverlayBubbleController met callbacks na AppController aksies
	•	_stop_overlay():
	•	close window, release controller
```
6.3 Apply settings hooks

In apply_settings(...) voeg:
```
	•	reason == "overlay":
	•	start/stop overlay
	•	update overlay behavior (spaces/fullscreen/click action)
```

Toets: enable/disable via menu & settings werk “live”.

⸻

7) Notifications policy: overlay source

FS sê notifications is policy-based. Overlay triggers moet as source "overlay" tel.
```
	•	In _should_notify(source):
	•	hotkey_only → notify net vir source == "hotkey"
	•	all → notify vir overlay ook
	•	off → niks
```
Toets: overlay klik → geen notif onder hotkey_only; wel notif onder all.

⸻

## 8) Packaging (py2app) + smoke tests

8.1 py2app build
```
	•	Build .app
	•	Run .app buite terminal om permissions gedrag te toets
```
8.2 Smoke test checklist
```
	1.	Launch: status item verskyn
	2.	Generate Entry → clipboard bevat output
	3.	Generate with Prompt → panel open, multi-line, copy werk
	4.	Mode B strict JSON → valid JSON in clipboard
	5.	Notifications:
	•	set to all → notif op menu generate
	•	set hotkey_only → notif net op hotkey
	6.	Hotkey:
	•	enable → trigger
	•	conflict → error/disable degrade
	7.	Overlay:
	•	enable → bubble verskyn
	•	drag + restart → pos onthou
	•	click action toggle → gedrag verander
	•	right-click menu → items werk
	•	fullscreen hide setting → overlay nie bo fullscreen app (kontroleer met bv. Safari fullscreen)
```
⸻

## 9) Release checklist (0.4.0)

```
	•	APP_VERSION, setup.py, CHANGELOG.md consistent
	•	README overlay usage + toggles
	•	No crashes if Carbon/UN frameworks absent
	•	Overlay disabled by default (veilig)
	•	Manual smoke test done
```

# Build Plan — Clipboard JSON Logger v0.5.0
**Date:** 2026-02-18  
**Implements:** FS v0.5.0 (User+system role, Afrikaans default + runtime language switch, JSON config export/import + apply at startup)  
**Packaging:** py2app  
**Code style:** single-file app module, class-based, modular

---

## 0) Definition of Done (v0.5.0)
Release is “done” when:
1. Role menu has **user / system / User + system**
2. **User + system** generates **two blocks** with **same id** + same datumtijd; copied to clipboard separated by a blank line
3. UI default language is **Afrikaans**
4. Language can change **without app restart** (menus + panels update immediately)
5. Settings can be exported to a local JSON config file
6. App startup loads config file (if present) and applies settings
7. All existing v0.4 features still work (prompt panel, overlay, notifications policy, hotkey capture/apply)

---

## 1) Repo assumptions (current structure)
Recommended minimal structure:
- `src/clipboard_json_logger.py`
- `README.md`
- `CHANGELOG.md`
- `setup.py`
- `LICENSE`

If your repo differs, we adapt paths, but keep code in **one** file.

---

## 2) Dependencies / environment
### 2.1 Python & venv
- Python 3.12
- venv activated (you already have this)

### 2.2 Python packages
Minimum:
- `pyobjc`
- `py2app`
Optional/best-effort:
- `pyobjc-framework-UserNotifications` (often already included via pyobjc meta-package)

Install/update:
```bash
python -m pip install -U pip
python -m pip install -U pyobjc py2app
# optional (only if you find missing UserNotifications module):
python -m pip install -U pyobjc-framework-UserNotifications


⸻

3) Config file strategy (v0.5.0)

3.1 Path (fixed default for v0.5.0)

Use a deterministic per-user path:

~/Library/Application Support/Clipboard JSON Logger/config.json

Reason: stable, normal macOS location, no UI file picker required.

3.2 Behavior
	•	On startup:
	•	If config exists: read JSON → apply settings → refresh UI
	•	If invalid: ignore + keep defaults; do not crash
	•	Export:
	•	“Write config to JSON” overwrites file (atomic write preferred)
	•	Manual import/apply:
	•	“Read config from JSON” reads file and applies immediately (no restart)

⸻

4) Implementation tasks (ordered)

Task A — Bump version metadata + changelog scaffolding
	1.	Set APP_VERSION = "0.5.0" in code (and build date)
	2.	Add new section to CHANGELOG.md for v0.5.0:
	•	Added: User + system role
	•	Added: Afrikaans default UI + runtime language switch
	•	Added: JSON config export/import + apply on startup

Checkpoint A: running app still launches and copies entries (existing features not broken).

⸻

Task B — Add UserAndSystem role end-to-end

Goal: A role choice that yields two entries sharing same id+datumtijd.
	1.	Update role domain:
	•	FS says role includes "UserAndSystem" as selection value.
	2.	Update settings:
	•	default_role can now be "user" | "system" | "UserAndSystem"
	3.	Update UI role menu:
	•	Add menu item “User + system”
	•	Checkmark logic includes third option
	4.	Update prompt panel role dropdown:
	•	Add “User + system”
	5.	Update entry generation logic:
	•	Replace _make_entry(role, prompt) with something like _make_entries(role_selection, prompt) returning a list.
	•	If role_selection == "UserAndSystem":
	•	Generate shared_id once
	•	Generate datumtijd once
	•	Create two EntryModels:
	•	role "user"
	•	role "system"
	•	Same prompt for both
	6.	Update formatter/clipboard output:
	•	Format each entry using selected output mode
	•	Join blocks with "\n\n" (blank line)
	•	Copy joined text to clipboard

Checkpoint B (manual tests):
	•	Select “User + system” → Generate Entry → paste:
	•	two blocks
	•	same id in both
	•	same datumtijd in both
	•	Works for Mode A and Mode B.

⸻

Task C — Internationalization (i18n) with runtime switching

Goal: Afrikaans default UI text; language switch updates UI immediately.
	1.	Add new setting:
	•	ui_language: e.g. "af" | "nl" | "en" (store code, not full name)
	2.	Build a string table in code:
	•	A dict: STRINGS = {"af": {...}, "nl": {...}, "en": {...}}
	•	Keys for every user-facing string:
	•	Menu titles, submenu titles, panel titles, buttons, alerts, status lines
	3.	Add helper function:
	•	t(key) -> str returns string based on current language
	4.	Update menu build to use t(...):
	•	When language changes, you must update existing menu items titles (not just rebuild on next launch)
	•	Practical approach:
	•	Keep references to each NSMenuItem as instance vars
	•	Provide _refresh_ui_texts() that sets each setTitle_() accordingly
	5.	Update Prompt panel UI texts:
	•	Add method on PromptPanelController: refresh_texts(lang) that updates:
	•	panel title
	•	labels/buttons
	6.	Update Settings panel UI texts:
	•	Add language dropdown:
	•	Afrikaans / Nederlands / English (display names localized too)
	•	On change:
	•	persist ui_language
	•	call app controller to refresh UI texts
	7.	Default language:
	•	Ensure defaults seed ui_language = "af" unless config overrides

Checkpoint C:
	•	Change language while app is running:
	•	menu text updates immediately
	•	settings + prompt panel labels update immediately (if open, they update too)
	•	no restart required

⸻

Task D — JSON config export/import + startup apply

Goal: Write defaults/settings to JSON; read on startup and apply; manual apply via Settings.
	1.	Add Config service:
	•	ConfigFileService with:
	•	config_path()
	•	export_config(app_config) -> (ok, err)
	•	import_config() -> dict | None
	•	apply_config(app_config, dict) -> (ok, err, warnings[])
	2.	Define JSON schema (v0.5 minimal):
	•	Only known keys, e.g.:
	•	default_role, id_strategy, output_mode, json_pretty,
notifications_mode, hotkey_enabled, hotkey_keycode, hotkey_modifiers,
overlay_enabled, overlay_click_action, overlay_show_all_spaces, overlay_hide_in_fullscreen,
overlay_pos_x, overlay_pos_y, overlay_screen_hint,
ui_language
	3.	Export:
	•	Write JSON pretty (indent=2) for readability
	•	Use atomic write:
	•	write to config.json.tmp then replace
	4.	Import at startup:
	•	In applicationDidFinishLaunching_:
	•	call ConfigFileService.import_config()
	•	if dict: apply to AppConfig setters
	•	then refresh:
	•	menu states
	•	UI texts
	•	hotkey registration (if enabled)
	•	overlay show/hide + behavior update
	5.	Manual export/import actions in Settings:
	•	Add two buttons:
	•	“Skryf config na JSON”
	•	“Lees config van JSON”
	•	On click: run export/import + show status label result

Checkpoint D:
	•	Export creates file at path
	•	Edit file manually (e.g. change language) → restart app → applied
	•	Manual import apply updates live without restart

⸻

Task E — Overlay updates (ensure it respects new features)
	1.	Overlay context menu strings go through t(...)
	2.	Overlay role behavior respects User+system (it already calls generate function; ensure it uses role selection)
	3.	Overlay click-action respects language (menu titles) and still works

Checkpoint E:
	•	Overlay enabled: right-click menu shows in selected language
	•	Clicking overlay generates correct output for User+system

⸻

%5) QA checklist (smoke tests)

Run these before tagging v0.5.0:
```
	1.	Clipboard
	•	Generate Entry copies something; paste matches expected format
	2.	Mode A / Mode B
	•	Mode A output remains “loose diary”
	•	Mode B output validates as JSON per block
	3.	User + system
	•	Two blocks, same id, same datumtijd
	4.	Prompt panel
	•	Multiline text preserved in both modes
	5.	Notifications policy
	•	Off / Hotkey only / All behaves as defined
	6.	Hotkey
	•	Works if Carbon available; capture + apply works; conflict handled
	7.	Language
	•	Default Afrikaans
	•	Switch to NL/EN updates menu + open panels immediately
	8.	Config file
	•	Export writes file
	•	Import at startup applies
	•	Manual import applies live
	9.	Overlay
	•	Enable/disable; drag persists; click works; context menu localized
```
⸻

6) Packaging & release steps (py2app)
	1.	Bump version references:
	•	code APP_VERSION
	•	setup.py plist CFBundleShortVersionString (if present)
	2.	Build:


```bash
python setup.py py2app
```
	3.	Run app from dist/ and repeat critical smoke tests (hotkey/notifications sometimes differ vs running from python).
	4.	Tag + release:

```bash
git add -A
git commit -m "v0.5.0: User+system role, Afrikaans UI + runtime language switch, JSON config export/import"
git tag v0.5.0
git push --tags
git push
```

⸻

# 7) Work breakdown into commits (recommended)
	•	Commit 1: version bump + changelog skeleton
	•	Commit 2: User + system role end-to-end
	•	Commit 3: i18n runtime switching + Afrikaans default
	•	Commit 4: config export/import + startup apply
	•	Commit 5: overlay localization + final polish

⸻

8) Risks & mitigations
	•	Spaces/fullscreen overlay quirks: treat as best-effort; clamp and keep toggles.
	•	Language refresh complexity: keep UI item references; implement one refresh function called everywhere.
	•	Config drift: apply only known keys; ignore unknown keys with warnings (display in settings status).

⸻


## Volgende opsies (kies net ’n nommer)

```1) **Build plan review checklist**: ek skryf ’n kort “afmerklys” wat jy kan volg terwyl jy implementeer (super prakties)  
2) **TS v0.5.0**: volledige tegniese spesifikasie vir alles in hierdie build plan (incl i18n + config schema + UI refresh strategy)  
3) **Direk na code**: ek genereer commit-ready blokke vir v0.5.0 (updated `clipboard_json_logger.py` + README + setup.py + CHANGELOG)  
4) **Een fokus-verbetering**: snap-to-edge of auto-start-at-login as add-on (FS/TS addendum)
```
