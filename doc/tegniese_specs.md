Ik ga dit doen, maar eerst eerlijk over de sanity-check: ik kan jouw “TS v0.3” niet letterlijk teruglezen als apart document, omdat die niet als volledige TS in deze chat staat. Wat ik wél kan doen (en ga doen) is:
	•	Stap 1 sanity-check tegen alles wat hier als v0.3/v0.3.1 functionaliteit al zichtbaar is (jouw code + requirements), plus wat ik net als TS v0.4 heb geschreven.
	•	Daarna herschrijf ik de volledige TS v0.4 inclusief overlay.
	•	En ik lever een volledig CHANGELOG vanaf v0.2 (v0.2 → v0.3 → v0.3.1 → v0.4.0), en check opnieuw dat niks uit stap 1 ontbreekt.

⸻

1) Sanity-check basis: alle functionaliteiten die behouden moeten blijven

Uit v0.2 (afgeleid uit requirements + code)
	•	Mode A (loose diary) default output, met triple quotes prompt en trailing },
	•	Mode B (strict JSON) toggle, valid JSON output
	•	JSON pretty toggle (Mode B)
	•	Role: user/system, default role setting + menu switch
	•	ID strategy: short_id (default) of uuid4
	•	datumtijd: YYYYMMDD (timezone Europe/Amsterdam via zoneinfo indien beskikbaar)
	•	Clipboard copy service
	•	Menu bar app (status item + menu)

Uit v0.3 / v0.3.1 (afgeleid uit code + requirements)
	•	Multiline prompt panel (NSPanel + NSTextView) + role dropdown
	•	Notifications (UserNotifications) best-effort
	•	policy all / hotkey_only / off
	•	permission request best-effort
	•	Global hotkey best-effort via Carbon
	•	enable/disable
	•	default Ctrl+Opt+Cmd+J
	•	hotkey capture UI + apply + reset
	•	conflict/unavailable degrade gracefully
	•	Settings panel
	•	hotkey enabled switch
	•	hotkey capture
	•	reset
	•	notifications mode dropdown
	•	pretty JSON toggle
	•	status line feedback
	•	Menu items voor role/mode/notifs/settings/hotkey toggle
	•	Fix voor Foundation import collision: prefer Cocoa / fallback Foundation (v0.3.1 bugfix)

Nieuw v0.4
	•	Overlay Bubble (floating button)
	•	enable/disable
	•	draggable + position persistence + screen clamp
	•	click action configurable (generate_blank / open_prompt_panel)
	•	right-click context menu
	•	show on all spaces (default ON)
	•	hide in fullscreen (default ON)
	•	no polling

✅ Dit is die “must keep” set. Hieronder komt de herschreven TS v0.4 die alles omvat.

⸻

TS v0.4 — Clipboard JSON Logger (Menu Bar + Overlay Bubble)

App: Clipboard JSON Logger
Release target: 0.4.0
Platform: macOS (menu bar utility)
Stack: Python 3.12 + PyObjC + py2app
Repo style: single-file app code (src), modular class-based

0) Doel

’n macOS menu bar app wat “chatlog entry” outputs genereer (Mode A of Mode B) en na clipboard kopieer, met optionele prompt panel, notifications, hotkey, en nou ook ’n always-on-top overlay bubble vir 1-click logging.

⸻

1) Data model & output formats

1.1 EntryModel

Fields:
	•	id: str
	•	role: str ("user" of "system")
	•	prompt: str (kan multiline wees)
	•	datumtijd: str (YYYYMMDD)

1.2 Mode A — Loose diary format (default)

Output is nie strict JSON nie. Dit moet visueel soos jou dagboek entry lyk.

Format:
	•	single entry string
	•	triple quotes vir prompt
	•	datumtijd: "YYYYMMDD"
	•	trailing },

Voorbeeld:

{'id': 'abc123xyz', role: 'system', prompt: """
Hallo
multi-line
"""
,
datumtijd: "20260214"
},

1.3 Mode B — Strict JSON (toggle)

Valid JSON string:

{
  "id": "…",
  "role": "user",
  "prompt": "…",
  "datumtijd": "YYYYMMDD"
}

Pretty option:
	•	json_pretty=True → indent=2
	•	False → compact separators (",", ":")

⸻

2) Config & persistence (NSUserDefaults)

2.1 Keys (existing)
	•	K_DEFAULT_ROLE = "default_role" (default "user")
	•	K_ID_STRATEGY = "id_strategy" ("short_id" default | "uuid4")
	•	K_OUTPUT_MODE = "output_mode" ("loose_diary" default | "strict_json")
	•	K_DATUMTIJD_STRATEGY = "datumtijd_strategy" ("date_yyyymmdd" default)
	•	K_HOTKEY_ENABLED = "hotkey_enabled" (default True)
	•	K_HOTKEY_KEYCODE = "hotkey_keycode" (default J keycode)
	•	K_HOTKEY_MODIFIERS = "hotkey_modifiers" (default ctrl+opt+cmd)
	•	K_NOTIFICATIONS_MODE = "notifications_mode" ("hotkey_only" default | "all" | "off")
	•	K_JSON_PRETTY = "json_pretty" (default True)

2.2 Keys (new v0.4 overlay)
	•	K_OVERLAY_ENABLED = "overlay_enabled" (default False)
	•	K_OVERLAY_CLICK_ACTION = "overlay_click_action"
	•	"generate_blank" default
	•	"open_prompt_panel"
	•	K_OVERLAY_SHOW_ALL_SPACES = "overlay_show_all_spaces" (default True)
	•	K_OVERLAY_HIDE_IN_FULLSCREEN = "overlay_hide_in_fullscreen" (default True)
	•	K_OVERLAY_POS_X = "overlay_pos_x" (float; optional)
	•	K_OVERLAY_POS_Y = "overlay_pos_y" (float; optional)
	•	K_OVERLAY_SCREEN_INDEX = "overlay_screen_index" (int; optional)

2.3 AppConfig behavior
	•	AppConfig._ensure_defaults() sets sane defaults (above).
	•	Provide getters/setters for all keys.
	•	Overlay position:
	•	getter returns None if missing
	•	setter stores x,y and optional screen index

⸻

3) Services / modules

3.1 IdService
	•	Strategy "short_id":
	•	alphabet: [a-z0-9]
	•	default length 9 (clamped 6..32)
	•	Strategy "uuid4":
	•	uuid.uuid4() string

3.2 DateTimeService
	•	Default timezone: "Europe/Amsterdam"
	•	Use zoneinfo.ZoneInfo if available, else local time.
	•	Format: %Y%m%d

3.3 EntryFormatter
	•	format_loose_diary(entry) returns Mode A string (as per spec).
	•	format_strict_json(entry, pretty) returns valid JSON.

3.4 ClipboardService
	•	Writes string to general pasteboard.
	•	Raises RuntimeError on failure; caller shows NSAlert.

3.5 NotificationService (best-effort)
	•	If UserNotifications framework missing or fails: no crash.
	•	ensure_permission() request authorization (async).
	•	notify_copied(title, body) sends immediate notification (no trigger).
	•	Policy enforcement happens in AppController:
	•	off → no notifications
	•	hotkey_only → only source "hotkey"
	•	all → notify for menu/overlay/hotkey

3.6 HotkeyService (best-effort Carbon)
	•	If Carbon missing: return False, app continues without hotkey.
	•	Register RegisterEventHotKey with keycode/modifiers.
	•	Handler calls callback safely.
	•	Start/stop lifecycle (stop on terminate).

3.7 Import collision hardening (v0.3.1 bugfix must stay)

Always import NSObject/NSUserDefaults/NSLog via Cocoa first:

try:
    from Cocoa import NSObject, NSUserDefaults, NSLog
except Exception:
    from Foundation import NSObject, NSUserDefaults, NSLog


⸻

4) UI Components

4.1 Menu Bar UI (existing)

Status item: { }

Menu items:
	•	Generate Entry
	•	Generate with Prompt…
	•	Role submenu: user/system (checkmarks)
	•	Output Mode submenu: Mode A / Mode B (checkmarks)
	•	Notifications submenu: All / Hotkey only / Off (checkmarks)
	•	Settings…
	•	Hotkey Enabled (checkbox)
	•	Quit

State refresh method updates all checkmarks.

⸻

4.2 Prompt Panel (existing v0.3)

NSPanel with:
	•	Role popup (user/system)
	•	NSTextView multiline prompt
	•	Copy Entry button
	•	Cancel button

Callback contract:
	•	On copy → returns (role, prompt)
	•	On cancel → returns (None, None) no action

⸻

4.3 Settings Panel (existing v0.3)

Settings UI:
	•	Hotkey Enabled switch
	•	Hotkey display field
	•	Capture Hotkey…
	•	Reset hotkey
	•	Notifications dropdown
	•	Pretty JSON toggle
	•	Status line

Hotkey capture:
	•	Focusable view captures next keyDown event
	•	Requires ≥1 modifier (reject if none)
	•	Converts NSEvent modifierFlags → Carbon masks (best-effort)

Apply callback contract:
	•	"hotkey" enable/disable: start/stop; return (ok,err)
	•	"hotkey_candidate" validate candidate by temporary register; revert if conflict
	•	"notifications": ensure permission if not off
	•	"json": refresh only

⸻

5) Overlay Bubble UI (new v0.4)

5.1 High-level

A small always-on-top bubble window that provides fast access:
	•	left click: generate blank OR open prompt panel (config)
	•	right click: context menu
	•	draggable
	•	position persisted and clamped

5.2 Classes to add

OverlayBubbleController(NSObject)

Responsibilities:
	•	Create window/panel
	•	Build bubble view/button
	•	Apply settings:
	•	click action
	•	spaces behavior
	•	fullscreen hide behavior
	•	Show/hide/close
	•	Persist position on drag end

OverlayBubbleView(NSView) (or NSButton subclass)

Responsibilities:
	•	Handle mouseDown/mouseDragged/mouseUp for dragging
	•	Handle rightMouseDown for context menu
	•	Delegate click to controller callback(s)

5.3 Window choice & configuration

Window type

Prefer NSPanel (utility) OR NSWindow borderless.

Recommended for v0.4:
	•	NSPanel created with style masks:
	•	titled? not needed
	•	utility? yes
	•	borderless if possible
	•	If borderless masks are messy in PyObjC, fallback to small titled-less panel with hidden titlebar.

Always-on-top
	•	window.setLevel_(NSFloatingWindowLevel)

Transparency
	•	window.setOpaque_(False)
	•	background clear (use NSColor.clearColor if needed)
	•	bubble view draws its own background

5.4 Bubble appearance (minimum)
	•	Size: 44x44 (or 48)
	•	Rounded corners radius = size/2
	•	Text: { } (consistent with menu bar)
	•	Subtle alpha (optional later)

5.5 Click action

Config overlay_click_action:
	•	"generate_blank":
	•	call AppController.generate_and_copy(source="overlay")
	•	"open_prompt_panel":
	•	call AppController.onGenerateWithPrompt_(None) (or direct prompt controller show)

5.6 Right-click context menu

On right click: show menu at cursor location with:
	•	Generate Entry
	•	Generate with Prompt…
	•	Output Mode → (Mode A / Mode B) OR a single “Toggle Mode”
	•	Open Settings…
	•	Hide Overlay
	•	Quit

All items call the same AppController handlers as menu bar uses.

5.7 Dragging + persistence

Implement dragging without Accessibility:
	•	On mouseDown_: store start mouse location + initial window origin
	•	On mouseDragged_: move window origin by delta
	•	On mouseUp_: persist final origin in NSUserDefaults:
	•	overlay_pos_x, overlay_pos_y
	•	overlay_screen_index optional

5.8 Restore position + clamping

At overlay startup:
	•	Determine target screen:
	•	if saved screen index exists and valid → use it
	•	else use NSScreen.mainScreen() or screen containing saved point
	•	Load visibleFrame of screen
	•	Clamp:
	•	x between minX and maxX - bubbleWidth
	•	y between minY and maxY - bubbleHeight
	•	If no saved position: place top-right of visibleFrame with margin (e.g. 16px)

5.9 Spaces behavior

If overlay_show_all_spaces=True:
	•	Set collectionBehavior:
	•	NSWindowCollectionBehaviorCanJoinAllSpaces
	•	optionally NSWindowCollectionBehaviorStationary

If False:
	•	default

5.10 Fullscreen hide behavior

If overlay_hide_in_fullscreen=True (default):
	•	Do not set NSWindowCollectionBehaviorFullScreenAuxiliary
	•	Keep it as normal window so it won’t overlay fullscreen apps in practice.

If False:
	•	you may set auxiliary, but that tends to annoy; for v0.4 allow but default stays hidden.

No polling requirement is met.

⸻

6) AppController integration changes

6.1 New fields
	•	self.overlay_controller = None

6.2 Lifecycle

On launch:
	•	if config.overlay_enabled: start overlay

On terminate:
	•	close overlay best-effort

6.3 Start/stop
	•	_start_overlay():
	•	create OverlayBubbleController with:
	•	config reference
	•	callbacks to AppController actions (generate blank, prompt, settings, quit)
	•	show window
	•	_stop_overlay():
	•	close window and set controller None

6.4 Menu integration (minimum viable)

Add menu section “Overlay”:
	•	Overlay Enabled (checkbox)
	•	Overlay Click Action → Generate blank / Prompt panel
	•	Show on all Spaces (checkbox)
	•	Hide in fullscreen (checkbox)

Handlers:
	•	update config keys
	•	if enabled changed → start/stop overlay
	•	else → call overlay_controller.apply_settings()

6.5 Notification source

Overlay calls generate_and_copy(source="overlay") so policy works.

⸻

7) Packaging / py2app

7.1 Version consistency
	•	APP_VERSION = "0.4.0"
	•	setup.py plist:
	•	CFBundleShortVersionString = "0.4.0"
	•	CFBundleVersion = "0.4.0"

7.2 Includes

Normally PyObjC frameworks auto-resolve.
Only add explicit includes if py2app misses:
	•	UserNotifications (optional)
	•	Carbon (optional)

⸻

8) Test plan (smoke)

8.1 Regression v0.2/v0.3
	•	Mode A output matches expected string style.
	•	Mode B output valid JSON; pretty toggle works.
	•	Role selection affects output.
	•	id_strategy affects id.
	•	datumtijd correct (YYYYMMDD).
	•	Prompt panel multi-line works.
	•	Settings panel controls persist.
	•	Hotkey works or gracefully fails.
	•	Notifications policy works.

8.2 Overlay v0.4
	•	Enable overlay shows bubble
	•	Drag bubble → persists after restart
	•	Click action works (blank vs prompt)
	•	Right-click menu shows and items work
	•	Show on all spaces works
	•	Hide in fullscreen works (default ON)

⸻

9) CHANGELOG (complete vanaf v0.2)

[0.2.0] — (retro)

Added
	•	Mode A “loose diary” output (default)
	•	Mode B “strict JSON” output toggle
	•	JSON pretty toggle (Mode B)
	•	Role selection (user/system) + persistence
	•	ID strategy: short_id (default) / uuid4
	•	datumtijd strategy: YYYYMMDD (timezone-aware best-effort)
	•	NSUserDefaults config wrapper
	•	Menu bar UI: role submenu, output mode submenu

Fixed
	•	Consistent clipboard writes with error surfacing (alert on failure)

⸻

[0.3.0] — (retro)

Added
	•	Multiline Prompt Panel (NSPanel + NSTextView) “Generate with Prompt…”
	•	Notifications (UserNotifications) best-effort
	•	policy: all / hotkey_only / off
	•	permission request best-effort
	•	Global hotkey best-effort via Carbon
	•	enable/disable
	•	default Ctrl+Opt+Cmd+J
	•	Settings panel UI
	•	hotkey capture/apply/reset
	•	notifications mode
	•	pretty JSON toggle
	•	status feedback line
	•	Menu items:
	•	Notifications submenu
	•	Settings…
	•	Hotkey Enabled toggle

Fixed
	•	Graceful degradation when Carbon/UserNotifications unavailable

⸻

[0.3.1] — 2026-02-18

Fixed
	•	Robust imports for NSObject/NSUserDefaults/NSLog:
	•	prefer Cocoa with fallback to Foundation to avoid venv module name collisions
	•	Version consistency hygiene (align app + packaging)

Notes
	•	If a PyPI package named Foundation exists in a venv, uninstall it to prevent collisions.

⸻

[0.4.0] — (planned)

Added
	•	Overlay Bubble (Floating Button):
	•	always-on-top bubble window
	•	draggable + persisted position + screen clamping
	•	click action: generate blank OR open prompt panel
	•	right-click context menu for core actions
	•	show on all Spaces (default ON)
	•	hide in fullscreen (default ON)
	•	Menu controls for overlay settings:
	•	enable/disable
	•	click action selection
	•	spaces toggle
	•	fullscreen hide toggle

Changed
	•	Notifications source classification includes "overlay"; policy remains:
	•	all / hotkey_only / off

Fixed
	•	(none specific yet; implementasie fase)

⸻

10) Sanity re-check (versus stap 1)

✅ Alles uit v0.2 en v0.3/v0.3.1 is ingesluit: modes, role, id strategy, datumtijd tz, clipboard, prompt panel, notifications policy, hotkey + capture UI, settings panel, import-collision hardening, menu controls.
✅ Overlay v0.4 volledige requirements ingesluit.

⸻

Volgende opsies
	1.	Direk na code v0.4: ek genereer commit-ready blokke (overlay controller + view + menu items + config keys + version bump + changelog bump)
	2.	Build plan v0.4 herskryf op basis van hierdie TS (as jy ’n strakker step-by-step wil hê)
	3.	FS v0.4 refine (snap-to-edge, opacity/size controls, auto-start on login)

Kies 1 / 2 / 3.
