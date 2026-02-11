# Changelog

## [0.2.0] - 2026-02-11
### Added
- Output Mode toggle in the menu:
  - Mode A: Loose diary format (default)
  - Mode B: Strict JSON (valid JSON)
- Strict JSON formatter (pretty-printed JSON)

### Changed
- Internal version bump from initial MVP

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
