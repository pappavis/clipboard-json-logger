# Changelog — Clipboard JSON Logger

All notable changes to this project will be documented in this file.

## [0.5.0] — 2026-02-18
### Added
- Role option **User + system**: generates **two blocks** with the **same `id`** + `datumtijd` and copies both to clipboard (blank line separator).
- UI language support:
  - Default language **Afrikaans**
  - Runtime language switching (no restart) for menu + panels.
- Local JSON config file:
  - Export settings to `~/Library/Application Support/Clipboard JSON Logger/config.json`
  - Import/apply on startup and via Settings panel.

### Changed
- Internal entry generation now supports multi-block output.
- UI text is now driven by an i18n string table.

### Fixed
- More defensive startup behavior: config load failures do not crash the app.

---

## [0.4.0] — 2026-02-18
### Added
- Overlay Bubble (floating button):
  - enable/disable
  - draggable + position persistence
  - always-on-top
  - click action: generate blank OR open prompt panel
  - right-click context menu
  - show on all Spaces toggle
  - hide in fullscreen toggle (best-effort)

---

## [0.3.1] — 2026-02-18
### Fixed
- Avoid `Foundation` import collisions by preferring `Cocoa` import with fallback.
- General stability improvements for PyObjC environments.

---

## [0.3.0] — 2026-02-18
### Added
- Multiline prompt panel (NSPanel + NSTextView).
- Notifications (best-effort UserNotifications) with policy: All / Hotkey only / Off.
- Settings panel: hotkey capture + apply, notifications mode, pretty JSON toggle.
- Global hotkey (best-effort Carbon).

---

## [0.2.0] — 2026-02-17
### Added
- Mode A: loose diary output (default).
- Mode B: strict JSON output (toggle).
- Role selection (user/system).
- ID generation strategies (short_id / uuid4).
- datumtijd generation (YYYYMMDD).

---

## [0.1.0] — 2026-02-17
### Added
- Initial prototype: generate entry and copy to clipboard from a minimal UI entry point.
