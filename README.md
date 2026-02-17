# Clipboard JSON Logger (macOS)

A tiny macOS menu bar utility that generates a “chatlog entry” and copies it to the clipboard with one click or a global hotkey. Built in **Python + PyObjC** for native AppKit integration on macOS.

<img src="./img/app_demo1.png">

## Why this exists

If you keep an online diary / running log and want every entry to have:
- a unique `id`
- a `role` (e.g., `user` or `system`)
- a `prompt`
- a date stamp (`datumtijd` in `YYYYMMDD`)

…generating those fields manually breaks flow. This tool makes it instant: **Generate → Paste → Continue writing**.

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
