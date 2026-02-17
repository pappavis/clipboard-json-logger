# Changelog

### Notes
- Prompt input is single-line in the MVP dialog; multi-line prompt UI planned.

## [0.1.0] - 2026-02-11
### Added
- macOS menu bar app (PyObjC)
- Generate Entry → clipboard
- Generate with Prompt… (single-line)
- Role selection (user/system)
- ID strategies: short_id (default), uuid4
- datumtijd in YYYYMMDD
- Best-effort global hotkey (Carbon where available)


## [0.2.0] - 2026-02-11
### Added
- Output Mode toggle in the menu:
  - Mode A: Loose diary format (default)
  - Mode B: Strict JSON (valid JSON)
- Strict JSON formatter (pretty-printed JSON)

### Changed
- Internal version bump from initial MVP


## [0.4.0] - 2026-02-18
### Added
- Overlay Bubble (Floating Button):
  - Always-on-top floating bubble window
  - Draggable with persisted position
  - Click action configurable: Generate blank / Open prompt panel
  - Right-click context menu for core actions
  - Show on all Spaces (default ON)
  - Hide in fullscreen (default ON)

### Changed
- Notifications source now includes `overlay` triggers; policy unchanged (all / hotkey_only / off).

## [0.3.1] - 2026-02-18
### Fixed
- Import collision hardening: prefer `Cocoa` for `NSObject/NSUserDefaults/NSLog`, fallback to `Foundation`.
- Version consistency hygiene.

## [0.3.0] - (retro)
### Added
- Multiline prompt panel (NSPanel + NSTextView) + role override.
- Notifications (UserNotifications) best-effort, with policy: all / hotkey_only / off.
- Global hotkey (Carbon) best-effort:
  - Enable/disable, default Ctrl+Opt+Cmd+J
- Settings panel:
  - Hotkey capture/apply/reset
  - Notifications selector
  - Pretty JSON toggle (Mode B)
  - Status feedback line
- Menu items for Settings + Notifications + Hotkey toggle.

### Fixed
- Graceful degradation when Carbon/UserNotifications are unavailable.

## [0.2.0] - (retro)
### Added
- Mode A (loose diary) output as default.
- Mode B (strict JSON) toggle + pretty JSON option.
- Role selection (user/system) persisted via NSUserDefaults.
- ID strategy: short_id (default) or uuid4.
- datumtijd as YYYYMMDD (timezone-aware best-effort).
