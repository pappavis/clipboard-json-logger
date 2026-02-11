---

## `clipboard_json_logger.py`
```python
# Clipboard JSON Logger
# Version: 0.2.0
# Date: 2026-02-11
#
# macOS Menu Bar utility (PyObjC) to generate a "chatlog entry"
# and copy it to the clipboard.
#
# Output modes:
# - Mode A: loose diary format (default)
# - Mode B: strict JSON

from __future__ import annotations

import json
import secrets
import string
import uuid
from dataclasses import dataclass
from datetime import datetime

try:
    # Python 3.9+
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None  # type: ignore

import objc
from Foundation import NSObject, NSUserDefaults, NSLog
from AppKit import (
    NSApplication,
    NSStatusBar,
    NSVariableStatusItemLength,
    NSMenu,
    NSMenuItem,
    NSPasteboard,
    NSStringPboardType,
    NSAlert,
    NSTextField,
    NSControlStateValueOn,
    NSControlStateValueOff,
)
from PyObjCTools import AppHelper

# ---- Optional Carbon hotkey (best-effort) ----
CARBON_AVAILABLE = False
try:
    import Carbon
    from Carbon import Events
    from Carbon import HIToolbox

    CARBON_AVAILABLE = True
except Exception:
    CARBON_AVAILABLE = False


APP_NAME = "Clipboard JSON Logger"
APP_VERSION = "0.2.0"
APP_BUILD_DATE = "2026-02-11"

DEFAULT_TIMEZONE = "Europe/Amsterdam"

# NSUserDefaults keys
K_DEFAULT_ROLE = "default_role"
K_ID_STRATEGY = "id_strategy"  # short_id | uuid4
K_OUTPUT_MODE = "output_mode"  # loose_diary | strict_json
K_DATUMTIJD_STRATEGY = "datumtijd_strategy"  # date_yyyymmdd
K_HOTKEY_ENABLED = "hotkey_enabled"
K_HOTKEY_KEYCODE = "hotkey_keycode"
K_HOTKEY_MODIFIERS = "hotkey_modifiers"


@dataclass(frozen=True)
class EntryModel:
    id: str
    role: str
    prompt: str
    datumtijd: str


class AppConfig:
    """
    Thin wrapper around NSUserDefaults with sane defaults.
    """

    def __init__(self) -> None:
        self.ud = NSUserDefaults.standardUserDefaults()
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        if self.ud.objectForKey_(K_DEFAULT_ROLE) is None:
            self.ud.setObject_forKey_("user", K_DEFAULT_ROLE)

        if self.ud.objectForKey_(K_ID_STRATEGY) is None:
            self.ud.setObject_forKey_("short_id", K_ID_STRATEGY)

        if self.ud.objectForKey_(K_OUTPUT_MODE) is None:
            self.ud.setObject_forKey_("loose_diary", K_OUTPUT_MODE)

        if self.ud.objectForKey_(K_DATUMTIJD_STRATEGY) is None:
            self.ud.setObject_forKey_("date_yyyymmdd", K_DATUMTIJD_STRATEGY)

        if self.ud.objectForKey_(K_HOTKEY_ENABLED) is None:
            self.ud.setBool_forKey_(True, K_HOTKEY_ENABLED)

        # Default hotkey: Ctrl+Option+Command+J (best-effort)
        if self.ud.objectForKey_(K_HOTKEY_KEYCODE) is None:
            # kVK_ANSI_J if Carbon available; else store fallback int
            self.ud.setInteger_forKey_(HIToolbox.kVK_ANSI_J if CARBON_AVAILABLE else 38, K_HOTKEY_KEYCODE)

        if self.ud.objectForKey_(K_HOTKEY_MODIFIERS) is None:
            default_mods = 0
            if CARBON_AVAILABLE:
                default_mods = HIToolbox.controlKey | HIToolbox.optionKey | HIToolbox.cmdKey
            self.ud.setInteger_forKey_(int(default_mods), K_HOTKEY_MODIFIERS)

        self.ud.synchronize()

    # --- getters ---
    @property
    def default_role(self) -> str:
        return str(self.ud.stringForKey_(K_DEFAULT_ROLE) or "user")

    @property
    def id_strategy(self) -> str:
        return str(self.ud.stringForKey_(K_ID_STRATEGY) or "short_id")

    @property
    def output_mode(self) -> str:
        return str(self.ud.stringForKey_(K_OUTPUT_MODE) or "loose_diary")

    @property
    def datumtijd_strategy(self) -> str:
        return str(self.ud.stringForKey_(K_DATUMTIJD_STRATEGY) or "date_yyyymmdd")

    @property
    def hotkey_enabled(self) -> bool:
        return bool(self.ud.boolForKey_(K_HOTKEY_ENABLED))

    @property
    def hotkey_keycode(self) -> int:
        return int(self.ud.integerForKey_(K_HOTKEY_KEYCODE))

    @property
    def hotkey_modifiers(self) -> int:
        return int(self.ud.integerForKey_(K_HOTKEY_MODIFIERS))

    # --- setters ---
    def set_default_role(self, role: str) -> None:
        self.ud.setObject_forKey_(role, K_DEFAULT_ROLE)
        self.ud.synchronize()

    def set_id_strategy(self, strategy: str) -> None:
        self.ud.setObject_forKey_(strategy, K_ID_STRATEGY)
        self.ud.synchronize()

    def set_output_mode(self, mode: str) -> None:
        self.ud.setObject_forKey_(mode, K_OUTPUT_MODE)
        self.ud.synchronize()

    def set_hotkey_enabled(self, enabled: bool) -> None:
        self.ud.setBool_forKey_(bool(enabled), K_HOTKEY_ENABLED)
        self.ud.synchronize()


class IdService:
    def __init__(self, strategy: str = "short_id", short_len: int = 9) -> None:
        self.strategy = strategy
        self.short_len = max(6, min(int(short_len), 32))
        self._chars = string.ascii_lowercase + string.digits

    def generate(self) -> str:
        if self.strategy == "uuid4":
            return str(uuid.uuid4())
        # short_id
        return "".join(secrets.choice(self._chars) for _ in range(self.short_len))


class DateTimeService:
    def __init__(self, timezone_name: str = DEFAULT_TIMEZONE) -> None:
        self.timezone_name = timezone_name

    def datumtijd_yyyymmdd(self) -> str:
        if ZoneInfo is not None:
            try:
                tz = ZoneInfo(self.timezone_name)
                return datetime.now(tz).strftime("%Y%m%d")
            except Exception:
                pass
        return datetime.now().strftime("%Y%m%d")


class EntryFormatter:
    """
    Mode A: loose diary format
    Mode B: strict JSON (valid JSON)
    """

    @staticmethod
    def format_loose_diary(entry: EntryModel) -> str:
        # Emit prompt as a triple-quote-like block for consistency with diary style.
        prompt_text = entry.prompt or ""
        return (
            "{'id': '"
            + entry.id
            + "', role: '"
            + entry.role
            + "', prompt: \"\"\"\n"
            + prompt_text
            + "\n\"\"\"\n"
            + ",\n"
            + 'datumtijd: "'
            + entry.datumtijd
            + '"\n'
            + "},"
        )

    @staticmethod
    def format_strict_json(entry: EntryModel) -> str:
        payload = {
            "id": entry.id,
            "role": entry.role,
            "prompt": entry.prompt or "",
            "datumtijd": entry.datumtijd,
        }
        # Pretty JSON is easier to read in logs; still valid for copy/paste.
        return json.dumps(payload, ensure_ascii=False, indent=2)


class ClipboardService:
    def __init__(self) -> None:
        self.pb = NSPasteboard.generalPasteboard()

    def copy_text(self, text: str) -> None:
        self.pb.declareTypes_owner_([NSStringPboardType], None)
        ok = self.pb.setString_forType_(text, NSStringPboardType)
        if not ok:
            raise RuntimeError("Failed to write to NSPasteboard")


class HotkeyService:
    """
    Best-effort global hotkey using Carbon RegisterEventHotKey (if available).
    If Carbon isn't available or registration fails, app continues without hotkey.
    """

    def __init__(self, keycode: int, modifiers: int, on_trigger) -> None:
        self.keycode = int(keycode)
        self.modifiers = int(modifiers)
        self.on_trigger = on_trigger
        self._hotkey_ref = None

    def start(self) -> bool:
        if not CARBON_AVAILABLE:
            return False

        try:
            event_type = Events.EventTypeSpec(Events.kEventClassKeyboard, Events.kEventHotKeyPressed)

            def _handler(next_handler, the_event, user_data):
                try:
                    self.on_trigger()
                except Exception as e:
                    NSLog("Hotkey callback error: %@", str(e))
                return 1

            self._event_handler = Events.EventHandlerUPP(_handler)
            Events.InstallApplicationEventHandler(self._event_handler, 1, (event_type,), None, None)

            hotkey_id = Events.EventHotKeyID(0x4A4C4F47, 1)  # 'JLOG' + id=1
            hotkey_ref = Events.EventHotKeyRef()
            status = Events.RegisterEventHotKey(
                self.keycode,
                self.modifiers,
                hotkey_id,
                Events.GetApplicationEventTarget(),
                0,
                hotkey_ref,
            )
            if status != 0:
                return False

            self._hotkey_ref = hotkey_ref
            return True
        except Exception as e:
            NSLog("Hotkey registration failed: %@", str(e))
            return False

    def stop(self) -> None:
        if not CARBON_AVAILABLE:
            return
        try:
            if self._hotkey_ref is not None:
                Events.UnregisterEventHotKey(self._hotkey_ref)
        except Exception:
            pass


class AppController(NSObject):
    def init(self):
        self = objc.super(AppController, self).init()
        if self is None:
            return None

        self.config = AppConfig()
        self.id_service = IdService(strategy=self.config.id_strategy)
        self.dt_service = DateTimeService()
        self.formatter = EntryFormatter()
        self.clipboard = ClipboardService()

        self.status_item = None
        self.menu = None

        self.hotkey = None
        return self

    def applicationDidFinishLaunching_(self, notification):
        NSLog("%@ v%@ (%@) launching", APP_NAME, APP_VERSION, APP_BUILD_DATE)
        self._setup_menu_bar()

        if self.config.hotkey_enabled:
            self._start_hotkey()

    # ---------- UI setup ----------
    def _setup_menu_bar(self):
        self.status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
        self.status_item.setTitle_("{ }")

        self.menu = NSMenu.alloc().init()

        # Generate Entry
        mi_gen = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Generate Entry", "onGenerateEntry:", "")
        mi_gen.setTarget_(self)
        self.menu.addItem_(mi_gen)

        # Generate with Prompt...
        mi_prompt = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Generate with Prompt…", "onGenerateWithPrompt:", "")
        mi_prompt.setTarget_(self)
        self.menu.addItem_(mi_prompt)

        self.menu.addItem_(NSMenuItem.separatorItem())

        # Role submenu
        role_menu = NSMenu.alloc().init()
        self.mi_role_user = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("user", "onSetRoleUser:", "")
        self.mi_role_user.setTarget_(self)
        role_menu.addItem_(self.mi_role_user)

        self.mi_role_system = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("system", "onSetRoleSystem:", "")
        self.mi_role_system.setTarget_(self)
        role_menu.addItem_(self.mi_role_system)

        role_root = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Role", None, "")
        role_root.setSubmenu_(role_menu)
        self.menu.addItem_(role_root)

        # Output mode submenu
        mode_menu = NSMenu.alloc().init()
        self.mi_mode_loose = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Loose diary (Mode A)", "onSetModeLoose:", "")
        self.mi_mode_loose.setTarget_(self)
        mode_menu.addItem_(self.mi_mode_loose)

        self.mi_mode_strict = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Strict JSON (Mode B)", "onSetModeStrict:", "")
        self.mi_mode_strict.setTarget_(self)
        mode_menu.addItem_(self.mi_mode_strict)

        mode_root = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Output Mode", None, "")
        mode_root.setSubmenu_(mode_menu)
        self.menu.addItem_(mode_root)

        self.menu.addItem_(NSMenuItem.separatorItem())

        # Hotkey toggle
        self.mi_hotkey = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Hotkey Enabled", "onToggleHotkey:", "")
        self.mi_hotkey.setTarget_(self)
        self.menu.addItem_(self.mi_hotkey)

        self.menu.addItem_(NSMenuItem.separatorItem())

        # Quit
        mi_quit = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit", "terminate:", "q")
        self.menu.addItem_(mi_quit)

        self.status_item.setMenu_(self.menu)
        self._refresh_menu_states()

    def _refresh_menu_states(self):
        # Role
        role = self.config.default_role
        self.mi_role_user.setState_(NSControlStateValueOn if role == "user" else NSControlStateValueOff)
        self.mi_role_system.setState_(NSControlStateValueOn if role == "system" else NSControlStateValueOff)

        # Output mode
        mode = self.config.output_mode
        self.mi_mode_loose.setState_(NSControlStateValueOn if mode == "loose_diary" else NSControlStateValueOff)
        self.mi_mode_strict.setState_(NSControlStateValueOn if mode == "strict_json" else NSControlStateValueOff)

        # Hotkey enabled
        self.mi_hotkey.setState_(NSControlStateValueOn if self.config.hotkey_enabled else NSControlStateValueOff)

    # ---------- Core ----------
    def _make_entry(self, role: str, prompt: str) -> EntryModel:
        self.id_service.strategy = self.config.id_strategy
        entry_id = self.id_service.generate()
        datumtijd = self.dt_service.datumtijd_yyyymmdd()
        return EntryModel(id=entry_id, role=role, prompt=prompt, datumtijd=datumtijd)

    def _format_entry(self, entry: EntryModel) -> str:
        mode = self.config.output_mode
        if mode == "strict_json":
            return self.formatter.format_strict_json(entry)
        return self.formatter.format_loose_diary(entry)

    def generate_and_copy(self, role_override: str | None = None, prompt: str = "") -> None:
        role = role_override or self.config.default_role
        entry = self._make_entry(role=role, prompt=prompt)
        out = self._format_entry(entry)
        self.clipboard.copy_text(out)
        NSLog("Copied entry (role=%@, mode=%@, id_strategy=%@)", role, self.config.output_mode, self.config.id_strategy)

    # ---------- Hotkey ----------
    def _start_hotkey(self):
        if not CARBON_AVAILABLE:
            NSLog("Carbon not available; hotkey disabled.")
            return

        if self.hotkey is not None:
            self.hotkey.stop()
            self.hotkey = None

        def _trigger():
            self.generate_and_copy()

        self.hotkey = HotkeyService(
            keycode=self.config.hotkey_keycode,
            modifiers=self.config.hotkey_modifiers,
            on_trigger=_trigger,
        )
        ok = self.hotkey.start()
        if not ok:
            NSLog("Hotkey registration failed; continuing without hotkey.")

    # ---------- Menu handlers ----------
    def onGenerateEntry_(self, sender):
        try:
            self.generate_and_copy()
        except Exception as e:
            self._show_error("Clipboard error", str(e))

    def onGenerateWithPrompt_(self, sender):
        try:
            prompt = self._prompt_dialog("Generate with Prompt", "Enter prompt text (single-line MVP):")
            if prompt is None:
                return
            self.generate_and_copy(prompt=prompt)
        except Exception as e:
            self._show_error("Error", str(e))

    def onSetRoleUser_(self, sender):
        self.config.set_default_role("user")
        self._refresh_menu_states()

    def onSetRoleSystem_(self, sender):
        self.config.set_default_role("system")
        self._refresh_menu_states()

    def onSetModeLoose_(self, sender):
        self.config.set_output_mode("loose_diary")
        self._refresh_menu_states()

    def onSetModeStrict_(self, sender):
        self.config.set_output_mode("strict_json")
        self._refresh_menu_states()

    def onToggleHotkey_(self, sender):
        new_state = not self.config.hotkey_enabled
        self.config.set_hotkey_enabled(new_state)
        self._refresh_menu_states()
        if new_state:
            self._start_hotkey()
        else:
            if self.hotkey is not None:
                self.hotkey.stop()
                self.hotkey = None

    # ---------- UI helpers ----------
    def _prompt_dialog(self, title: str, message: str) -> str | None:
        alert = NSAlert.alloc().init()
        alert.setMessageText_(title)
        alert.setInformativeText_(message)

        tf = NSTextField.alloc().initWithFrame_(((0, 0), (380, 24)))
        tf.setStringValue_("")
        alert.setAccessoryView_(tf)

        alert.addButtonWithTitle_("Copy Entry")
        alert.addButtonWithTitle_("Cancel")

        resp = alert.runModal()
        if resp == 1000:  # NSAlertFirstButtonReturn
            return str(tf.stringValue() or "")
        return None

    def _show_error(self, title: str, message: str) -> None:
        alert = NSAlert.alloc().init()
        alert.setAlertStyle_(2)  # NSAlertStyleCritical
        alert.setMessageText_(title)
        alert.setInformativeText_(message)
        alert.addButtonWithTitle_("OK")
        alert.runModal()


def main():
    app = NSApplication.sharedApplication()
    delegate = AppController.alloc().init()
    app.setDelegate_(delegate)
    AppHelper.runEventLoop()


if __name__ == "__main__":
    main()
