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

```	•	APP_VERSION, setup.py, CHANGELOG.md consistent
	•	README overlay usage + toggles
	•	No crashes if Carbon/UN frameworks absent
	•	Overlay disabled by default (veilig)
	•	Manual smoke test done
```
