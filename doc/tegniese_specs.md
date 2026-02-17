# Technical Specification (TS) — Clipboard JSON Logger
**Version:** 0.4 (TS v0.4.0)  
**Date:** 2026-02-17  
**Platform:** macOS menu bar app (PyObjC)  
**Language:** Python 3.12  
**Packaging:** py2app  
**Code style:** modular + class-based, prefer single-file app module (`src/clipboard_json_logger.py`)  

---

## 0. Sanity check (TS v0.4 completeness)
Hierdie dokument is die **volledige TS v0.4** (nie ’n opsomming nie).

### Features wat TS v0.4 móét dek (checklist)
- [x] Menu bar status item + menus/submenus + checkmarks
- [x] Entry model: id/role/prompt/datumtijd
- [x] ID strategies: short_id vs uuid4
- [x] datumtijd: YYYYMMDD with timezone best-effort (Europe/Amsterdam default)
- [x] Output mode: Mode A loose diary (default)
- [x] Output mode: Mode B strict JSON + pretty toggle
- [x] Prompt panel: multiline prompt + role override
- [x] Clipboard service: write to NSPasteboard, errors -> NSAlert
- [x] Notifications: best-effort UserNotifications + policy All/Hotkey only/Off
- [x] Global hotkey: best-effort Carbon + enable/disable + capture UI + reset + conflict handling
- [x] Settings panel: hotkey enabled, capture/apply/reset, notifications mode, pretty JSON
- [x] Overlay Bubble (floating button): enable/disable, always-on-top, draggable, position persistence
- [x] Overlay options: click action, show on all Spaces, hide in fullscreen, context menu
- [x] Persistence via NSUserDefaults for all settings incl overlay state/pos
- [x] Packaging notes (py2app) + Info.plist keys, LSUIElement, entitlements note
- [x] Logging policy (NSLog only, no prompt persisted)

✅ As jy iets hier mis sien, is dit ’n bug in TS v0.4 — maar ek het alles ingesluit.

---

## 1. Architecture overview
Single-process macOS app using Cocoa event loop via PyObjC.

### 1.1 Modules/classes (logical)
- **Domain**
  - `EntryModel` (dataclass): `id`, `role`, `prompt`, `datumtijd`
- **Config**
  - `AppConfig`: wrapper around `NSUserDefaults`, default seeding, getters/setters
- **Services**
  - `IdService`: `short_id` or `uuid4`
  - `DateTimeService`: timezone best-effort `YYYYMMDD`
  - `EntryFormatter`: Mode A vs Mode B (+ pretty)
  - `ClipboardService`: NSPasteboard writes
  - `NotificationService`: best-effort UserNotifications
  - `HotkeyService`: best-effort Carbon global hotkey
- **UI Controllers**
  - `AppController`: NSApplication delegate; menu wiring; orchestration
  - `PromptPanelController`: NSPanel + NSTextView (multiline)
  - `SettingsPanelController`: preferences UI + hotkey capture/apply
  - `HotkeyCaptureView`: captures keyDown for hotkey (first responder)
  - `OverlayBubbleController` (NEW v0.4): floating NSPanel/NSWindow acting as draggable bubble
  - `OverlayBubbleView` (NEW v0.4): draws bubble button and handles mouse events
  - `OverlayMenuFactory` (optional helper): build context menu for overlay

### 1.2 Key design constraints
- Keep core logic separate from UI callbacks (services called from controllers).
- Degrade gracefully if optional frameworks missing (`Carbon`, `UserNotifications`).
- Avoid persisting prompt content (only write to clipboard and pass through formatter).
- Default output remains Mode A.

---

## 2. Data & persistence (NSUserDefaults)
### 2.1 Existing keys (v0.3.x)
- `default_role`: `"user"|"system"`
- `id_strategy`: `"short_id"|"uuid4"`
- `output_mode`: `"loose_diary"|"strict_json"`
- `datumtijd_strategy`: `"date_yyyymmdd"`
- `hotkey_enabled`: bool
- `hotkey_keycode`: int
- `hotkey_modifiers`: int (Carbon masks)
- `notifications_mode`: `"all"|"hotkey_only"|"off"`
- `json_pretty`: bool

### 2.2 New keys (v0.4 overlay)
Add these keys:
- `overlay_enabled`: bool
- `overlay_click_action`: `"generate_blank"|"open_prompt_panel"`
- `overlay_show_all_spaces`: bool
- `overlay_hide_in_fullscreen`: bool
- `overlay_pos_x`: float
- `overlay_pos_y`: float
- `overlay_screen_hint`: int (optional best-effort; -1 if unknown)

Defaults:
- overlay disabled by default (`false`) unless you decide otherwise.
- click action default: `generate_blank`
- show all spaces default: `true`
- hide in fullscreen default: `true`
- pos default: top-right-ish offset from main screen visible frame.

---

## 3. Entry generation pipeline
### 3.1 Make entry
`AppController._make_entry(role, prompt)`:
- `id = IdService.generate()` using `AppConfig.id_strategy`
- `datumtijd = DateTimeService.datumtijd_yyyymmdd()`
- return `EntryModel(id, role, prompt, datumtijd)`

### 3.2 Format entry
`AppController._format_entry(entry)`:
- if output_mode == `strict_json`:
  - `EntryFormatter.format_strict_json(entry, pretty=config.json_pretty)`
- else:
  - `EntryFormatter.format_loose_diary(entry)`

### 3.3 Copy to clipboard
`ClipboardService.copy_text(text)`:
- `NSPasteboard.generalPasteboard()`
- `declareTypes_owner_([NSStringPboardType], None)`
- `setString_forType_`
- if fails: raise `RuntimeError` → caller shows NSAlert

### 3.4 Notifications
`NotificationService.notify_copied(title, body)`:
- if UN not available: no-op
- call `ensure_permission()` (idempotent)
- create `UNMutableNotificationContent`
- create immediate `UNNotificationRequest` (trigger None)
- add request; swallow errors (NSLog only)

Policy decision:
`AppController._should_notify(source)`:
- `off` => False
- `hotkey_only` => source == "hotkey"
- `all` => True

Sources:
- `"menu"`, `"hotkey"`, `"overlay"`

---

## 4. UI: Menu bar app
### 4.1 Status item
- Use `NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)`
- Title or template image, e.g. `{ }`

### 4.2 Menu structure
Menu items (top-level):
1. Generate Entry
2. Generate with Prompt…
3. Separator
4. Role submenu: user/system (checkmark)
5. Output Mode submenu: Mode A / Mode B (checkmark)
6. Notifications submenu: All / Hotkey only / Off (checkmark)
7. Overlay submenu (NEW v0.4)
8. Separator
9. Settings…
10. Hotkey Enabled (toggle)
11. Separator
12. Quit

Checkmark refresh:
`AppController._refresh_menu_states()` updates:
- role checks
- output mode checks
- notifications checks
- hotkey enabled check
- overlay checks (enabled/click-action/spaces/fullscreen)

### 4.3 Event handlers
- `onGenerateEntry_` → `generate_and_copy(source="menu")`
- `onGenerateWithPrompt_` → show prompt panel; callback copies
- Role toggles set `default_role`
- Mode toggles set `output_mode`
- Notification toggles set `notifications_mode` and possibly request permission
- Overlay toggles call overlay controller to show/hide or update behavior
- Settings opens settings panel
- Hotkey toggle calls start/stop hotkey and persists

---

## 5. UI: Prompt panel (multiline)
### 5.1 Controls
- `NSPanel` (utility window style)
- `NSPopUpButton`: role selection (user/system)
- `NSScrollView` with `NSTextView`: multiline prompt
- Buttons: Copy Entry, Cancel

### 5.2 Callback contract
`PromptPanelController` calls back:
- `(role, prompt)` on Copy
- `(None, None)` on Cancel

App behavior:
- On callback success: `generate_and_copy(role_override=role, prompt=prompt, source="menu")`

---

## 6. UI: Settings panel + hotkey capture
### 6.1 Controls
- Hotkey enabled switch (NSSwitchButton)
- Label showing current hotkey (⌃⌥⌘J format)
- Capture Hotkey… button
- Reset button
- Notifications mode popup (All/Hotkey only/Off)
- Pretty JSON toggle
- Status label line

### 6.2 Hotkey capture behavior
Implementation:
- Invisible focusable `HotkeyCaptureView` as first responder when capturing
- On keyDown:
  - read `event.keyCode()`
  - read `event.modifierFlags()`
  - map to Carbon masks (only if Carbon available)
- Validation:
  - reject if modifiers == 0 (must have at least one)
- Apply:
  - call `AppController.apply_settings("hotkey_candidate", (keycode, modifiers))`
  - if ok: persist via `AppConfig.set_hotkey(...)`
  - if not ok: show error in status line, revert to previous

### 6.3 Hotkey conflict handling
- When applying candidate:
  - stop current hotkey
  - attempt register candidate
  - if fail: attempt re-register previous; report conflict/unavailable

---

## 7. Global hotkey (Carbon) — best-effort
### 7.1 Availability
- `CARBON_AVAILABLE` only if `from Carbon import Events, HIToolbox` succeeds.

### 7.2 Register
Use:
- `Events.InstallApplicationEventHandler(...)`
- `Events.RegisterEventHotKey(keycode, modifiers, hotkey_id, target, 0, hotkey_ref)`

Callback:
- triggers `AppController.generate_and_copy(source="hotkey")`

### 7.3 Stop
- `Events.UnregisterEventHotKey(hotkey_ref)` best-effort

---

## 8. Overlay Bubble (Floating Button) — v0.4
### 8.1 Window type & behavior
Use an `NSPanel` or borderless `NSWindow` configured as floating utility:

Recommended:
- `NSPanel` with style:
  - titled off / borderless look (may still use utility window)
- Set:
  - `setFloatingPanel_(True)` (if NSPanel)
  - `setLevel_(NSStatusWindowLevel or NSFloatingWindowLevel)`
  - `setOpaque_(False)` + `setBackgroundColor_(clear)`
  - `setHasShadow_(True)` optional
  - `setIgnoresMouseEvents_(False)`

Always-on-top:
- `setLevel_(NSFloatingWindowLevel)` or similar.

No activation stealing:
- Consider `setHidesOnDeactivate_(False)` so it stays visible.
- Keep it lightweight; avoid becoming key window unless needed.

### 8.2 Show on all Spaces / fullscreen policy
- **Show on all Spaces**:
  - `collectionBehavior` includes `NSWindowCollectionBehaviorCanJoinAllSpaces`
- **Hide in fullscreen**:
  - If enabled: also include `NSWindowCollectionBehaviorFullScreenAuxiliary` decisions carefully.
  - Practical approach:
    - If hide_in_fullscreen = true: remove `FullScreenAuxiliary` and rely on default hiding OR explicitly manage with workspace notifications (optional).
    - If hide_in_fullscreen = false: include `NSWindowCollectionBehaviorFullScreenAuxiliary` so it can appear over fullscreen apps.

Implementation note:
- Cocoa flags can be finicky; TS requirement is functional, not perfect across every edge case.
- Start with behavior flags; if needed add workspace/fullscreen observers later.

### 8.3 Bubble view (hit targets)
`OverlayBubbleView`:
- Draw a rounded bubble (circle/pill) with `{ }` label.
- Handle events:
  - `mouseDown_`: record starting point
  - `mouseDragged_`: move window
  - `mouseUp_`: persist position
  - `rightMouseDown_` (or ctrl-click): open context menu

### 8.4 Dragging & persistence
On drag end:
- Determine window frame origin in screen coordinates.
- Save:
  - `overlay_pos_x`, `overlay_pos_y`
  - screen hint optional:
    - find which `NSScreen` contains most of the window; store index

On launch:
- If overlay enabled:
  - restore position
  - clamp position to visibleFrame of target screen:
    - ensure bubble not off-screen
  - if screen hint invalid, use main screen.

### 8.5 Click action
Config: `overlay_click_action`:
- `"generate_blank"`: call `generate_and_copy(source="overlay")`
- `"open_prompt_panel"`: call existing prompt panel show

### 8.6 Context menu
On right-click, show menu with:
- Generate Entry
- Generate with Prompt…
- Output Mode:
  - Loose diary (Mode A)
  - Strict JSON (Mode B)
- Open Settings…
- Hide Overlay
- Quit

Menu actions call back into `AppController` handlers (reuse existing logic).

### 8.7 Overlay enable/disable
- If disabled:
  - close window (orderOut / close)
- If enabled:
  - create controller if needed, show window

---

## 9. AppController orchestration changes (v0.4)
### 9.1 New fields
- `self.overlay = None` (OverlayBubbleController)
- Menu items for overlay submenu stored as ivars for state updates

### 9.2 Launch behavior
`applicationDidFinishLaunching_`:
- setup menu bar
- start hotkey if enabled
- request notifications permission if policy != off
- if overlay_enabled: show overlay

### 9.3 Settings application
When toggles change:
- call overlay controller update:
  - enabled
  - click action
  - show all spaces
  - hide in fullscreen

---

## 10. Logging & diagnostics
- Use `NSLog` for:
  - app launch version
  - clipboard copy success (metadata only: role/mode/id_strategy)
  - errors: hotkey registration fail, notification fail
- Do **not** log prompt content.

---

## 11. Packaging (py2app)
### 11.1 setup.py essentials
- `app=["src/clipboard_json_logger.py"]`
- include packages:
  - `pyobjc`, `pyobjc-framework-Cocoa`
  - optional `pyobjc-framework-UserNotifications` (if needed)
- `plist` settings:
  - `CFBundleName`, `CFBundleIdentifier`
  - `CFBundleShortVersionString` = `0.4.x`
  - `NSHumanReadableCopyright`
  - `LSUIElement` = `True` (menu bar app, no Dock)

### 11.2 Notarization/signing (optional)
- Not required for local run, but recommended if you distribute.
- Hotkey + notifications may behave differently under unsigned builds; test both.

---

## 12. Testing plan (technical)
### 12.1 Smoke tests
- Menu: Generate Entry copies to clipboard (paste into text editor)
- Prompt panel: multiline prompt preserved
- Mode A output matches expected diary format
- Mode B output is valid JSON (use `python -c 'import json; ...'` on pasted content)
- Pretty toggle affects indentation
- Role toggles persist across restart
- Notifications:
  - policy off = no notifications
  - hotkey_only = only hotkey triggers notification
- Hotkey:
  - enabled, triggers copy
  - capture new combo, conflict handling
- Overlay:
  - enable shows bubble
  - click action works (blank or prompt)
  - drag persists across restart
  - context menu works
  - show on all spaces toggle changes behavior
  - hide in fullscreen toggle behaves acceptably

### 12.2 Regression tests
- If Carbon missing: app still runs, settings shows message
- If UserNotifications missing: app still runs, no crash

---

## 13. CHANGELOG requirements (from v0.2)
TS implies CHANGELOG must include:
- Added/Changed/Fixed per version
- Mention best-effort fallbacks
- Note overlay introduction in v0.4

(CHANGELOG content itself lives in `CHANGELOG.md`, but TS defines required coverage.)

---

## 14. Implementation notes / pitfalls
- **Spaces/fullscreen:** window collection behaviors differ; treat as “best-effort”.
- **Multiple screens:** store a screen hint but always clamp to visibleFrame to avoid lost overlay.
- **Hotkey flags:** NSEvent modifierFlags mapping is brittle; keep Carbon masks as the stored truth.
- **Clipboard type:** `NSStringPboardType` works; newer APIs exist but keep stable.
- **Foundation import collision:** prefer `from Cocoa import ...` fallback to `Foundation`.

---

✅ Sanity check: Ek het die volledige TS v0.4 hierbo ge-output as één GitHub-ready .md blok. Geen afdelings is weggelaat.

⸻

# Volgende opsies (kies net ’n nommer)
```
	1.	Build plan v0.4 (retrofit + actionable steps, commands, smoke tests, release checklist)
	2.	Direk na code: v0.4 commit-ready blokke (updated clipboard_json_logger.py + README + setup.py + CHANGELOG)
	3.	Verbeter die overlay: snap-to-edge + opacity/size sliders (FS/TS addendum)
	4.	Auto-start at login (LaunchAgent/SMAppService) plan + implementasie opsies
	5.	Entry templates (custom fields + presets) voorstel vir v0.5
```
