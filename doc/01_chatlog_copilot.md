
Hieronder staat **de volledige `src/clipboard_json_logger.py`** (single‑file, class‑based) met **v0.5.0** en **Fase 1** geïmplementeerd: **Role = “User + system”** ⇒ **2 entries** met **zelfde `id` + `datumtijd`**, en **2 blokken** op clipboard gescheiden door een lege regel.  
Alle v0.4‑features uit jouw TS blijven inbegrepen (menu bar, Mode A/B, prompt panel, settings panel, notifications policy, hotkey best‑effort, overlay bubble).

> ⚠️ Let op: ik kon jouw bestaande `clipboard_json_logger.py` niet terugvinden via enterprise search, dus dit is een **complete, zelfvoorzienende implementatie** conform jouw **TS v0.4** + **Fase 1 delta**. [\[Document L...th useful  | Viva Engage\]](https://engage.cloud.microsoft/main/threads/eyJfdHlwZSI6IlRocmVhZCIsImlkIjoiMzY2MzYzOTUwOTEyMzA3MiJ9), [\[fugro.sharepoint.com\]](https://fugro.sharepoint.com/sites/Projects/Shared%20Documents/Vessels/West_White_Rose/EMS/231419-AtlanticXL-RECON-2024NOV11/E-LOGS/Server_Backup/Desktop/Seagate%20Backup%20Software/Toolkit/Backup/HUSKYEMSSERVER/c/Users/huskyadmin/.PyCharmCE2018.3/config/plugins/availables.xml?web=1), [\[UK-STM-OPL...r Programs | Word\]](https://fugro.sharepoint.com/sites/FugroUKBMS/_layouts/15/Doc.aspx?sourcedoc=%7B39D93B5E-29C6-4E3D-8AB1-D1D70D314D6A%7D&file=UK-STM-OPL-PR-003%20Version%20Control%20-%20Logger%20Programs.docx&action=default&mobileredirect=true&DefaultItemOpen=1), [\[
✅ The wor...has chang | Viva Engage\]](https://engage.cloud.microsoft/main/threads/eyJfdHlwZSI6IlRocmVhZCIsImlkIjoiMzU2MDgxNjkwOTQ3NTg0MCJ9), [\[Discovery...hrough the | Viva Engage\]](https://engage.cloud.microsoft/main/threads/eyJfdHlwZSI6IlRocmVhZCIsImlkIjoiMzYxODg1MDAwMzc5NTk2OCJ9), [\[loggernet | PDF\]](https://fugro.sharepoint.com/sites/Monitoring/Monitoring%20Experts%20%20Loggersystemen/Uitzoeken%20-%20Data%20dump/Campbell/manuals/Software%20Applications/loggernet.pdf?web=1), [\[USA-MAI-OP...VS Profile | Word\]](https://fugro.sharepoint.com/sites/FUSA/FUSAMI/_layouts/15/Doc.aspx?sourcedoc=%7BF5BFAB50-FB9C-4380-A94F-9CD55C35C142%7D&file=USA-MAI-OPS-GU-0007%20MiniSVS%20Profile.docx&action=default&mobileredirect=true&DefaultItemOpen=1), [\[GLOB-USV-O...l Logbooks | Word\]](https://fugro.sharepoint.com/sites/FugroGBMSHome/_layouts/15/Doc.aspx?sourcedoc=%7B1A97CBC9-2624-4D8C-9DC4-01B7667B7CEC%7D&file=GLOB-USV-OPL-PR-030%20USV%20Navtor%20Digital%20Logbooks.docx&action=default&mobileredirect=true&DefaultItemOpen=1), [\[Geophysica...762) Rev A | PDF\]](https://fugro.sharepoint.com/sites/APAC-BMS/WorkingDocuments/Legacy%20(Check%20and%20Archive%202026)/CHECK%20AND%20ARCHIVE%20-%20Legacy%20BMS/Geotechnical/2.%20Internal%20Document%20Review%20(IDR)/IDR%20Geotechnical%20Work%20Instructions%20for%20Review%20(x%2010)/Geophysical%20Wireline%20Logging%20P%20and%20S%20Wave%20Suspension%20Logger%20and%20Caliper%20Ops%20Work%20Instruction%20(SEA-M-25762)%20Rev%20A.pdf?web=1)

***

## ✅ `src/clipboard_json_logger.py` (v0.5.0 — Phase 1)

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Clipboard JSON Logger — macOS menu bar app (PyObjC)
Version: 0.5.0  (Phase 1: User + system role selection => two entries share same id+datumtijd)

Core features (TS v0.4 baseline):
- Menu bar app (LSUIElement via plist recommended; also uses activation policy)
- Entry model fields: id, role, prompt, datumtijd
- ID strategies: short_id (default) or uuid4
- datumtijd: YYYYMMDD, timezone best-effort (Europe/Amsterdam default)
- Output mode:
  - Mode A: loose diary (default)
  - Mode B: strict JSON + pretty toggle
- Prompt panel: multiline prompt + role override
- Clipboard: NSPasteboard write + NSAlert on failure
- Notifications: best-effort UserNotifications + policy all/hotkey_only/off
- Global hotkey: best-effort Carbon + enable/disable + capture UI + reset + conflict handling
- Settings panel: hotkey enabled, capture/apply/reset, notifications mode, pretty JSON
- Overlay bubble: enable/disable, draggable, always-on-top, position persistence
  + click action, show on all Spaces, hide in fullscreen, context menu
- Persistence: NSUserDefaults (no prompt content stored)
- Logging: NSLog only (no prompt content)
"""

APP_VERSION = "0.5.0"

import json
import uuid
import random
import string
import os
from dataclasses import dataclass

# PyObjC / Cocoa
import objc
from Cocoa import (
    NSObject,
    NSApplication,
    NSApp,
    NSApplicationActivationPolicyProhibited,
    NSStatusBar,
    NSVariableStatusItemLength,
    NSMenu,
    NSMenuItem,
    NSAlert,
    NSAlertStyleWarning,
    NSPasteboard,
    NSPasteboardTypeString,
    NSScreen,
    NSPanel,
    NSWindow,
    NSWindowStyleMaskTitled,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskUtilityWindow,
    NSWindowStyleMaskNonactivatingPanel,
    NSWindowStyleMaskBorderless,
    NSBackingStoreBuffered,
    NSFloatingWindowLevel,
    NSStatusWindowLevel,
    NSColor,
    NSFont,
    NSFontAttributeName,
    NSForegroundColorAttributeName,
    NSBezelStyleRounded,
    NSButton,
    NSTextField,
    NSSwitchButton,
    NSPopUpButton,
    NSScrollView,
    NSTextView,
    NSMakeRect,
    NSMakePoint,
    NSMakeSize,
    NSRectFill,
    NSBezierPath,
    NSImage,
    NSImageSymbolConfiguration,
    NSLog,
    NSEvent,
)

from Foundation import (
    NSUserDefaults,
    NSTimer,
    NSString,
)

# Optional frameworks
UN_AVAILABLE = False
try:
    import UserNotifications as UN  # pyobjc-framework-UserNotifications
    UN_AVAILABLE = True
except Exception:
    UN_AVAILABLE = False

CARBON_AVAILABLE = False
try:
    from Carbon import Events, HIToolbox
    CARBON_AVAILABLE = True
except Exception:
    CARBON_AVAILABLE = False


# -----------------------------
# Domain constants
# -----------------------------

ROLE_USER = "user"
ROLE_SYSTEM = "system"
# UI selection (generator mode). MUST NOT appear in output EntryModel.role.
ROLE_USER_AND_SYSTEM = "UserAndSystem"

OUTPUT_MODE_LOOSE = "loose_diary"
OUTPUT_MODE_STRICT = "strict_json"

ID_STRATEGY_SHORT = "short_id"
ID_STRATEGY_UUID4 = "uuid4"

DATUMTIJD_STRATEGY = "date_yyyymmdd"

NOTIF_ALL = "all"
NOTIF_HOTKEY_ONLY = "hotkey_only"
NOTIF_OFF = "off"

OVERLAY_CLICK_GENERATE = "generate_blank"
OVERLAY_CLICK_PROMPT = "open_prompt_panel"


# -----------------------------
# Domain model
# -----------------------------

@dataclass
class EntryModel:
    id: str
    role: str
    prompt: str
    datumtijd: str


# -----------------------------
# Config (NSUserDefaults)
# -----------------------------

class AppConfig:
    # Core keys
    K_DEFAULT_ROLE = "default_role"
    K_ID_STRATEGY = "id_strategy"
    K_OUTPUT_MODE = "output_mode"
    K_DATUMTIJD_STRATEGY = "datumtijd_strategy"
    K_JSON_PRETTY = "json_pretty"
    K_NOTIFICATIONS_MODE = "notifications_mode"
    K_TIMEZONE_NAME = "timezone_name"

    # Hotkey
    K_HOTKEY_ENABLED = "hotkey_enabled"
    K_HOTKEY_KEYCODE = "hotkey_keycode"
    K_HOTKEY_MODIFIERS = "hotkey_modifiers"

    # Overlay (v0.4)
    K_OVERLAY_ENABLED = "overlay_enabled"
    K_OVERLAY_CLICK_ACTION = "overlay_click_action"
    K_OVERLAY_SHOW_ALL_SPACES = "overlay_show_all_spaces"
    K_OVERLAY_HIDE_IN_FULLSCREEN = "overlay_hide_in_fullscreen"
    K_OVERLAY_POS_X = "overlay_pos_x"
    K_OVERLAY_POS_Y = "overlay_pos_y"
    K_OVERLAY_SCREEN_HINT = "overlay_screen_hint"

    # Defaults
    DEFAULT_ROLE = ROLE_USER
    DEFAULT_ID_STRATEGY = ID_STRATEGY_SHORT
    DEFAULT_OUTPUT_MODE = OUTPUT_MODE_LOOSE
    DEFAULT_DATUMTIJD_STRATEGY = DATUMTIJD_STRATEGY
    DEFAULT_JSON_PRETTY = False
    DEFAULT_NOTIFICATIONS_MODE = NOTIF_HOTKEY_ONLY
    DEFAULT_TIMEZONE = "Europe/Amsterdam"

    DEFAULT_HOTKEY_ENABLED = False
    # Default hotkey: Ctrl+Opt+Cmd+J best-effort
    DEFAULT_HOTKEY_KEYCODE = 38  # 'J' keycode on macOS (commonly)
    DEFAULT_HOTKEY_MODIFIERS = 0
    if CARBON_AVAILABLE:
        DEFAULT_HOTKEY_MODIFIERS = (
            Events.controlKey |
            Events.optionKey |
            Events.cmdKey
        )

    DEFAULT_OVERLAY_ENABLED = False
    DEFAULT_OVERLAY_CLICK_ACTION = OVERLAY_CLICK_GENERATE
    DEFAULT_OVERLAY_SHOW_ALL_SPACES = True
    DEFAULT_OVERLAY_HIDE_IN_FULLSCREEN = True
    DEFAULT_OVERLAY_POS_X = 0.0
    DEFAULT_OVERLAY_POS_Y = 0.0
    DEFAULT_OVERLAY_SCREEN_HINT = -1

    def __init__(self):
        self.ud = NSUserDefaults.standardUserDefaults()
        self._seed_defaults_once()

    def _seed_defaults_once(self):
        # registerDefaults_ does not overwrite existing values
        defaults = {
            self.K_DEFAULT_ROLE: self.DEFAULT_ROLE,
            self.K_ID_STRATEGY: self.DEFAULT_ID_STRATEGY,
            self.K_OUTPUT_MODE: self.DEFAULT_OUTPUT_MODE,
            self.K_DATUMTIJD_STRATEGY: self.DEFAULT_DATUMTIJD_STRATEGY,
            self.K_JSON_PRETTY: self.DEFAULT_JSON_PRETTY,
            self.K_NOTIFICATIONS_MODE: self.DEFAULT_NOTIFICATIONS_MODE,
            self.K_TIMEZONE_NAME: self.DEFAULT_TIMEZONE,
            self.K_HOTKEY_ENABLED: self.DEFAULT_HOTKEY_ENABLED,
            self.K_HOTKEY_KEYCODE: self.DEFAULT_HOTKEY_KEYCODE,
            self.K_HOTKEY_MODIFIERS: int(self.DEFAULT_HOTKEY_MODIFIERS),
            self.K_OVERLAY_ENABLED: self.DEFAULT_OVERLAY_ENABLED,
            self.K_OVERLAY_CLICK_ACTION: self.DEFAULT_OVERLAY_CLICK_ACTION,
            self.K_OVERLAY_SHOW_ALL_SPACES: self.DEFAULT_OVERLAY_SHOW_ALL_SPACES,
            self.K_OVERLAY_HIDE_IN_FULLSCREEN: self.DEFAULT_OVERLAY_HIDE_IN_FULLSCREEN,
            self.K_OVERLAY_POS_X: self.DEFAULT_OVERLAY_POS_X,
            self.K_OVERLAY_POS_Y: self.DEFAULT_OVERLAY_POS_Y,
            self.K_OVERLAY_SCREEN_HINT: self.DEFAULT_OVERLAY_SCREEN_HINT,
        }
        self.ud.registerDefaults_(defaults)

        # if overlay pos unset, pick a reasonable default in main screen visible frame
        x = self.ud.doubleForKey_(self.K_OVERLAY_POS_X)
        y = self.ud.doubleForKey_(self.K_OVERLAY_POS_Y)
        if x == 0.0 and y == 0.0:
            scr = NSScreen.mainScreen()
            if scr:
                vf = scr.visibleFrame()
                # top-right-ish
                self.ud.setDouble_forKey_(vf.origin.x + vf.size.width - 80, self.K_OVERLAY_POS_X)
                self.ud.setDouble_forKey_(vf.origin.y + vf.size.height - 120, self.K_OVERLAY_POS_Y)

    # Helpers
    def _get_str(self, k, default):
        v = self.ud.stringForKey_(k)
        return v if v else default

    def _set_str(self, k, v):
        self.ud.setObject_forKey_(v, k)

    def _get_bool(self, k, default=False):
        # boolForKey returns False when missing; we seeded defaults so ok
        return bool(self.ud.boolForKey_(k))

    def _set_bool(self, k, v):
        self.ud.setBool_forKey_(bool(v), k)

    def _get_int(self, k, default=0):
        return int(self.ud.integerForKey_(k) or default)

    def _set_int(self, k, v):
        self.ud.setInteger_forKey_(int(v), k)

    def _get_double(self, k, default=0.0):
        return float(self.ud.doubleForKey_(k) or default)

    def _set_double(self, k, v):
        self.ud.setDouble_forKey_(float(v), k)

    # Core getters/setters
    def default_role(self) -> str:
        v = self._get_str(self.K_DEFAULT_ROLE, self.DEFAULT_ROLE)
        if v not in (ROLE_USER, ROLE_SYSTEM, ROLE_USER_AND_SYSTEM):
            return self.DEFAULT_ROLE
        return v

    def set_default_role(self, v: str) -> None:
        if v not in (ROLE_USER, ROLE_SYSTEM, ROLE_USER_AND_SYSTEM):
            v = self.DEFAULT_ROLE
        self._set_str(self.K_DEFAULT_ROLE, v)

    def id_strategy(self) -> str:
        v = self._get_str(self.K_ID_STRATEGY, self.DEFAULT_ID_STRATEGY)
        return v if v in (ID_STRATEGY_SHORT, ID_STRATEGY_UUID4) else self.DEFAULT_ID_STRATEGY

    def set_id_strategy(self, v: str) -> None:
        if v not in (ID_STRATEGY_SHORT, ID_STRATEGY_UUID4):
            v = self.DEFAULT_ID_STRATEGY
        self._set_str(self.K_ID_STRATEGY, v)

    def output_mode(self) -> str:
        v = self._get_str(self.K_OUTPUT_MODE, self.DEFAULT_OUTPUT_MODE)
        return v if v in (OUTPUT_MODE_LOOSE, OUTPUT_MODE_STRICT) else self.DEFAULT_OUTPUT_MODE

    def set_output_mode(self, v: str) -> None:
        if v not in (OUTPUT_MODE_LOOSE, OUTPUT_MODE_STRICT):
            v = self.DEFAULT_OUTPUT_MODE
        self._set_str(self.K_OUTPUT_MODE, v)

    def datumtijd_strategy(self) -> str:
        v = self._get_str(self.K_DATUMTIJD_STRATEGY, self.DEFAULT_DATUMTIJD_STRATEGY)
        return v if v == DATUMTIJD_STRATEGY else self.DEFAULT_DATUMTIJD_STRATEGY

    def json_pretty(self) -> bool:
        return self._get_bool(self.K_JSON_PRETTY, self.DEFAULT_JSON_PRETTY)

    def set_json_pretty(self, v: bool) -> None:
        self._set_bool(self.K_JSON_PRETTY, v)

    def notifications_mode(self) -> str:
        v = self._get_str(self.K_NOTIFICATIONS_MODE, self.DEFAULT_NOTIFICATIONS_MODE)
        return v if v in (NOTIF_ALL, NOTIF_HOTKEY_ONLY, NOTIF_OFF) else self.DEFAULT_NOTIFICATIONS_MODE

    def set_notifications_mode(self, v: str) -> None:
        if v not in (NOTIF_ALL, NOTIF_HOTKEY_ONLY, NOTIF_OFF):
            v = self.DEFAULT_NOTIFICATIONS_MODE
        self._set_str(self.K_NOTIFICATIONS_MODE, v)

    def timezone_name(self) -> str:
        return self._get_str(self.K_TIMEZONE_NAME, self.DEFAULT_TIMEZONE)

    # Hotkey
    def hotkey_enabled(self) -> bool:
        return self._get_bool(self.K_HOTKEY_ENABLED, self.DEFAULT_HOTKEY_ENABLED)

    def set_hotkey_enabled(self, v: bool) -> None:
        self._set_bool(self.K_HOTKEY_ENABLED, v)

    def hotkey_keycode(self) -> int:
        return self._get_int(self.K_HOTKEY_KEYCODE, self.DEFAULT_HOTKEY_KEYCODE)

    def hotkey_modifiers(self) -> int:
        return self._get_int(self.K_HOTKEY_MODIFIERS, int(self.DEFAULT_HOTKEY_MODIFIERS))

    def set_hotkey(self, keycode: int, modifiers: int) -> None:
        self._set_int(self.K_HOTKEY_KEYCODE, keycode)
        self._set_int(self.K_HOTKEY_MODIFIERS, int(modifiers))

    # Overlay
    def overlay_enabled(self) -> bool:
        return self._get_bool(self.K_OVERLAY_ENABLED, self.DEFAULT_OVERLAY_ENABLED)

    def set_overlay_enabled(self, v: bool) -> None:
        self._set_bool(self.K_OVERLAY_ENABLED, v)

    def overlay_click_action(self) -> str:
        v = self._get_str(self.K_OVERLAY_CLICK_ACTION, self.DEFAULT_OVERLAY_CLICK_ACTION)
        return v if v in (OVERLAY_CLICK_GENERATE, OVERLAY_CLICK_PROMPT) else self.DEFAULT_OVERLAY_CLICK_ACTION

    def set_overlay_click_action(self, v: str) -> None:
        if v not in (OVERLAY_CLICK_GENERATE, OVERLAY_CLICK_PROMPT):
            v = self.DEFAULT_OVERLAY_CLICK_ACTION
        self._set_str(self.K_OVERLAY_CLICK_ACTION, v)

    def overlay_show_all_spaces(self) -> bool:
        return self._get_bool(self.K_OVERLAY_SHOW_ALL_SPACES, self.DEFAULT_OVERLAY_SHOW_ALL_SPACES)

    def set_overlay_show_all_spaces(self, v: bool) -> None:
        self._set_bool(self.K_OVERLAY_SHOW_ALL_SPACES, v)

    def overlay_hide_in_fullscreen(self) -> bool:
        return self._get_bool(self.K_OVERLAY_HIDE_IN_FULLSCREEN, self.DEFAULT_OVERLAY_HIDE_IN_FULLSCREEN)

    def set_overlay_hide_in_fullscreen(self, v: bool) -> None:
        self._set_bool(self.K_OVERLAY_HIDE_IN_FULLSCREEN, v)

    def overlay_pos(self):
        return (self._get_double(self.K_OVERLAY_POS_X, 0.0), self._get_double(self.K_OVERLAY_POS_Y, 0.0))

    def set_overlay_pos(self, x: float, y: float, screen_hint: int = -1):
        self._set_double(self.K_OVERLAY_POS_X, x)
        self._set_double(self.K_OVERLAY_POS_Y, y)
        self._set_int(self.K_OVERLAY_SCREEN_HINT, int(screen_hint))

    def overlay_screen_hint(self) -> int:
        return self._get_int(self.K_OVERLAY_SCREEN_HINT, -1)


# -----------------------------
# Services
# -----------------------------

class IdService:
    @staticmethod
    def generate(strategy: str) -> str:
        if strategy == ID_STRATEGY_UUID4:
            return str(uuid.uuid4())
        # short_id ~ 9 chars
        alphabet = string.ascii_lowercase + string.digits
        return "".join(random.choice(alphabet) for _ in range(9))


class DateTimeService:
    @staticmethod
    def datumtijd_yyyymmdd(tz_name: str = "Europe/Amsterdam") -> str:
        # Best-effort timezone using zoneinfo (Python 3.9+)
        try:
            from datetime import datetime
            from zoneinfo import ZoneInfo
            tz = ZoneInfo(tz_name)
            return datetime.now(tz=tz).strftime("%Y%m%d")
        except Exception:
            # Fallback: localtime
            try:
                from datetime import datetime
                return datetime.now().strftime("%Y%m%d")
            except Exception:
                return "19700101"


class EntryFormatter:
    @staticmethod
    def format_loose_diary(entry: EntryModel) -> str:
        # Intentionally not strict JSON; matches diary-ish format
        # Keep triple quotes for multiline prompt
        prompt = entry.prompt or ""
        return (
            "{'id': '" + entry.id + "', role: '" + entry.role + "', prompt: \"\"\"\n"
            + prompt
            + "\n\"\"\"\n,\ndatumtijd: \"" + entry.datumtijd + "\"\n},"
        )

    @staticmethod
    def format_strict_json(entry: EntryModel, pretty: bool = False) -> str:
        payload = {
            "id": entry.id,
            "role": entry.role,
            "prompt": entry.prompt or "",
            "datumtijd": entry.datumtijd,
        }
        if pretty:
            return json.dumps(payload, ensure_ascii=False, indent=2)
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


class ClipboardService:
    @staticmethod
    def copy_text(text: str) -> None:
        pb = NSPasteboard.generalPasteboard()
        pb.clearContents()
        ok = pb.setString_forType_(text, NSPasteboardTypeString)
        if not ok:
            raise RuntimeError("Clipboard write failed")


class NotificationService:
    def __init__(self):
        self._permission_requested = False

    def ensure_permission(self):
        if not UN_AVAILABLE:
            return
        if self._permission_requested:
            return
        self._permission_requested = True
        try:
            center = UN.UNUserNotificationCenter.currentNotificationCenter()
            # Request authorization non-blocking
            def _cb(granted, err):
                # Do not log prompt; only status
                if err is not None:
                    NSLog("Notifications permission error: %@", err)
            options = (UN.UNAuthorizationOptionAlert |
                       UN.UNAuthorizationOptionSound |
                       UN.UNAuthorizationOptionBadge)
            center.requestAuthorizationWithOptions_completionHandler_(options, _cb)
        except Exception as e:
            NSLog("Notifications permission request failed: %@", str(e))

    def notify_copied(self, title: str, body: str):
        if not UN_AVAILABLE:
            return
        try:
            self.ensure_permission()
            content = UN.UNMutableNotificationContent.alloc().init()
            content.setTitle_(title)
            content.setBody_(body)

            request = UN.UNNotificationRequest.requestWithIdentifier_content_trigger_(
                str(uuid.uuid4()), content, None
            )
            center = UN.UNUserNotificationCenter.currentNotificationCenter()
            def _cb(err):
                if err is not None:
                    NSLog("Notification delivery error: %@", err)
            center.addNotificationRequest_withCompletionHandler_(request, _cb)
        except Exception as e:
            NSLog("Notification failed: %@", str(e))


# -----------------------------
# Hotkey (Carbon) best-effort
# -----------------------------

def _nsevent_flags_to_carbon_modifiers(nsevent_modifier_flags: int) -> int:
    """
    Map NSEvent modifierFlags to Carbon modifier masks.
    Stored hotkey modifiers are Carbon masks (Events.*Key)
    """
    if not CARBON_AVAILABLE:
        return 0
    mods = 0
    # NSEventModifierFlag* values are bitmasks; use known constants by numeric bits
    # control: 1<<18, option: 1<<19, shift: 1<<17, command: 1<<20
    if nsevent_modifier_flags & (1 << 18):
        mods |= Events.controlKey
    if nsevent_modifier_flags & (1 << 19):
        mods |= Events.optionKey
    if nsevent_modifier_flags & (1 << 17):
        mods |= Events.shiftKey
    if nsevent_modifier_flags & (1 << 20):
        mods |= Events.cmdKey
    return int(mods)


class HotkeyService:
    def __init__(self, on_trigger):
        self.on_trigger = on_trigger
        self.hotkey_ref = None
        self.handler_installed = False
        self.event_handler = None

    def available(self) -> bool:
        return CARBON_AVAILABLE

    def start(self, keycode: int, modifiers: int) -> bool:
        if not CARBON_AVAILABLE:
            return False
        try:
            self.stop()
            # Install handler once
            if not self.handler_installed:
                self._install_handler()

            hotkey_id = Events.EventHotKeyID()
            hotkey_id.signature = 0xC0DE  # arbitrary
            hotkey_id.id = 1

            # Register hotkey
            self.hotkey_ref = Events.EventHotKeyRef()
            target = Events.GetApplicationEventTarget()
            status = Events.RegisterEventHotKey(
                int(keycode), int(modifiers), hotkey_id, target, 0, self.hotkey_ref
            )
            if status != 0:
                # Non-zero -> fail
                NSLog("RegisterEventHotKey failed status=%d", status)
                self.hotkey_ref = None
                return False

            NSLog("Hotkey registered keycode=%d modifiers=%d", int(keycode), int(modifiers))
            return True
        except Exception as e:
            NSLog("Hotkey start error: %@", str(e))
            self.hotkey_ref = None
            return False

    def stop(self):
        if not CARBON_AVAILABLE:
            return
        try:
            if self.hotkey_ref is not None:
                try:
                    Events.UnregisterEventHotKey(self.hotkey_ref)
                except Exception:
                    pass
                self.hotkey_ref = None
        except Exception as e:
            NSLog("Hotkey stop error: %@", str(e))

    def _install_handler(self):
        if not CARBON_AVAILABLE:
            return
        # Define event types
        event_spec = Events.EventTypeSpec()
        event_spec.eventClass = Events.kEventClassKeyboard
        event_spec.eventKind = Events.kEventHotKeyPressed

        def _handler(next_handler, the_event, user_data):
            try:
                # Trigger callback
                self.on_trigger()
            except Exception as e:
                NSLog("Hotkey handler error: %@", str(e))
            return 0

        self.event_handler = _handler
        try:
            Events.InstallApplicationEventHandler(self.event_handler, 1, event_spec, None, None)
            self.handler_installed = True
        except Exception as e:
            NSLog("InstallApplicationEventHandler failed: %@", str(e))
            self.handler_installed = False


# -----------------------------
# Overlay bubble (v0.4)
# -----------------------------

class OverlayBubbleView(NSObject):
    """
    NSView implemented via objc in a lightweight way:
    We'll create an NSButton-like drawing by subclassing NSView through objc.
    """
    # Use NSView via PyObjC dynamic subclassing
    pass


# Create a real NSView subclass with objc
from Cocoa import NSView

class OverlayBubbleNSView(NSView):
    def initWithController_(self, controller):
        self = objc.super(OverlayBubbleNSView, self).initWithFrame_(NSMakeRect(0, 0, 56, 56))
        if self is None:
            return None
        self.controller = controller
        self._dragging = False
        self._drag_start = None
        self._win_start = None
        return self

    def isOpaque(self):
        return False

    def drawRect_(self, rect):
        NSColor.clearColor().set()
        NSRectFill(rect)

        # Circle background
        circle = NSBezierPath.bezierPathWithOvalInRect_(self.bounds())
        NSColor.colorWithCalibratedWhite_alpha_(0.15, 0.95).set()
        circle.fill()

        # Border
        NSColor.colorWithCalibratedWhite_alpha_(0.0, 0.25).set()
        circle.setLineWidth_(1.0)
        circle.stroke()

        # Text "{ }"
        s = "{ }"
        attrs = {
            NSFontAttributeName: NSFont.boldSystemFontOfSize_(14),
            NSForegroundColorAttributeName: NSColor.colorWithCalibratedWhite_alpha_(0.1, 1.0),
        }
        size = NSString.stringWithString_(s).sizeWithAttributes_(attrs)
        x = (self.bounds().size.width - size.width) / 2.0
        y = (self.bounds().size.height - size.height) / 2.0
        NSString.stringWithString_(s).drawAtPoint_withAttributes_(NSMakePoint(x, y), attrs)

    def mouseDown_(self, event):
        self._dragging = True
        self._drag_start = event.locationInWindow()
        w = self.window()
        if w:
            self._win_start = w.frame().origin

    def mouseDragged_(self, event):
        if not self._dragging:
            return
        w = self.window()
        if not w:
            return
        loc = event.locationInWindow()
        dx = loc.x - self._drag_start.x
        dy = loc.y - self._drag_start.y
        new_x = self._win_start.x + dx
        new_y = self._win_start.y + dy
        frame = w.frame()
        frame.origin.x = new_x
        frame.origin.y = new_y
        w.setFrame_display_(frame, True)

    def mouseUp_(self, event):
        if not self._dragging:
            return
        self._dragging = False
        self.controller.persist_position()

    def rightMouseDown_(self, event):
        self.controller.show_context_menu(self, event)

    def otherMouseDown_(self, event):
        # Treat ctrl-click as right-click
        try:
            if event.modifierFlags() & (1 << 18):  # control
                self.controller.show_context_menu(self, event)
        except Exception:
            pass

    def mouseDownCanMoveWindow(self):
        return False

    def mouseUpCanMoveWindow(self):
        return False

    def mouseClicked_(self, event):
        self.controller.primary_click()

    def mouseUp_(self, event):
        # Decide click vs drag: if minimal movement, treat as click
        was_dragging = self._dragging
        self._dragging = False
        self.controller.persist_position()
        # If no significant drag, treat as click
        try:
            if not was_dragging:
                self.controller.primary_click()
        except Exception:
            pass

    # Better: implement click on mouseUp when little movement
    def mouseUp_(self, event):
        w = self.window()
        if w and self._win_start and self._drag_start:
            end_loc = event.locationInWindow()
            dx = abs(end_loc.x - self._drag_start.x)
            dy = abs(end_loc.y - self._drag_start.y)
            self.controller.persist_position()
            if dx < 2 and dy < 2:
                self.controller.primary_click()
        else:
            self.controller.persist_position()


class OverlayBubbleController(NSObject):
    def initWithAppController_(self, app_controller):
        self = objc.super(OverlayBubbleController, self).init()
        if self is None:
            return None
        self.app = app_controller
        self.panel = None
        self.view = None
        return self

    def show(self):
        if self.panel is None:
            self._build()
        self.apply_behavior()
        self.panel.orderFrontRegardless()

    def hide(self):
        if self.panel is not None:
            self.panel.orderOut_(None)

    def close(self):
        if self.panel is not None:
            try:
                self.panel.close()
            except Exception:
                pass
        self.panel = None
        self.view = None

    def _build(self):
        # Small borderless non-activating panel
        rect = NSMakeRect(200, 200, 56, 56)
        style = NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel
        self.panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, style, NSBackingStoreBuffered, False
        )
        self.panel.setLevel_(NSFloatingWindowLevel)
        self.panel.setOpaque_(False)
        self.panel.setBackgroundColor_(NSColor.clearColor())
        self.panel.setHasShadow_(True)
        self.panel.setIgnoresMouseEvents_(False)
        self.panel.setHidesOnDeactivate_(False)
        self.panel.setMovableByWindowBackground_(False)

        self.view = OverlayBubbleNSView.alloc().initWithController_(self)
        self.panel.setContentView_(self.view)

        self.restore_position()

    def apply_behavior(self):
        if not self.panel:
            return
        # Spaces behavior
        behavior = 0
        try:
            from Cocoa import NSWindowCollectionBehaviorCanJoinAllSpaces, NSWindowCollectionBehaviorFullScreenAuxiliary
            if self.app.config.overlay_show_all_spaces():
                behavior |= NSWindowCollectionBehaviorCanJoinAllSpaces
            # Fullscreen: best-effort
            if not self.app.config.overlay_hide_in_fullscreen():
                behavior |= NSWindowCollectionBehaviorFullScreenAuxiliary
            self.panel.setCollectionBehavior_(behavior)
        except Exception:
            pass

    def primary_click(self):
        action = self.app.config.overlay_click_action()
        if action == OVERLAY_CLICK_PROMPT:
            self.app.onGenerateWithPrompt_(None)
        else:
            self.app.generate_and_copy(source="overlay")

    def show_context_menu(self, view, event):
        menu = self.app.build_overlay_context_menu()
        # Pop up near cursor
        try:
            NSMenu.popUpContextMenu_withEvent_forView_(menu, event, view)
        except Exception:
            # fallback: show at mouse location in screen coords
            menu.popUpMenuPositioningItem_atLocation_inView_(None, event.locationInWindow(), view)

    def persist_position(self):
        if not self.panel:
            return
        frame = self.panel.frame()
        x = frame.origin.x
        y = frame.origin.y
        hint = self._screen_hint_for_point(x, y)
        self.app.config.set_overlay_pos(x, y, hint)

    def restore_position(self):
        if not self.panel:
            return
        x, y = self.app.config.overlay_pos()
        hint = self.app.config.overlay_screen_hint()
        scr = self._screen_from_hint(hint) or NSScreen.mainScreen()
        if scr:
            vf = scr.visibleFrame()
            # clamp
            w = self.panel.frame().size.width
            h = self.panel.frame().size.height
            x = max(vf.origin.x, min(x, vf.origin.x + vf.size.width - w))
            y = max(vf.origin.y, min(y, vf.origin.y + vf.size.height - h))
        frame = self.panel.frame()
        frame.origin.x = x
        frame.origin.y = y
        self.panel.setFrame_display_(frame, True)

    def _screen_from_hint(self, hint: int):
        try:
            screens = NSScreen.screens()
            if hint is not None and hint >= 0 and hint < len(screens):
                return screens[hint]
        except Exception:
            pass
        return None

    def _screen_hint_for_point(self, x: float, y: float) -> int:
        try:
            screens = NSScreen.screens()
            for i, s in enumerate(screens):
                vf = s.frame()
                if (x >= vf.origin.x and x <= vf.origin.x + vf.size.width and
                    y >= vf.origin.y and y <= vf.origin.y + vf.size.height):
                    return i
        except Exception:
            pass
        return -1


# -----------------------------
# Settings Panel + Hotkey capture
# -----------------------------

from Cocoa import NSControl, NSKeyDown, NSResponder

class HotkeyCaptureView(NSView):
    def initWithController_(self, controller):
        self = objc.super(HotkeyCaptureView, self).initWithFrame_(NSMakeRect(0, 0, 260, 28))
        if self is None:
            return None
        self.controller = controller
        self.setWantsLayer_(True)
        return self

    def acceptsFirstResponder(self):
        return True

    def becomeFirstResponder(self):
        self.controller.set_status("Press desired hotkey…")
        return True

    def keyDown_(self, event):
        keycode = int(event.keyCode())
        mods = int(event.modifierFlags())
        carbon_mods = _nsevent_flags_to_carbon_modifiers(mods)
        # Require at least one modifier
        if carbon_mods == 0:
            self.controller.set_status("Hotkey must include modifier (Ctrl/Opt/Cmd/Shift).")
            return
        self.controller.on_captured_hotkey(keycode, carbon_mods)

    def drawRect_(self, rect):
        NSColor.colorWithCalibratedWhite_alpha_(0.95, 1.0).set()
        NSRectFill(rect)
        border = NSBezierPath.bezierPathWithRect_(self.bounds())
        NSColor.colorWithCalibratedWhite_alpha_(0.0, 0.15).set()
        border.setLineWidth_(1.0)
        border.stroke()

        s = "Click here, then press keys…"
        attrs = {
            NSFontAttributeName: NSFont.systemFontOfSize_(12),
            NSForegroundColorAttributeName: NSColor.colorWithCalibratedWhite_alpha_(0.25, 1.0),
        }
        size = NSString.stringWithString_(s).sizeWithAttributes_(attrs)
        x = 8
        y = (self.bounds().size.height - size.height) / 2.0
        NSString.stringWithString_(s).drawAtPoint_withAttributes_(NSMakePoint(x, y), attrs)


class SettingsPanelController(NSObject):
    def initWithAppController_(self, app_controller):
        self = objc.super(SettingsPanelController, self).init()
        if self is None:
            return None
        self.app = app_controller
        self.panel = None
        self.status_label = None
        self.capture_view = None
        self._build_ui()
        return self

    def _build_ui(self):
        rect = NSMakeRect(0, 0, 420, 320)
        style = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskUtilityWindow
        self.panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, style, NSBackingStoreBuffered, False
        )
        self.panel.setTitle_("Settings")
        content = self.panel.contentView()

        y = 275

        # Hotkey enabled switch
        self.hotkey_switch = NSButton.alloc().initWithFrame_(NSMakeRect(20, y, 200, 24))
        self.hotkey_switch.setButtonType_(NSSwitchButton)
        self.hotkey_switch.setTitle_("Hotkey enabled")
        self.hotkey_switch.setTarget_(self)
        self.hotkey_switch.setAction_("onToggleHotkeyEnabled:")
        content.addSubview_(self.hotkey_switch)

        y -= 35

        # Current hotkey label
        self.hotkey_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, y, 360, 20))
        self.hotkey_label.setBezeled_(False)
        self.hotkey_label.setDrawsBackground_(False)
        self.hotkey_label.setEditable_(False)
        self.hotkey_label.setSelectable_(True)
        content.addSubview_(self.hotkey_label)

        y -= 35

        # Capture view
        self.capture_view = HotkeyCaptureView.alloc().initWithController_(self)
        self.capture_view.setFrame_(NSMakeRect(20, y, 260, 28))
        content.addSubview_(self.capture_view)

        self.capture_btn = NSButton.alloc().initWithFrame_(NSMakeRect(290, y, 110, 28))
        self.capture_btn.setTitle_("Capture…")
        self.capture_btn.setBezelStyle_(NSBezelStyleRounded)
        self.capture_btn.setTarget_(self)
        self.capture_btn.setAction_("onStartCapture:")
        content.addSubview_(self.capture_btn)

        y -= 40

        self.reset_btn = NSButton.alloc().initWithFrame_(NSMakeRect(20, y, 110, 28))
        self.reset_btn.setTitle_("Reset")
        self.reset_btn.setBezelStyle_(NSBezelStyleRounded)
        self.reset_btn.setTarget_(self)
        self.reset_btn.setAction_("onResetHotkey:")
        content.addSubview_(self.reset_btn)

        y -= 45

        # Notifications dropdown
        self.notif_popup = NSPopUpButton.alloc().initWithFrame_pullsDown_(NSMakeRect(20, y, 220, 26), False)
        self.notif_popup.addItemWithTitle_("Notifications: All")
        self.notif_popup.addItemWithTitle_("Notifications: Hotkey only")
        self.notif_popup.addItemWithTitle_("Notifications: Off")
        self.notif_popup.setTarget_(self)
        self.notif_popup.setAction_("onNotificationsChanged:")
        content.addSubview_(self.notif_popup)

        y -= 40

        # Pretty JSON toggle
        self.pretty_switch = NSButton.alloc().initWithFrame_(NSMakeRect(20, y, 200, 24))
        self.pretty_switch.setButtonType_(NSSwitchButton)
        self.pretty_switch.setTitle_("Pretty JSON (Mode B)")
        self.pretty_switch.setTarget_(self)
        self.pretty_switch.setAction_("onTogglePrettyJSON:")
        content.addSubview_(self.pretty_switch)

        y -= 45

        # Status line
        self.status_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, y, 380, 20))
        self.status_label.setBezeled_(False)
        self.status_label.setDrawsBackground_(False)
        self.status_label.setEditable_(False)
        self.status_label.setSelectable_(False)
        content.addSubview_(self.status_label)

        self.refresh()

    def show(self):
        self.refresh()
        self.panel.makeKeyAndOrderFront_(None)
        NSApp.activateIgnoringOtherApps_(True)

    def refresh(self):
        cfg = self.app.config
        self.hotkey_switch.setState_(1 if cfg.hotkey_enabled() else 0)
        self.hotkey_label.setStringValue_(f"Current hotkey: {self.app.format_hotkey(cfg.hotkey_keycode(), cfg.hotkey_modifiers())}")
        # notif
        nm = cfg.notifications_mode()
        if nm == NOTIF_ALL:
            self.notif_popup.selectItemAtIndex_(0)
        elif nm == NOTIF_HOTKEY_ONLY:
            self.notif_popup.selectItemAtIndex_(1)
        else:
            self.notif_popup.selectItemAtIndex_(2)
        self.pretty_switch.setState_(1 if cfg.json_pretty() else 0)
        self.set_status("")

    def set_status(self, msg: str):
        if self.status_label:
            self.status_label.setStringValue_(msg)

    # UI actions
    def onToggleHotkeyEnabled_(self, sender):
        enabled = bool(self.hotkey_switch.state() == 1)
        self.app.set_hotkey_enabled(enabled)
        self.refresh()

    def onStartCapture_(self, sender):
        if not CARBON_AVAILABLE:
            self.set_status("Carbon not available; hotkey unsupported on this system.")
            return
        self.panel.makeFirstResponder_(self.capture_view)
        self.set_status("Press desired hotkey…")

    def onResetHotkey_(self, sender):
        cfg = self.app.config
        cfg.set_hotkey(AppConfig.DEFAULT_HOTKEY_KEYCODE, int(AppConfig.DEFAULT_HOTKEY_MODIFIERS))
        self.app.apply_hotkey_from_config()
        self.refresh()
        self.set_status("Hotkey reset.")

    def onNotificationsChanged_(self, sender):
        idx = int(self.notif_popup.indexOfSelectedItem())
        if idx == 0:
            self.app.config.set_notifications_mode(NOTIF_ALL)
        elif idx == 1:
            self.app.config.set_notifications_mode(NOTIF_HOTKEY_ONLY)
        else:
            self.app.config.set_notifications_mode(NOTIF_OFF)
        # best-effort permission request
        if self.app.config.notifications_mode() != NOTIF_OFF:
            self.app.notifier.ensure_permission()
        self.refresh()
        self.set_status("Notifications updated.")

    def onTogglePrettyJSON_(self, sender):
        self.app.config.set_json_pretty(bool(self.pretty_switch.state() == 1))
        self.refresh()
        self.set_status("Pretty JSON updated.")

    # capture callback
    def on_captured_hotkey(self, keycode: int, carbon_mods: int):
        ok = self.app.try_apply_hotkey_candidate(keycode, carbon_mods)
        if ok:
            self.app.config.set_hotkey(keycode, carbon_mods)
            self.set_status("Hotkey applied.")
        else:
            self.set_status("Hotkey conflict/unavailable; reverted.")
        self.refresh()


# -----------------------------
# Prompt Panel
# -----------------------------

class PromptPanelController(NSObject):
    def initWithAppController_(self, app_controller):
        self = objc.super(PromptPanelController, self).init()
        if self is None:
            return None
        self.app = app_controller
        self.panel = None
        self.text_view = None
        self.role_popup = None
        self._build_ui()
        return self

    def _build_ui(self):
        rect = NSMakeRect(0, 0, 520, 360)
        style = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskUtilityWindow
        self.panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, style, NSBackingStoreBuffered, False
        )
        self.panel.setTitle_("Generate with Prompt")
        content = self.panel.contentView()

        # Role popup (v0.5 Phase 1: add User + system)
        self.role_popup = NSPopUpButton.alloc().initWithFrame_pullsDown_(NSMakeRect(20, 315, 200, 26), False)
        self.role_popup.addItemWithTitle_("user")
        self.role_popup.addItemWithTitle_("system")
        self.role_popup.addItemWithTitle_("User + system")
        content.addSubview_(self.role_popup)

        # Text view (multiline)
        scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(20, 70, 480, 230))
        scroll.setHasVerticalScroller_(True)
        scroll.setHasHorizontalScroller_(False)
        self.text_view = NSTextView.alloc().initWithFrame_(NSMakeRect(0, 0, 480, 230))
        scroll.setDocumentView_(self.text_view)
        content.addSubview_(scroll)

        # Buttons
        self.copy_btn = NSButton.alloc().initWithFrame_(NSMakeRect(310, 20, 90, 32))
        self.copy_btn.setTitle_("Copy")
        self.copy_btn.setBezelStyle_(NSBezelStyleRounded)
        self.copy_btn.setTarget_(self)
        self.copy_btn.setAction_("onCopy:")
        content.addSubview_(self.copy_btn)

        self.cancel_btn = NSButton.alloc().initWithFrame_(NSMakeRect(410, 20, 90, 32))
        self.cancel_btn.setTitle_("Cancel")
        self.cancel_btn.setBezelStyle_(NSBezelStyleRounded)
        self.cancel_btn.setTarget_(self)
        self.cancel_btn.setAction_("onCancel:")
        content.addSubview_(self.cancel_btn)

    def show(self):
        # default role selection to current config
        role_sel = self.app.config.default_role()
        if role_sel == ROLE_SYSTEM:
            self.role_popup.selectItemAtIndex_(1)
        elif role_sel == ROLE_USER_AND_SYSTEM:
            self.role_popup.selectItemAtIndex_(2)
        else:
            self.role_popup.selectItemAtIndex_(0)

        self.panel.makeKeyAndOrderFront_(None)
        NSApp.activateIgnoringOtherApps_(True)

    def onCopy_(self, sender):
        title = self.role_popup.titleOfSelectedItem()
        if title == "User + system":
            role_override = ROLE_USER_AND_SYSTEM
        elif title == "system":
            role_override = ROLE_SYSTEM
        else:
            role_override = ROLE_USER

        prompt = self.text_view.string() or ""
        self.app.generate_and_copy(source="menu", role_override=role_override, prompt=prompt)
        self.panel.orderOut_(None)

    def onCancel_(self, sender):
        self.panel.orderOut_(None)


# -----------------------------
# App Controller
# -----------------------------

class AppController(NSObject):
    def init(self):
        self = objc.super(AppController, self).init()
        if self is None:
            return None

        self.config = AppConfig()

        self.id_service = IdService()
        self.datetime_service = DateTimeService()
        self.entry_formatter = EntryFormatter()
        self.clipboard = ClipboardService()
        self.notifier = NotificationService()
        self.hotkey_service = HotkeyService(self._on_hotkey_triggered)

        self.status_item = None
        self.menu = None

        self.prompt_panel = None
        self.settings_panel = None

        self.overlay = None

        # Keep menu item references for state refresh
        self.role_item_user = None
        self.role_item_system = None
        self.role_item_user_and_system = None

        self.mode_item_a = None
        self.mode_item_b = None

        self.notif_item_all = None
        self.notif_item_hotkey = None
        self.notif_item_off = None

        self.hotkey_enabled_item = None

        # Overlay submenu items
        self.overlay_enabled_item = None
        self.overlay_click_generate_item = None
        self.overlay_click_prompt_item = None
        self.overlay_show_spaces_item = None
        self.overlay_hide_fullscreen_item = None

        return self

    def applicationDidFinishLaunching_(self, notification):
        NSLog("Clipboard JSON Logger starting v%@", APP_VERSION)

        # Build menu bar
        self._build_status_item()

        # Hotkey + notifications + overlay
        if self.config.notifications_mode() != NOTIF_OFF:
            self.notifier.ensure_permission()

        self.apply_hotkey_from_config()

        if self.config.overlay_enabled():
            self._start_overlay()

        self._refresh_menu_states()

    # -------------------------
    # Entry pipeline (v0.5 Phase 1: multi-entry)
    # -------------------------

    def _make_entries(self, role_selection: str, prompt: str) -> list:
        """
        v0.5 Phase 1:
          - role_selection = user | system | UserAndSystem
          - UserAndSystem => two entries with SAME id and datumtijd
        """
        p = prompt or ""
        entry_id = self.id_service.generate(self.config.id_strategy())
        dt = self.datetime_service.datumtijd_yyyymmdd(self.config.timezone_name())

        if role_selection == ROLE_USER_AND_SYSTEM:
            return [
                EntryModel(entry_id, ROLE_USER, p, dt),
                EntryModel(entry_id, ROLE_SYSTEM, p, dt),
            ]

        role = role_selection if role_selection in (ROLE_USER, ROLE_SYSTEM) else ROLE_USER
        return [EntryModel(entry_id, role, p, dt)]

    def _format_entry(self, entry: EntryModel) -> str:
        if self.config.output_mode() == OUTPUT_MODE_STRICT:
            return self.entry_formatter.format_strict_json(entry, pretty=self.config.json_pretty())
        return self.entry_formatter.format_loose_diary(entry)

    def generate_and_copy(self, source: str, role_override: str = None, prompt: str = ""):
        role_selection = role_override or self.config.default_role()
        entries = self._make_entries(role_selection, prompt)
        blocks = [self._format_entry(e) for e in entries]
        text = "\n\n".join(blocks)

        try:
            self.clipboard.copy_text(text)
            # log metadata only
            NSLog("Copied to clipboard (source=%@ mode=%@ role_selection=%@ id_strategy=%@)",
                  source, self.config.output_mode(), role_selection, self.config.id_strategy())
        except Exception as e:
            self._show_alert("Clipboard error", str(e))
            return

        if self._should_notify(source):
            self.notifier.notify_copied("Copied", "Entry copied to clipboard")

    def _should_notify(self, source: str) -> bool:
        mode = self.config.notifications_mode()
        if mode == NOTIF_OFF:
            return False
        if mode == NOTIF_HOTKEY_ONLY:
            return source == "hotkey"
        return True

    # -------------------------
    # Menu bar UI
    # -------------------------

    def _build_status_item(self):
        bar = NSStatusBar.systemStatusBar()
        self.status_item = bar.statusItemWithLength_(NSVariableStatusItemLength)
        # Minimal title
        self.status_item.button().setTitle_("{ }")

        self.menu = NSMenu.alloc().init()

        # 1) Generate Entry
        item_gen = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Generate Entry", "onGenerateEntry:", "")
        self.menu.addItem_(item_gen)

        # 2) Generate with Prompt…
        item_prompt = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Generate with Prompt…", "onGenerateWithPrompt:", "")
        self.menu.addItem_(item_prompt)

        self.menu.addItem_(NSMenuItem.separatorItem())

        # 4) Role submenu (v0.5 Phase 1)
        role_menu = NSMenu.alloc().init()
        self.role_item_user = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("user", "onSetRoleUser:", "")
        self.role_item_system = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("system", "onSetRoleSystem:", "")
        self.role_item_user_and_system = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("User + system", "onSetRoleUserAndSystem:", "")
        role_menu.addItem_(self.role_item_user)
        role_menu.addItem_(self.role_item_system)
        role_menu.addItem_(self.role_item_user_and_system)

        role_root = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Role", None, "")
        role_root.setSubmenu_(role_menu)
        self.menu.addItem_(role_root)

        # 5) Output Mode submenu
        mode_menu = NSMenu.alloc().init()
        self.mode_item_a = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Mode A (Loose diary)", "onSetModeA:", "")
        self.mode_item_b = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Mode B (Strict JSON)", "onSetModeB:", "")
        mode_menu.addItem_(self.mode_item_a)
        mode_menu.addItem_(self.mode_item_b)
        mode_root = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Output mode", None, "")
        mode_root.setSubmenu_(mode_menu)
        self.menu.addItem_(mode_root)

        # 6) Notifications submenu
        notif_menu = NSMenu.alloc().init()
        self.notif_item_all = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("All", "onSetNotifAll:", "")
        self.notif_item_hotkey = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Hotkey only", "onSetNotifHotkeyOnly:", "")
        self.notif_item_off = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Off", "onSetNotifOff:", "")
        notif_menu.addItem_(self.notif_item_all)
        notif_menu.addItem_(self.notif_item_hotkey)
        notif_menu.addItem_(self.notif_item_off)
        notif_root = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Notifications", None, "")
        notif_root.setSubmenu_(notif_menu)
        self.menu.addItem_(notif_root)

        # 7) Overlay submenu
        overlay_menu = NSMenu.alloc().init()
        self.overlay_enabled_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Enabled", "onToggleOverlayEnabled:", "")
        overlay_menu.addItem_(self.overlay_enabled_item)

        overlay_menu.addItem_(NSMenuItem.separatorItem())

        self.overlay_click_generate_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Click: Generate blank", "onOverlayClickGenerate:", "")
        self.overlay_click_prompt_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Click: Open prompt panel", "onOverlayClickPrompt:", "")
        overlay_menu.addItem_(self.overlay_click_generate_item)
        overlay_menu.addItem_(self.overlay_click_prompt_item)

        overlay_menu.addItem_(NSMenuItem.separatorItem())

        self.overlay_show_spaces_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Show on all Spaces", "onToggleOverlaySpaces:", "")
        self.overlay_hide_fullscreen_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Hide in fullscreen", "onToggleOverlayFullscreen:", "")
        overlay_menu.addItem_(self.overlay_show_spaces_item)
        overlay_menu.addItem_(self.overlay_hide_fullscreen_item)

        overlay_root = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Overlay", None, "")
        overlay_root.setSubmenu_(overlay_menu)
        self.menu.addItem_(overlay_root)

        self.menu.addItem_(NSMenuItem.separatorItem())

        # 9) Settings…
        item_settings = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Settings…", "onOpenSettings:", "")
        self.menu.addItem_(item_settings)

        # 10) Hotkey enabled toggle
        self.hotkey_enabled_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Hotkey enabled", "onToggleHotkeyEnabled:", "")
        self.menu.addItem_(self.hotkey_enabled_item)

        self.menu.addItem_(NSMenuItem.separatorItem())

        # Quit
        item_quit = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit", "onQuit:", "")
        self.menu.addItem_(item_quit)

        self.status_item.setMenu_(self.menu)

    def _refresh_menu_states(self):
        role = self.config.default_role()
        self.role_item_user.setState_(1 if role == ROLE_USER else 0)
        self.role_item_system.setState_(1 if role == ROLE_SYSTEM else 0)
        self.role_item_user_and_system.setState_(1 if role == ROLE_USER_AND_SYSTEM else 0)

        mode = self.config.output_mode()
        self.mode_item_a.setState_(1 if mode == OUTPUT_MODE_LOOSE else 0)
        self.mode_item_b.setState_(1 if mode == OUTPUT_MODE_STRICT else 0)

        nm = self.config.notifications_mode()
        self.notif_item_all.setState_(1 if nm == NOTIF_ALL else 0)
        self.notif_item_hotkey.setState_(1 if nm == NOTIF_HOTKEY_ONLY else 0)
        self.notif_item_off.setState_(1 if nm == NOTIF_OFF else 0)

        self.hotkey_enabled_item.setState_(1 if self.config.hotkey_enabled() else 0)

        # Overlay
        self.overlay_enabled_item.setState_(1 if self.config.overlay_enabled() else 0)
        ca = self.config.overlay_click_action()
        self.overlay_click_generate_item.setState_(1 if ca == OVERLAY_CLICK_GENERATE else 0)
        self.overlay_click_prompt_item.setState_(1 if ca == OVERLAY_CLICK_PROMPT else 0)
        self.overlay_show_spaces_item.setState_(1 if self.config.overlay_show_all_spaces() else 0)
        self.overlay_hide_fullscreen_item.setState_(1 if self.config.overlay_hide_in_fullscreen() else 0)

    # -------------------------
    # Menu actions
    # -------------------------

    def onGenerateEntry_(self, sender):
        self.generate_and_copy(source="menu")

    def onGenerateWithPrompt_(self, sender):
        if self.prompt_panel is None:
            self.prompt_panel = PromptPanelController.alloc().initWithAppController_(self)
        self.prompt_panel.show()

    # Role actions
    def onSetRoleUser_(self, sender):
        self.config.set_default_role(ROLE_USER)
        self._refresh_menu_states()

    def onSetRoleSystem_(self, sender):
        self.config.set_default_role(ROLE_SYSTEM)
        self._refresh_menu_states()

    def onSetRoleUserAndSystem_(self, sender):
        self.config.set_default_role(ROLE_USER_AND_SYSTEM)
        self._refresh_menu_states()

    # Output mode actions
    def onSetModeA_(self, sender):
        self.config.set_output_mode(OUTPUT_MODE_LOOSE)
        self._refresh_menu_states()

    def onSetModeB_(self, sender):
        self.config.set_output_mode(OUTPUT_MODE_STRICT)
        self._refresh_menu_states()

    # Notification actions
    def onSetNotifAll_(self, sender):
        self.config.set_notifications_mode(NOTIF_ALL)
        self.notifier.ensure_permission()
        self._refresh_menu_states()

    def onSetNotifHotkeyOnly_(self, sender):
        self.config.set_notifications_mode(NOTIF_HOTKEY_ONLY)
        self.notifier.ensure_permission()
        self._refresh_menu_states()

    def onSetNotifOff_(self, sender):
        self.config.set_notifications_mode(NOTIF_OFF)
        self._refresh_menu_states()

    # Settings
    def onOpenSettings_(self, sender):
        if self.settings_panel is None:
            self.settings_panel = SettingsPanelController.alloc().initWithAppController_(self)
        self.settings_panel.show()

    # Hotkey enabled
    def onToggleHotkeyEnabled_(self, sender):
        enabled = not self.config.hotkey_enabled()
        self.set_hotkey_enabled(enabled)
        self._refresh_menu_states()

    def set_hotkey_enabled(self, enabled: bool):
        self.config.set_hotkey_enabled(enabled)
        self.apply_hotkey_from_config()

    def apply_hotkey_from_config(self):
        if not CARBON_AVAILABLE:
            # If Carbon missing, keep app usable
            return
        if self.config.hotkey_enabled():
            ok = self.hotkey_service.start(self.config.hotkey_keycode(), self.config.hotkey_modifiers())
            if not ok:
                # disable if cannot register
                self.config.set_hotkey_enabled(False)
                self.hotkey_service.stop()
        else:
            self.hotkey_service.stop()
        self._refresh_menu_states()

    def try_apply_hotkey_candidate(self, keycode: int, carbon_mods: int) -> bool:
        """
        Stop current hotkey, attempt candidate. If fails, restore previous.
        """
        if not CARBON_AVAILABLE:
            return False
        prev_enabled = self.config.hotkey_enabled()
        prev_keycode = self.config.hotkey_keycode()
        prev_mods = self.config.hotkey_modifiers()

        # Temporarily enable for test
        self.hotkey_service.stop()
        ok = self.hotkey_service.start(keycode, carbon_mods)
        if ok:
            self.config.set_hotkey_enabled(True)
            return True

        # Restore previous if needed
        self.hotkey_service.stop()
        if prev_enabled:
            self.hotkey_service.start(prev_keycode, prev_mods)
        self.config.set_hotkey_enabled(prev_enabled)
        return False

    def format_hotkey(self, keycode: int, modifiers: int) -> str:
        # Human-ish representation
        parts = []
        if CARBON_AVAILABLE:
            if modifiers & Events.controlKey:
                parts.append("⌃")
            if modifiers & Events.optionKey:
                parts.append("⌥")
            if modifiers & Events.shiftKey:
                parts.append("⇧")
            if modifiers & Events.cmdKey:
                parts.append("⌘")
        parts.append(f"KeyCode({keycode})")
        return "".join(parts)

    def _on_hotkey_triggered(self):
        self.generate_and_copy(source="hotkey")

    # Overlay actions
    def onToggleOverlayEnabled_(self, sender):
        enabled = not self.config.overlay_enabled()
        self.config.set_overlay_enabled(enabled)
        if enabled:
            self._start_overlay()
        else:
            self._stop_overlay()
        self._refresh_menu_states()

    def onOverlayClickGenerate_(self, sender):
        self.config.set_overlay_click_action(OVERLAY_CLICK_GENERATE)
        if self.overlay:
            self.overlay.apply_behavior()
        self._refresh_menu_states()

    def onOverlayClickPrompt_(self, sender):
        self.config.set_overlay_click_action(OVERLAY_CLICK_PROMPT)
        if self.overlay:
            self.overlay.apply_behavior()
        self._refresh_menu_states()

    def onToggleOverlaySpaces_(self, sender):
        self.config.set_overlay_show_all_spaces(not self.config.overlay_show_all_spaces())
        if self.overlay:
            self.overlay.apply_behavior()
        self._refresh_menu_states()

    def onToggleOverlayFullscreen_(self, sender):
        self.config.set_overlay_hide_in_fullscreen(not self.config.overlay_hide_in_fullscreen())
        if self.overlay:
            self.overlay.apply_behavior()
        self._refresh_menu_states()

    def _start_overlay(self):
        if self.overlay is None:
            self.overlay = OverlayBubbleController.alloc().initWithAppController_(self)
        self.overlay.show()

    def _stop_overlay(self):
        if self.overlay is not None:
            self.overlay.hide()

    def build_overlay_context_menu(self):
        menu = NSMenu.alloc().init()

        mi1 = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Generate Entry", "onGenerateEntry:", "")
        menu.addItem_(mi1)

        mi2 = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Generate with Prompt…", "onGenerateWithPrompt:", "")
        menu.addItem_(mi2)

        menu.addItem_(NSMenuItem.separatorItem())

        # Output mode quick toggle
        m_mode_a = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Mode A (Loose diary)", "onSetModeA:", "")
        m_mode_b = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Mode B (Strict JSON)", "onSetModeB:", "")
        m_mode_a.setState_(1 if self.config.output_mode() == OUTPUT_MODE_LOOSE else 0)
        m_mode_b.setState_(1 if self.config.output_mode() == OUTPUT_MODE_STRICT else 0)
        menu.addItem_(m_mode_a)
        menu.addItem_(m_mode_b)

        menu.addItem_(NSMenuItem.separatorItem())

        ms = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Open Settings…", "onOpenSettings:", "")
        menu.addItem_(ms)

        mh = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Hide Overlay", "onToggleOverlayEnabled:", "")
        menu.addItem_(mh)

        menu.addItem_(NSMenuItem.separatorItem())

        mq = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit", "onQuit:", "")
        menu.addItem_(mq)

        return menu

    # Quit
    def onQuit_(self, sender):
        if self.overlay:
            self.overlay.close()
        NSApp.terminate_(None)

    # Alert
    def _show_alert(self, title: str, message: str):
        try:
            alert = NSAlert.alloc().init()
            alert.setMessageText_(title)
            alert.setInformativeText_(message)
            alert.setAlertStyle_(NSAlertStyleWarning)
            alert.runModal()
        except Exception:
            # last resort
            NSLog("ALERT: %@ - %@", title, message)


# -----------------------------
# Main
# -----------------------------

def main():
    app = NSApplication.sharedApplication()
    # Prefer no Dock icon (also set LSUIElement=True in Info.plist when packaging)
    try:
        app.setActivationPolicy_(NSApplicationActivationPolicyProhibited)
    except Exception:
        pass

    delegate = AppController.alloc().init()
    app.setDelegate_(delegate)
    app.run()


if __name__ == "__main__":
    main()
```

***

## Ontwikkelcyclus‑opties (zoals jouw procesregels)

Kies **één nummer** (geen extra bevestiging nodig):

1.  **FS → TS v0.5.0 afronden (Phase 2/3)**: ik maak een complete TS v0.5.0 (incl. runtime i18n + config import/export schema + UI refresh strategy).
2.  **Build plan review v0.5**: praktische afvink‑checklist per commit + smoke tests (py2app‑run).
3.  **Direct naar code — Fase 2 (i18n runtime + Afrikaans default)**: commit‑ready patch + volledige file update.
4.  **Direct naar code — Fase 3 (JSON config export/import + startup apply)**: commit‑ready patch + schema + atomic write.

***

### Bronnen / knowledge base (zoals gevraagd)

*   Ik heb enterprise search gebruikt om jouw bestaande `clipboard_json_logger.py` te vinden, maar die kwam niet terug in de resultaten; daarom lever ik een complete implementatie op basis van jouw **TS v0.4** uit de chat en de **Fase 1** requirements. [\[Document L...th useful  | Viva Engage\]](https://engage.cloud.microsoft/main/threads/eyJfdHlwZSI6IlRocmVhZCIsImlkIjoiMzY2MzYzOTUwOTEyMzA3MiJ9), [\[fugro.sharepoint.com\]](https://fugro.sharepoint.com/sites/Projects/Shared%20Documents/Vessels/West_White_Rose/EMS/231419-AtlanticXL-RECON-2024NOV11/E-LOGS/Server_Backup/Desktop/Seagate%20Backup%20Software/Toolkit/Backup/HUSKYEMSSERVER/c/Users/huskyadmin/.PyCharmCE2018.3/config/plugins/availables.xml?web=1), [\[UK-STM-OPL...r Programs | Word\]](https://fugro.sharepoint.com/sites/FugroUKBMS/_layouts/15/Doc.aspx?sourcedoc=%7B39D93B5E-29C6-4E3D-8AB1-D1D70D314D6A%7D&file=UK-STM-OPL-PR-003%20Version%20Control%20-%20Logger%20Programs.docx&action=default&mobileredirect=true&DefaultItemOpen=1), [\[
✅ The wor...has chang | Viva Engage\]](https://engage.cloud.microsoft/main/threads/eyJfdHlwZSI6IlRocmVhZCIsImlkIjoiMzU2MDgxNjkwOTQ3NTg0MCJ9), [\[Discovery...hrough the | Viva Engage\]](https://engage.cloud.microsoft/main/threads/eyJfdHlwZSI6IlRocmVhZCIsImlkIjoiMzYxODg1MDAwMzc5NTk2OCJ9), [\[loggernet | PDF\]](https://fugro.sharepoint.com/sites/Monitoring/Monitoring%20Experts%20%20Loggersystemen/Uitzoeken%20-%20Data%20dump/Campbell/manuals/Software%20Applications/loggernet.pdf?web=1), [\[USA-MAI-OP...VS Profile | Word\]](https://fugro.sharepoint.com/sites/FUSA/FUSAMI/_layouts/15/Doc.aspx?sourcedoc=%7BF5BFAB50-FB9C-4380-A94F-9CD55C35C142%7D&file=USA-MAI-OPS-GU-0007%20MiniSVS%20Profile.docx&action=default&mobileredirect=true&DefaultItemOpen=1), [\[GLOB-USV-O...l Logbooks | Word\]](https://fugro.sharepoint.com/sites/FugroGBMSHome/_layouts/15/Doc.aspx?sourcedoc=%7B1A97CBC9-2624-4D8C-9DC4-01B7667B7CEC%7D&file=GLOB-USV-OPL-PR-030%20USV%20Navtor%20Digital%20Logbooks.docx&action=default&mobileredirect=true&DefaultItemOpen=1), [\[Geophysica...762) Rev A | PDF\]](https://fugro.sharepoint.com/sites/APAC-BMS/WorkingDocuments/Legacy%20(Check%20and%20Archive%202026)/CHECK%20AND%20ARCHIVE%20-%20Legacy%20BMS/Geotechnical/2.%20Internal%20Document%20Review%20(IDR)/IDR%20Geotechnical%20Work%20Instructions%20for%20Review%20(x%2010)/Geophysical%20Wireline%20Logging%20P%20and%20S%20Wave%20Suspension%20Logger%20and%20Caliper%20Ops%20Work%20Instruction%20(SEA-M-25762)%20Rev%20A.pdf?web=1)

Wil je dat ik nu meteen doorga met **optie 3 (Fase 2 i18n)** of **optie 4 (Fase 3 config)**?

