# Clipboard JSON Logger (macOS)

A tiny macOS menu bar utility that generates a “chatlog entry” and copies it to the clipboard with one click or a global hotkey. Built in **Python + PyObjC** for native AppKit integration on macOS.

<img src="./img/app_demo1.png">

Built for fast journaling / logging workflows where you paste structured blocks into a text editor.

## What it does
- 1 click (or hotkey) → generate entry block(s) → **clipboard**
- Two output modes:
  - **Mode A (default):** loose diary format (intentionally not strict JSON)
  - **Mode B:** strict JSON (valid JSON) + pretty toggle
- Roles:
  - `user`
  - `system`
  - **User + system** → generates **two blocks** with the **same `id`** and **same `datumtijd`**
- Prompt panel: multiline prompt input
- Notifications: All / Hotkey only / Off (best-effort)
- Global hotkey: best-effort Carbon hotkey + capture UI (if available)
- Overlay bubble (floating button): draggable, always-on-top, optional
- UI language:
  - Default **Afrikaans**
  - Switch language **without app restart**
- Config export/import:
  - write settings to local JSON file
  - read/apply JSON at startup and on demand

## Why this exists

If you keep an online diary / running log and want every entry to have:
- a unique `id`
- a `role` (e.g., `user` or `system`)
- a `prompt`
- a date stamp (`datumtijd` in `YYYYMMDD`)

…generating those fields manually breaks flow. This tool makes it instant: **Generate → Paste → Continue writing**.

# Ontwikkelcyclus
<img src="./img/ontwikkelcyclusAI.jpg" width="60%" height="60%">


## Output modes

### Mode A — “Loose diary” (default)
Intentionally not strict JSON; matches a diary-friendly loose format for maximum copy/paste convenience.

Example:
```text
{'id': 'efeqer3fr', role: 'system', prompt: """
Hello diary
"""
,
datumtijd: "20260214"
},
```

# Optioneel: Build MacOS frontend
```
python3 -m pip install -U py2app
python3 setup.py py2app
```

# Dev setup
``` bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -U pyobjc py2app
# Optional if you get missing UserNotifications:
python -m pip install -U pyobjc-framework-UserNotifications
```

## PyObjC Foundation import collisions

If you ever see import errors like cannot import name 'NSObject' from 'Foundation',
your venv may contain a conflicting PyPI package named Foundation.

Fix:
```bash
pip uninstall -y Foundation
pip install -U pyobjc-core pyobjc-framework-Cocoa pyobjc-framework-UserNotifications
```


# Run code

```python
python src/clipboard_json_logger.py
```

# Credits
Michiel Erasmus
