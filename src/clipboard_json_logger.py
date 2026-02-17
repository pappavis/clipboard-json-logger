# Clipboard JSON Logger
# Version: 0.5.0
# Date: 2026-02-18
#
# macOS Menu Bar utility (PyObjC) to generate "chatlog entry" snippet(s)
# and copy them to the clipboard.
#
# Output modes:
# - Mode A: loose diary format (default)
# - Mode B: strict JSON (toggle) + pretty toggle
#
# Role modes:
# - user
# - system
# - User + system (generates TWO blocks with SAME id + datumtijd)
#
# v0.3+: multiline prompt panel, notifications, hotkey + capture UI
# v0.4+: overlay bubble (floating button)
# v0.5+: Afrikaans default UI + runtime language switch (no restart),
#        config export/import to local JSON + apply at startup,
#        role "User + system"

from __future__ import annotations

import json
import os
import secrets
import string
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:
    ZoneInfo = None  # type: ignore

import objc

# Prefer Cocoa to avoid "Foundation" module name collisions in some venvs.
try:
    from Cocoa import NSObject, NSUserDefaults, NSLog
except Exception:
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
    NSControlStateValueOn,
    NSControlStateValueOff,
    NSPanel,
    NSWindow,
    NSWindowStyleMaskTitled,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskUtilityWindow,
    NSWindowStyleMaskResizable,
    NSWindowStyleMaskBorderless,
    NSBackingStoreBuffered,
    NSView,
    NSScrollView,
    NSTextView,
    NSTextField,
    NSPopUpButton,
    NSButton,
    NSSwitchButton,
    NSMomentaryPushInButton,
    NSBezelStyleRounded,
    NSFont,
    NSColor,
    NSBezierPath,
    NSMakeRect,
    NSEvent,
    NSScreen,
    NSFloatingWindowLevel,
    NSStatusWindowLevel,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorFullScreenAuxiliary,
    NSWindowCollectionBehaviorMoveToActiveSpace,
)
from PyObjCTools import AppHelper

# ---- Optional Carbon hotkey (best-effort) ----
CARBON_AVAILABLE = False
try:
    from Carbon import Events, HIToolbox

    CARBON_AVAILABLE = True
except Exception:
    CARBON_AVAILABLE = False

# ---- Optional UserNotifications (best-effort) ----
UN_AVAILABLE = False
try:
    from UserNotifications import (
        UNUserNotificationCenter,
        UNAuthorizationOptionAlert,
        UNAuthorizationOptionSound,
        UNMutableNotificationContent,
        UNNotificationRequest,
    )

    UN_AVAILABLE = True
except Exception:
    UN_AVAILABLE = False


APP_NAME = "Clipboard JSON Logger"
APP_VERSION = "0.5.0"
APP_BUILD_DATE = "2026-02-18"
DEFAULT_TIMEZONE = "Europe/Amsterdam"


# ----------------------------
# i18n
# ----------------------------
# Language codes:
# - af: Afrikaans (default)
# - nl: Nederlands
# - en: English
STRINGS: Dict[str, Dict[str, str]] = {
    "af": {
        "menu.generate": "Genereer inskrywing",
        "menu.generate_prompt": "Genereer met prompt…",
        "menu.role": "Rol",
        "menu.role.user": "user",
        "menu.role.system": "system",
        "menu.role.user_and_system": "User + system",
        "menu.output_mode": "Uitvoer-modus",
        "menu.mode.a": "Los dagboek (Modus A)",
        "menu.mode.b": "Streng JSON (Modus B)",
        "menu.notifications": "Kennisgewings",
        "menu.notif.all": "Alles",
        "menu.notif.hotkey": "Slegs sneltoets",
        "menu.notif.off": "Af",
        "menu.overlay": "Overlay-borrel",
        "menu.overlay.enabled": "Overlay geaktiveer",
        "menu.overlay.click_action": "Klik-aksie",
        "menu.overlay.click_blank": "Genereer leë inskrywing",
        "menu.overlay.click_prompt": "Open prompt-paneel",
        "menu.overlay.all_spaces": "Wys op alle Spaces",
        "menu.overlay.hide_fullscreen": "Versteek in volskerm",
        "menu.settings": "Instellings…",
        "menu.hotkey_enabled": "Sneltoets geaktiveer",
        "menu.quit": "Sluit af",
        "panel.prompt.title": "Genereer met prompt",
        "panel.prompt.role": "Rol:",
        "panel.prompt.copy": "Kopieer inskrywing",
        "panel.prompt.cancel": "Kanselleer",
        "panel.settings.title": "Instellings",
        "panel.settings.hotkey_enabled": "Sneltoets geaktiveer",
        "panel.settings.current_hotkey": "Huidige sneltoets:",
        "panel.settings.capture": "Vang sneltoets…",
        "panel.settings.reset": "Herstel",
        "panel.settings.notifications": "Kennisgewings:",
        "panel.settings.pretty": "Netjiese JSON (Modus B)",
        "panel.settings.language": "Taal:",
        "panel.settings.export": "Skryf config na JSON",
        "panel.settings.import": "Lees config van JSON",
        "status.hotkey_missing": "Sneltoets nie beskikbaar nie (Carbon ontbreek).",
        "status.press_combo": "Druk nou ’n sleutel-kombinasie… (minstens 1 modifier)",
        "status.rejected_modifier": "Verwerp: voeg minstens 1 modifier by (Ctrl/Opt/Cmd/Shift).",
        "status.hotkey_applied": "Sneltoets toegepas.",
        "status.hotkey_reset_applied": "Sneltoets herstel + toegepas.",
        "status.hotkey_failed": "Sneltoets misluk: %s",
        "status.export_ok": "Config geskryf: %s",
        "status.export_fail": "Kon nie config skryf nie: %s",
        "status.import_ok": "Config toegepas.",
        "status.import_fail": "Kon nie config lees/toepas nie: %s",
        "alert.clipboard.title": "Clipboard-fout",
        "alert.hotkey.title": "Sneltoets",
        "alert.hotkey.msg": "Sneltoets konflik/onbeskikbaar. Probeer ’n ander kombinasie in Instellings…",
        "notify.title": "Inskrywing gekopieer",
        "notify.body": "rol=%s, modus=%s, blokke=%d",
    },
    "nl": {
        "menu.generate": "Entry genereren",
        "menu.generate_prompt": "Genereren met prompt…",
        "menu.role": "Rol",
        "menu.role.user": "user",
        "menu.role.system": "system",
        "menu.role.user_and_system": "User + system",
        "menu.output_mode": "Output-modus",
        "menu.mode.a": "Los dagboek (Modus A)",
        "menu.mode.b": "Strikte JSON (Modus B)",
        "menu.notifications": "Meldingen",
        "menu.notif.all": "Alles",
        "menu.notif.hotkey": "Alleen hotkey",
        "menu.notif.off": "Uit",
        "menu.overlay": "Overlay-bubble",
        "menu.overlay.enabled": "Overlay ingeschakeld",
        "menu.overlay.click_action": "Klik-actie",
        "menu.overlay.click_blank": "Lege entry genereren",
        "menu.overlay.click_prompt": "Prompt-paneel openen",
        "menu.overlay.all_spaces": "Toon op alle Spaces",
        "menu.overlay.hide_fullscreen": "Verbergen in fullscreen",
        "menu.settings": "Instellingen…",
        "menu.hotkey_enabled": "Hotkey ingeschakeld",
        "menu.quit": "Afsluiten",
        "panel.prompt.title": "Genereren met prompt",
        "panel.prompt.role": "Rol:",
        "panel.prompt.copy": "Entry kopiëren",
        "panel.prompt.cancel": "Annuleren",
        "panel.settings.title": "Instellingen",
        "panel.settings.hotkey_enabled": "Hotkey ingeschakeld",
        "panel.settings.current_hotkey": "Huidige hotkey:",
        "panel.settings.capture": "Hotkey vastleggen…",
        "panel.settings.reset": "Reset",
        "panel.settings.notifications": "Meldingen:",
        "panel.settings.pretty": "Pretty JSON (Modus B)",
        "panel.settings.language": "Taal:",
        "panel.settings.export": "Config naar JSON schrijven",
        "panel.settings.import": "Config uit JSON lezen",
        "status.hotkey_missing": "Hotkey niet beschikbaar (Carbon ontbreekt).",
        "status.press_combo": "Druk nu een toetscombinatie… (minstens 1 modifier)",
        "status.rejected_modifier": "Afgewezen: voeg minstens 1 modifier toe (Ctrl/Opt/Cmd/Shift).",
        "status.hotkey_applied": "Hotkey toegepast.",
        "status.hotkey_reset_applied": "Hotkey gereset + toegepast.",
        "status.hotkey_failed": "Hotkey mislukt: %s",
        "status.export_ok": "Config geschreven: %s",
        "status.export_fail": "Config schrijven mislukt: %s",
        "status.import_ok": "Config toegepast.",
        "status.import_fail": "Config lezen/toepassen mislukt: %s",
        "alert.clipboard.title": "Clipboard-fout",
        "alert.hotkey.title": "Hotkey",
        "alert.hotkey.msg": "Hotkey conflict/onbeschikbaar. Probeer een andere combo in Instellingen…",
        "notify.title": "Entry gekopieerd",
        "notify.body": "rol=%s, modus=%s, blokken=%d",
    },
    "en": {
        "menu.generate": "Generate Entry",
        "menu.generate_prompt": "Generate with Prompt…",
        "menu.role": "Role",
        "menu.role.user": "user",
        "menu.role.system": "system",
        "menu.role.user_and_system": "User + system",
        "menu.output_mode": "Output Mode",
        "menu.mode.a": "Loose diary (Mode A)",
        "menu.mode.b": "Strict JSON (Mode B)",
        "menu.notifications": "Notifications",
        "menu.notif.all": "All",
        "menu.notif.hotkey": "Hotkey only",
        "menu.notif.off": "Off",
        "menu.overlay": "Overlay Bubble",
        "menu.overlay.enabled": "Overlay enabled",
        "menu.overlay.click_action": "Click action",
        "menu.overlay.click_blank": "Generate blank entry",
        "menu.overlay.click_prompt": "Open prompt panel",
        "menu.overlay.all_spaces": "Show on all Spaces",
        "menu.overlay.hide_fullscreen": "Hide in fullscreen",
        "menu.settings": "Settings…",
        "menu.hotkey_enabled": "Hotkey Enabled",
        "menu.quit": "Quit",
        "panel.prompt.title": "Generate with Prompt",
        "panel.prompt.role": "Role:",
        "panel.prompt.copy": "Copy Entry",
        "panel.prompt.cancel": "Cancel",
        "panel.settings.title": "Settings",
        "panel.settings.hotkey_enabled": "Hotkey Enabled",
        "panel.settings.current_hotkey": "Current hotkey:",
        "panel.settings.capture": "Capture Hotkey…",
        "panel.settings.reset": "Reset",
        "panel.settings.notifications": "Notifications:",
        "panel.settings.pretty": "Pretty JSON (Mode B)",
        "panel.settings.language": "Language:",
        "panel.settings.export": "Write config to JSON",
        "panel.settings.import": "Read config from JSON",
        "status.hotkey_missing": "Hotkey not available (Carbon missing).",
        "status.press_combo": "Press a key combo now… (requires at least 1 modifier)",
        "status.rejected_modifier": "Rejected: add at least 1 modifier (Ctrl/Opt/Cmd/Shift).",
        "status.hotkey_applied": "Hotkey applied.",
        "status.hotkey_reset_applied": "Hotkey reset + applied.",
        "status.hotkey_failed": "Hotkey failed: %s",
        "status.export_ok": "Config written: %s",
        "status.export_fail": "Failed to write config: %s",
        "status.import_ok": "Config applied.",
        "status.import_fail": "Failed to read/apply config: %s",
        "alert.clipboard.title": "Clipboard error",
        "alert.hotkey.title": "Hotkey",
        "alert.hotkey.msg": "Hotkey conflict/unavailable. Try another combo in Settings…",
        "notify.title": "Copied entry",
        "notify.body": "role=%s, mode=%s, blocks=%d",
    },
}


# ----------------------------
# Keys (NSUserDefaults)
# ----------------------------
K_DEFAULT_ROLE = "default_role"  # user | system | UserAndSystem
K_ID_STRATEGY = "id_strategy"  # short_id | uuid4
K_OUTPUT_MODE = "output_mode"  # loose_diary | strict_json
K_DATUMTIJD_STRATEGY = "datumtijd_strategy"  # date_yyyymmdd
K_HOTKEY_ENABLED = "hotkey_enabled"
K_HOTKEY_KEYCODE = "hotkey_keycode"
K_HOTKEY_MODIFIERS = "hotkey_modifiers"

K_NOTIFICATIONS_MODE = "notifications_mode"  # all | hotkey_only | off
K_JSON_PRETTY = "json_pretty"  # bool

# Overlay (v0.4+)
K_OVERLAY_ENABLED = "overlay_enabled"
K_OVERLAY_CLICK_ACTION = "overlay_click_action"  # generate_blank | open_prompt_panel
K_OVERLAY_SHOW_ALL_SPACES = "overlay_show_all_spaces"  # bool
K_OVERLAY_HIDE_FULLSCREEN = "overlay_hide_in_fullscreen"  # bool
K_OVERLAY_POS_X = "overlay_pos_x"
K_OVERLAY_POS_Y = "overlay_pos_y"
K_OVERLAY_SCREEN_HINT = "overlay_screen_hint"

# i18n (v0.5)
K_UI_LANGUAGE = "ui_language"  # af | nl | en


# ----------------------------
# Domain
# ----------------------------
@dataclass(frozen=True)
class EntryModel:
    id: str
    role: str
    prompt: str
    datumtijd: str


# ----------------------------
# Config
# ----------------------------
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
            self.ud.setInteger_forKey_(HIToolbox.kVK_ANSI_J if CARBON_AVAILABLE else 38, K_HOTKEY_KEYCODE)

        if self.ud.objectForKey_(K_HOTKEY_MODIFIERS) is None:
            default_mods = 0
            if CARBON_AVAILABLE:
                default_mods = HIToolbox.controlKey | HIToolbox.optionKey | HIToolbox.cmdKey
            self.ud.setInteger_forKey_(int(default_mods), K_HOTKEY_MODIFIERS)

        if self.ud.objectForKey_(K_NOTIFICATIONS_MODE) is None:
            self.ud.setObject_forKey_("hotkey_only", K_NOTIFICATIONS_MODE)

        if self.ud.objectForKey_(K_JSON_PRETTY) is None:
            self.ud.setBool_forKey_(True, K_JSON_PRETTY)

        # Overlay defaults
        if self.ud.objectForKey_(K_OVERLAY_ENABLED) is None:
            self.ud.setBool_forKey_(False, K_OVERLAY_ENABLED)

        if self.ud.objectForKey_(K_OVERLAY_CLICK_ACTION) is None:
            self.ud.setObject_forKey_("generate_blank", K_OVERLAY_CLICK_ACTION)

        if self.ud.objectForKey_(K_OVERLAY_SHOW_ALL_SPACES) is None:
            self.ud.setBool_forKey_(True, K_OVERLAY_SHOW_ALL_SPACES)

        if self.ud.objectForKey_(K_OVERLAY_HIDE_FULLSCREEN) is None:
            self.ud.setBool_forKey_(True, K_OVERLAY_HIDE_FULLSCREEN)

        if self.ud.objectForKey_(K_OVERLAY_POS_X) is None:
            self.ud.setDouble_forKey_(0.0, K_OVERLAY_POS_X)

        if self.ud.objectForKey_(K_OVERLAY_POS_Y) is None:
            self.ud.setDouble_forKey_(0.0, K_OVERLAY_POS_Y)

        if self.ud.objectForKey_(K_OVERLAY_SCREEN_HINT) is None:
            self.ud.setInteger_forKey_(-1, K_OVERLAY_SCREEN_HINT)

        # i18n default: Afrikaans
        if self.ud.objectForKey_(K_UI_LANGUAGE) is None:
            self.ud.setObject_forKey_("af", K_UI_LANGUAGE)

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

    @property
    def notifications_mode(self) -> str:
        return str(self.ud.stringForKey_(K_NOTIFICATIONS_MODE) or "hotkey_only")

    @property
    def json_pretty(self) -> bool:
        return bool(self.ud.boolForKey_(K_JSON_PRETTY))

    @property
    def overlay_enabled(self) -> bool:
        return bool(self.ud.boolForKey_(K_OVERLAY_ENABLED))

    @property
    def overlay_click_action(self) -> str:
        return str(self.ud.stringForKey_(K_OVERLAY_CLICK_ACTION) or "generate_blank")

    @property
    def overlay_show_all_spaces(self) -> bool:
        return bool(self.ud.boolForKey_(K_OVERLAY_SHOW_ALL_SPACES))

    @property
    def overlay_hide_in_fullscreen(self) -> bool:
        return bool(self.ud.boolForKey_(K_OVERLAY_HIDE_FULLSCREEN))

    @property
    def overlay_pos(self) -> Tuple[float, float]:
        return (float(self.ud.doubleForKey_(K_OVERLAY_POS_X)), float(self.ud.doubleForKey_(K_OVERLAY_POS_Y)))

    @property
    def overlay_screen_hint(self) -> int:
        return int(self.ud.integerForKey_(K_OVERLAY_SCREEN_HINT))

    @property
    def ui_language(self) -> str:
        return str(self.ud.stringForKey_(K_UI_LANGUAGE) or "af")

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

    def set_hotkey(self, keycode: int, modifiers: int) -> None:
        self.ud.setInteger_forKey_(int(keycode), K_HOTKEY_KEYCODE)
        self.ud.setInteger_forKey_(int(modifiers), K_HOTKEY_MODIFIERS)
        self.ud.synchronize()

    def set_notifications_mode(self, mode: str) -> None:
        self.ud.setObject_forKey_(mode, K_NOTIFICATIONS_MODE)
        self.ud.synchronize()

    def set_json_pretty(self, pretty: bool) -> None:
        self.ud.setBool_forKey_(bool(pretty), K_JSON_PRETTY)
        self.ud.synchronize()

    def set_overlay_enabled(self, enabled: bool) -> None:
        self.ud.setBool_forKey_(bool(enabled), K_OVERLAY_ENABLED)
        self.ud.synchronize()

    def set_overlay_click_action(self, action: str) -> None:
        self.ud.setObject_forKey_(action, K_OVERLAY_CLICK_ACTION)
        self.ud.synchronize()

    def set_overlay_show_all_spaces(self, enabled: bool) -> None:
        self.ud.setBool_forKey_(bool(enabled), K_OVERLAY_SHOW_ALL_SPACES)
        self.ud.synchronize()

    def set_overlay_hide_in_fullscreen(self, enabled: bool) -> None:
        self.ud.setBool_forKey_(bool(enabled), K_OVERLAY_HIDE_FULLSCREEN)
        self.ud.synchronize()

    def set_overlay_pos(self, x: float, y: float) -> None:
        self.ud.setDouble_forKey_(float(x), K_OVERLAY_POS_X)
        self.ud.setDouble_forKey_(float(y), K_OVERLAY_POS_Y)
        self.ud.synchronize()

    def set_overlay_screen_hint(self, idx: int) -> None:
        self.ud.setInteger_forKey_(int(idx), K_OVERLAY_SCREEN_HINT)
        self.ud.synchronize()

    def set_ui_language(self, lang: str) -> None:
        self.ud.setObject_forKey_(lang, K_UI_LANGUAGE)
        self.ud.synchronize()


# ----------------------------
# Services
# ----------------------------
class IdService:
    def __init__(self, strategy: str = "short_id", short_len: int = 9) -> None:
        self.strategy = strategy
        self.short_len = max(6, min(int(short_len), 32))
        self._chars = string.ascii_lowercase + string.digits

    def generate(self) -> str:
        if self.strategy == "uuid4":
            return str(uuid.uuid4())
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
    Mode A: loose diary format (not necessarily valid JSON)
    Mode B: strict JSON (valid JSON)
    """

    @staticmethod
    def format_loose_diary(entry: EntryModel) -> str:
        prompt_text = entry.prompt or ""
        # Keep this intentionally close to user's diary example (loose / python-ish dict style).
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
    def format_strict_json(entry: EntryModel, pretty: bool = True) -> str:
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
    def __init__(self) -> None:
        self.pb = NSPasteboard.generalPasteboard()

    def copy_text(self, text: str) -> None:
        self.pb.declareTypes_owner_([NSStringPboardType], None)
        ok = self.pb.setString_forType_(text, NSStringPboardType)
        if not ok:
            raise RuntimeError("Failed to write to NSPasteboard")


class NotificationService:
    """
    Best-effort macOS notifications. If UserNotifications isn't available or permission is denied,
    degrade gracefully (no crash).
    """

    def __init__(self) -> None:
        self._center = None
        self._permission_requested = False

        if UN_AVAILABLE:
            try:
                self._center = UNUserNotificationCenter.currentNotificationCenter()
            except Exception:
                self._center = None

    def is_available(self) -> bool:
        return self._center is not None

    def ensure_permission(self) -> None:
        if not self.is_available():
            return
        if self._permission_requested:
            return

        self._permission_requested = True
        options = int(UNAuthorizationOptionAlert | UNAuthorizationOptionSound)

        def _cb(granted, error):
            if error is not None:
                try:
                    NSLog("Notification permission error: %@", str(error))
                except Exception:
                    pass
            else:
                NSLog("Notification permission granted=%@", "true" if granted else "false")

        try:
            self._center.requestAuthorizationWithOptions_completionHandler_(options, _cb)
        except Exception as e:
            NSLog("Notification permission request failed: %@", str(e))

    def notify(self, title: str, body: str) -> None:
        if not self.is_available():
            return

        self.ensure_permission()

        try:
            content = UNMutableNotificationContent.alloc().init()
            content.setTitle_(title)
            content.setBody_(body)

            req = UNNotificationRequest.requestWithIdentifier_content_trigger_(
                str(uuid.uuid4()), content, None
            )
            self._center.addNotificationRequest_withCompletionHandler_(req, None)
        except Exception as e:
            NSLog("Notification send failed: %@", str(e))


class HotkeyService:
    """
    Best-effort global hotkey using Carbon RegisterEventHotKey (if available).
    """

    def __init__(self, keycode: int, modifiers: int, on_trigger: Callable[[], None]) -> None:
        self.keycode = int(keycode)
        self.modifiers = int(modifiers)
        self.on_trigger = on_trigger
        self._hotkey_ref = None
        self._event_handler = None

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

            hotkey_id = Events.EventHotKeyID(0x4A4C4F47, 1)  # 'JLOG'
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


class ConfigFileService:
    """
    v0.5: export/import settings to a local JSON config file and apply at startup.
    Default path:
    ~/Library/Application Support/Clipboard JSON Logger/config.json
    """

    def __init__(self, app_name: str = APP_NAME) -> None:
        self.app_name = app_name

    def config_path(self) -> Path:
        base = Path("~/Library/Application Support").expanduser()
        folder = base / self.app_name
        return folder / "config.json"

    def export_config(self, config: AppConfig) -> Tuple[bool, str]:
        try:
            path = self.config_path()
            path.parent.mkdir(parents=True, exist_ok=True)

            payload = self._config_to_dict(config)
            tmp = path.with_suffix(".json.tmp")

            tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(str(tmp), str(path))
            return True, str(path)
        except Exception as e:
            return False, str(e)

    def import_config(self) -> Tuple[Optional[dict], Optional[str]]:
        try:
            path = self.config_path()
            if not path.exists():
                return None, None
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw)
            if not isinstance(data, dict):
                return None, "Config JSON is not an object/dict"
            return data, None
        except Exception as e:
            return None, str(e)

    def apply_config_dict(self, config: AppConfig, data: dict) -> Tuple[bool, str, List[str]]:
        """
        Applies known keys only. Unknown keys ignored with warnings.
        """
        warnings: List[str] = []
        try:
            known = set(self._config_to_dict(config).keys())
            for k in data.keys():
                if k not in known:
                    warnings.append(f"Ignoring unknown key: {k}")

            # Apply known keys defensively
            if "ui_language" in data and data["ui_language"] in ("af", "nl", "en"):
                config.set_ui_language(str(data["ui_language"]))

            if "default_role" in data and str(data["default_role"]) in ("user", "system", "UserAndSystem"):
                config.set_default_role(str(data["default_role"]))

            if "id_strategy" in data and str(data["id_strategy"]) in ("short_id", "uuid4"):
                config.set_id_strategy(str(data["id_strategy"]))

            if "output_mode" in data and str(data["output_mode"]) in ("loose_diary", "strict_json"):
                config.set_output_mode(str(data["output_mode"]))

            if "json_pretty" in data:
                config.set_json_pretty(bool(data["json_pretty"]))

            if "notifications_mode" in data and str(data["notifications_mode"]) in ("all", "hotkey_only", "off"):
                config.set_notifications_mode(str(data["notifications_mode"]))

            if "hotkey_enabled" in data:
                config.set_hotkey_enabled(bool(data["hotkey_enabled"]))

            if "hotkey_keycode" in data and isinstance(data["hotkey_keycode"], int):
                # Only set keycode if we also have modifiers (or keep existing)
                keycode = int(data["hotkey_keycode"])
                modifiers = config.hotkey_modifiers
                if "hotkey_modifiers" in data and isinstance(data["hotkey_modifiers"], int):
                    modifiers = int(data["hotkey_modifiers"])
                config.set_hotkey(keycode, modifiers)

            if "hotkey_modifiers" in data and isinstance(data["hotkey_modifiers"], int):
                config.set_hotkey(config.hotkey_keycode, int(data["hotkey_modifiers"]))

            # Overlay
            if "overlay_enabled" in data:
                config.set_overlay_enabled(bool(data["overlay_enabled"]))

            if "overlay_click_action" in data and str(data["overlay_click_action"]) in ("generate_blank", "open_prompt_panel"):
                config.set_overlay_click_action(str(data["overlay_click_action"]))

            if "overlay_show_all_spaces" in data:
                config.set_overlay_show_all_spaces(bool(data["overlay_show_all_spaces"]))

            if "overlay_hide_in_fullscreen" in data:
                config.set_overlay_hide_in_fullscreen(bool(data["overlay_hide_in_fullscreen"]))

            if "overlay_pos_x" in data and "overlay_pos_y" in data:
                try:
                    x = float(data["overlay_pos_x"])
                    y = float(data["overlay_pos_y"])
                    config.set_overlay_pos(x, y)
                except Exception:
                    warnings.append("Invalid overlay_pos_x/overlay_pos_y; ignored")

            if "overlay_screen_hint" in data and isinstance(data["overlay_screen_hint"], int):
                config.set_overlay_screen_hint(int(data["overlay_screen_hint"]))

            return True, "ok", warnings
        except Exception as e:
            return False, str(e), warnings

    def _config_to_dict(self, config: AppConfig) -> dict:
        x, y = config.overlay_pos
        return {
            "ui_language": config.ui_language,
            "default_role": config.default_role,
            "id_strategy": config.id_strategy,
            "output_mode": config.output_mode,
            "json_pretty": config.json_pretty,
            "notifications_mode": config.notifications_mode,
            "hotkey_enabled": config.hotkey_enabled,
            "hotkey_keycode": config.hotkey_keycode,
            "hotkey_modifiers": config.hotkey_modifiers,
            "overlay_enabled": config.overlay_enabled,
            "overlay_click_action": config.overlay_click_action,
            "overlay_show_all_spaces": config.overlay_show_all_spaces,
            "overlay_hide_in_fullscreen": config.overlay_hide_in_fullscreen,
            "overlay_pos_x": x,
            "overlay_pos_y": y,
            "overlay_screen_hint": config.overlay_screen_hint,
        }


# ----------------------------
# Helpers: hotkey display
# ----------------------------
KEYCODE_TO_CHAR = {
    0: "A",
    11: "B",
    8: "C",
    2: "D",
    14: "E",
    3: "F",
    5: "G",
    4: "H",
    34: "I",
    38: "J",
    40: "K",
    37: "L",
    46: "M",
    45: "N",
    31: "O",
    35: "P",
    12: "Q",
    15: "R",
    1: "S",
    17: "T",
    32: "U",
    9: "V",
    13: "W",
    7: "X",
    16: "Y",
    6: "Z",
    18: "1",
    19: "2",
    20: "3",
    21: "4",
    23: "5",
    22: "6",
    26: "7",
    28: "8",
    25: "9",
    29: "0",
}


def format_hotkey_display(keycode: int, modifiers: int) -> str:
    parts = []
    if CARBON_AVAILABLE:
        if modifiers & HIToolbox.controlKey:
            parts.append("⌃")
        if modifiers & HIToolbox.optionKey:
            parts.append("⌥")
        if modifiers & HIToolbox.shiftKey:
            parts.append("⇧")
        if modifiers & HIToolbox.cmdKey:
            parts.append("⌘")
    key = KEYCODE_TO_CHAR.get(int(keycode), f"keycode:{int(keycode)}")
    return "".join(parts) + key


# ----------------------------
# UI: Prompt panel
# ----------------------------
class PromptPanelController(NSObject):
    """
    Reusable multiline prompt panel: NSPanel + NSTextView.
    Calls back with (role_selection, prompt) or (None, None) if cancelled.
    """

    def initWithApp_callback_(self, app, callback):
        self = objc.super(PromptPanelController, self).init()
        if self is None:
            return None

        self._app = app
        self._callback = callback

        self.panel = None
        self.lbl_role = None
        self.role_popup = None
        self.text_view = None
        self.btn_copy = None
        self.btn_cancel = None

        self._build_ui()
        self.refresh_texts()
        return self

    def _build_ui(self):
        style = (
            NSWindowStyleMaskTitled
            | NSWindowStyleMaskClosable
            | NSWindowStyleMaskResizable
            | NSWindowStyleMaskUtilityWindow
        )
        self.panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(200, 200, 520, 360), style, NSBackingStoreBuffered, False
        )

        content = self.panel.contentView()

        # Role label + popup
        self.lbl_role = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 320, 60, 22))
        self.lbl_role.setEditable_(False)
        self.lbl_role.setBordered_(False)
        self.lbl_role.setDrawsBackground_(False)
        content.addSubview_(self.lbl_role)

        self.role_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(80, 316, 180, 26))
        content.addSubview_(self.role_popup)

        # Scroll + text view
        scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(20, 70, 480, 236))
        scroll.setHasVerticalScroller_(True)
        scroll.setHasHorizontalScroller_(False)

        self.text_view = NSTextView.alloc().initWithFrame_(NSMakeRect(0, 0, 480, 236))
        self.text_view.setFont_(NSFont.systemFontOfSize_(13))
        self.text_view.setString_("")
        scroll.setDocumentView_(self.text_view)
        content.addSubview_(scroll)

        # Buttons
        self.btn_copy = NSButton.alloc().initWithFrame_(NSMakeRect(320, 20, 180, 32))
        self.btn_copy.setButtonType_(NSMomentaryPushInButton)
        self.btn_copy.setBezelStyle_(NSBezelStyleRounded)
        self.btn_copy.setTarget_(self)
        self.btn_copy.setAction_("onCopy:")
        content.addSubview_(self.btn_copy)

        self.btn_cancel = NSButton.alloc().initWithFrame_(NSMakeRect(220, 20, 90, 32))
        self.btn_cancel.setButtonType_(NSMomentaryPushInButton)
        self.btn_cancel.setBezelStyle_(NSBezelStyleRounded)
        self.btn_cancel.setTarget_(self)
        self.btn_cancel.setAction_("onCancel:")
        content.addSubview_(self.btn_cancel)

    def refresh_texts(self):
        t = self._app.t
        self.panel.setTitle_(t("panel.prompt.title"))
        self.lbl_role.setStringValue_(t("panel.prompt.role"))
        self.btn_copy.setTitle_(t("panel.prompt.copy"))
        self.btn_cancel.setTitle_(t("panel.prompt.cancel"))

        # Rebuild role items (localized display name may differ per language)
        current = self._app.config.default_role
        self.role_popup.removeAllItems()
        self.role_popup.addItemWithTitle_(t("menu.role.user"))
        self.role_popup.addItemWithTitle_(t("menu.role.system"))
        self.role_popup.addItemWithTitle_(t("menu.role.user_and_system"))
        self._select_role(current)

    def _select_role(self, role: str):
        t = self._app.t
        if role == "system":
            self.role_popup.selectItemWithTitle_(t("menu.role.system"))
        elif role == "UserAndSystem":
            self.role_popup.selectItemWithTitle_(t("menu.role.user_and_system"))
        else:
            self.role_popup.selectItemWithTitle_(t("menu.role.user"))

    def show(self):
        # refresh selection from current defaults
        self._select_role(self._app.config.default_role)
        self.panel.makeKeyAndOrderFront_(None)
        self.panel.makeFirstResponder_(self.text_view)

    def _role_selection_value(self) -> str:
        # Map display title back to internal value
        title = str(self.role_popup.titleOfSelectedItem())
        t = self._app.t
        if title == t("menu.role.system"):
            return "system"
        if title == t("menu.role.user_and_system"):
            return "UserAndSystem"
        return "user"

    def onCopy_(self, sender):
        try:
            role_sel = self._role_selection_value()
            prompt = str(self.text_view.string() or "")
            self.panel.orderOut_(None)
            if self._callback:
                self._callback(role_sel, prompt)
        except Exception as e:
            NSLog("Prompt panel copy error: %@", str(e))

    def onCancel_(self, sender):
        try:
            self.panel.orderOut_(None)
            if self._callback:
                self._callback(None, None)
        except Exception as e:
            NSLog("Prompt panel cancel error: %@", str(e))


# ----------------------------
# UI: Settings panel + hotkey capture
# ----------------------------
class HotkeyCaptureView(NSView):
    """
    A focusable view that captures the next keyDown event as a hotkey combination.
    """

    def initWithCallback_(self, callback):
        self = objc.super(HotkeyCaptureView, self).init()
        if self is None:
            return None
        self._callback = callback
        self._capturing = False
        return self

    def acceptsFirstResponder(self):
        return True

    def setCapturing_(self, capturing: bool):
        self._capturing = bool(capturing)

    def keyDown_(self, event):
        if not self._capturing:
            return

        keycode = int(event.keyCode())
        mods = int(event.modifierFlags())

        # Convert Cocoa modifierFlags to Carbon-style mask subset
        carbon_mods = 0
        if CARBON_AVAILABLE:
            if mods & (1 << 18):
                carbon_mods |= HIToolbox.controlKey
            if mods & (1 << 19):
                carbon_mods |= HIToolbox.optionKey
            if mods & (1 << 17):
                carbon_mods |= HIToolbox.shiftKey
            if mods & (1 << 20):
                carbon_mods |= HIToolbox.cmdKey

        if self._callback:
            self._callback(keycode, carbon_mods)


class SettingsPanelController(NSObject):
    """
    Settings panel for:
    - Hotkey enabled
    - Hotkey capture + apply
    - Notifications mode
    - JSON pretty toggle (strict mode)
    - Language selection (runtime)
    - Config export/import
    """

    def initWithApp_applyCallback_(self, app, apply_callback):
        self = objc.super(SettingsPanelController, self).init()
        if self is None:
            return None

        self.app = app
        self.config = app.config
        self.apply_callback = apply_callback

        self.panel = None
        self.chk_hotkey = None
        self.lbl_hotkey = None
        self.btn_capture = None
        self.btn_reset = None
        self.mode_popup = None
        self.chk_json_pretty = None
        self.lbl_status = None

        self.lbl_lang = None
        self.lang_popup = None

        self.btn_export = None
        self.btn_import = None

        self.capture_view = None
        self._capture_active = False

        self._build_ui()
        self.refresh_texts()
        self._refresh_ui_state()
        return self

    def _build_ui(self):
        style = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskUtilityWindow
        self.panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(260, 260, 560, 300), style, NSBackingStoreBuffered, False
        )

        content = self.panel.contentView()

        # Hotkey enabled switch
        self.chk_hotkey = NSButton.alloc().initWithFrame_(NSMakeRect(20, 250, 240, 24))
        self.chk_hotkey.setButtonType_(NSSwitchButton)
        self.chk_hotkey.setTarget_(self)
        self.chk_hotkey.setAction_("onToggleHotkeyEnabled:")
        content.addSubview_(self.chk_hotkey)

        # Current hotkey label
        self.lbl_current_hotkey = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 220, 120, 22))
        self.lbl_current_hotkey.setEditable_(False)
        self.lbl_current_hotkey.setBordered_(False)
        self.lbl_current_hotkey.setDrawsBackground_(False)
        content.addSubview_(self.lbl_current_hotkey)

        self.lbl_hotkey = NSTextField.alloc().initWithFrame_(NSMakeRect(140, 216, 400, 24))
        self.lbl_hotkey.setEditable_(False)
        self.lbl_hotkey.setBordered_(True)
        self.lbl_hotkey.setDrawsBackground_(True)
        content.addSubview_(self.lbl_hotkey)

        # Capture/reset buttons
        self.btn_capture = NSButton.alloc().initWithFrame_(NSMakeRect(20, 180, 160, 30))
        self.btn_capture.setBezelStyle_(NSBezelStyleRounded)
        self.btn_capture.setTarget_(self)
        self.btn_capture.setAction_("onCaptureHotkey:")
        content.addSubview_(self.btn_capture)

        self.btn_reset = NSButton.alloc().initWithFrame_(NSMakeRect(190, 180, 120, 30))
        self.btn_reset.setBezelStyle_(NSBezelStyleRounded)
        self.btn_reset.setTarget_(self)
        self.btn_reset.setAction_("onResetHotkey:")
        content.addSubview_(self.btn_reset)

        # Notifications mode
        self.lbl_notif = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 142, 120, 22))
        self.lbl_notif.setEditable_(False)
        self.lbl_notif.setBordered_(False)
        self.lbl_notif.setDrawsBackground_(False)
        content.addSubview_(self.lbl_notif)

        self.mode_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(140, 138, 200, 26))
        self.mode_popup.setTarget_(self)
        self.mode_popup.setAction_("onNotificationsModeChanged:")
        content.addSubview_(self.mode_popup)

        # JSON pretty (strict mode)
        self.chk_json_pretty = NSButton.alloc().initWithFrame_(NSMakeRect(20, 106, 260, 24))
        self.chk_json_pretty.setButtonType_(NSSwitchButton)
        self.chk_json_pretty.setTarget_(self)
        self.chk_json_pretty.setAction_("onToggleJsonPretty:")
        content.addSubview_(self.chk_json_pretty)

        # Language
        self.lbl_lang = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 72, 120, 22))
        self.lbl_lang.setEditable_(False)
        self.lbl_lang.setBordered_(False)
        self.lbl_lang.setDrawsBackground_(False)
        content.addSubview_(self.lbl_lang)

        self.lang_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(140, 68, 200, 26))
        self.lang_popup.setTarget_(self)
        self.lang_popup.setAction_("onLanguageChanged:")
        content.addSubview_(self.lang_popup)

        # Config export/import
        self.btn_export = NSButton.alloc().initWithFrame_(NSMakeRect(360, 68, 180, 30))
        self.btn_export.setBezelStyle_(NSBezelStyleRounded)
        self.btn_export.setTarget_(self)
        self.btn_export.setAction_("onExportConfig:")
        content.addSubview_(self.btn_export)

        self.btn_import = NSButton.alloc().initWithFrame_(NSMakeRect(360, 34, 180, 30))
        self.btn_import.setBezelStyle_(NSBezelStyleRounded)
        self.btn_import.setTarget_(self)
        self.btn_import.setAction_("onImportConfig:")
        content.addSubview_(self.btn_import)

        # Status line
        self.lbl_status = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 16, 520, 22))
        self.lbl_status.setEditable_(False)
        self.lbl_status.setBordered_(False)
        self.lbl_status.setDrawsBackground_(False)
        self.lbl_status.setStringValue_("")
        content.addSubview_(self.lbl_status)

        # Capture view (invisible but focusable)
        self.capture_view = HotkeyCaptureView.alloc().initWithCallback_(lambda kc, m: self.__onCapturedHotkey(kc, m))
        self.capture_view.setFrame_(NSMakeRect(0, 0, 1, 1))
        content.addSubview_(self.capture_view)

    def show(self):
        self._refresh_ui_state()
        self.panel.makeKeyAndOrderFront_(None)

    def refresh_texts(self):
        t = self.app.t
        self.panel.setTitle_(t("panel.settings.title"))

        self.chk_hotkey.setTitle_(t("panel.settings.hotkey_enabled"))
        self.lbl_current_hotkey.setStringValue_(t("panel.settings.current_hotkey"))
        self.btn_capture.setTitle_(t("panel.settings.capture"))
        self.btn_reset.setTitle_(t("panel.settings.reset"))
        self.lbl_notif.setStringValue_(t("panel.settings.notifications"))
        self.chk_json_pretty.setTitle_(t("panel.settings.pretty"))
        self.lbl_lang.setStringValue_(t("panel.settings.language"))
        self.btn_export.setTitle_(t("panel.settings.export"))
        self.btn_import.setTitle_(t("panel.settings.import"))

        # Rebuild notifications popup titles (localized)
        current_mode = self.config.notifications_mode
        self.mode_popup.removeAllItems()
        self.mode_popup.addItemWithTitle_(t("menu.notif.all"))
        self.mode_popup.addItemWithTitle_(t("menu.notif.hotkey"))
        self.mode_popup.addItemWithTitle_(t("menu.notif.off"))
        self._select_notifications(current_mode)

        # Rebuild language popup (localized display)
        self._rebuild_language_popup()

        # Preserve status text as-is (could be in previous language); optional to clear:
        # self.lbl_status.setStringValue_("")

    def _rebuild_language_popup(self):
        t = self.app.t
        # Labels should be in current language too.
        options = [
            ("af", "Afrikaans" if self.config.ui_language == "af" else "Afrikaans"),
            ("nl", "Nederlands"),
            ("en", "English"),
        ]
        # Localize display names lightly
        # (We keep them recognizable; you can fully localize later.)
        self.lang_popup.removeAllItems()
        for code, label in options:
            self.lang_popup.addItemWithTitle_(label)
        # Select current
        idx = {"af": 0, "nl": 1, "en": 2}.get(self.config.ui_language, 0)
        self.lang_popup.selectItemAtIndex_(idx)

    def _refresh_ui_state(self):
        self.chk_hotkey.setState_(NSControlStateValueOn if self.config.hotkey_enabled else NSControlStateValueOff)
        self.lbl_hotkey.setStringValue_(format_hotkey_display(self.config.hotkey_keycode, self.config.hotkey_modifiers))
        self.chk_json_pretty.setState_(NSControlStateValueOn if self.config.json_pretty else NSControlStateValueOff)
        self._select_notifications(self.config.notifications_mode)
        # language selection reflects config
        idx = {"af": 0, "nl": 1, "en": 2}.get(self.config.ui_language, 0)
        try:
            self.lang_popup.selectItemAtIndex_(idx)
        except Exception:
            pass

    def _select_notifications(self, mode: str):
        t = self.app.t
        if mode == "all":
            self.mode_popup.selectItemWithTitle_(t("menu.notif.all"))
        elif mode == "off":
            self.mode_popup.selectItemWithTitle_(t("menu.notif.off"))
        else:
            self.mode_popup.selectItemWithTitle_(t("menu.notif.hotkey"))

    def _set_status(self, msg: str):
        self.lbl_status.setStringValue_(msg)

    # ---- handlers ----
    def onToggleHotkeyEnabled_(self, sender):
        enabled = sender.state() == NSControlStateValueOn
        self.config.set_hotkey_enabled(enabled)
        self._refresh_ui_state()
        self.apply_callback("hotkey")

    def onNotificationsModeChanged_(self, sender):
        title = str(self.mode_popup.titleOfSelectedItem())
        t = self.app.t
        if title == t("menu.notif.all"):
            mode = "all"
        elif title == t("menu.notif.off"):
            mode = "off"
        else:
            mode = "hotkey_only"
        self.config.set_notifications_mode(mode)
        self._refresh_ui_state()
        self.apply_callback("notifications")

    def onToggleJsonPretty_(self, sender):
        pretty = sender.state() == NSControlStateValueOn
        self.config.set_json_pretty(pretty)
        self._refresh_ui_state()
        self.apply_callback("json")

    def onResetHotkey_(self, sender):
        t = self.app.t
        if not CARBON_AVAILABLE:
            self._set_status(t("status.hotkey_missing"))
            return

        keycode = HIToolbox.kVK_ANSI_J
        modifiers = HIToolbox.controlKey | HIToolbox.optionKey | HIToolbox.cmdKey
        self._apply_hotkey_candidate(keycode, modifiers, is_reset=True)

    def onCaptureHotkey_(self, sender):
        t = self.app.t
        if not CARBON_AVAILABLE:
            self._set_status(t("status.hotkey_missing"))
            return

        self._capture_active = True
        self.capture_view.setCapturing_(True)
        self._set_status(t("status.press_combo"))
        self.panel.makeFirstResponder_(self.capture_view)

    def onLanguageChanged_(self, sender):
        # Map popup index to code
        idx = int(self.lang_popup.indexOfSelectedItem())
        lang = {0: "af", 1: "nl", 2: "en"}.get(idx, "af")
        self.config.set_ui_language(lang)

        # Refresh all UI texts without restart
        self.app.refresh_all_ui_texts()
        self._set_status("")  # clear

    def onExportConfig_(self, sender):
        t = self.app.t
        ok, msg = self.app.config_file.export_config(self.config)
        if ok:
            self._set_status(t("status.export_ok") % msg)
        else:
            self._set_status(t("status.export_fail") % msg)

    def onImportConfig_(self, sender):
        t = self.app.t
        data, err = self.app.config_file.import_config()
        if err is not None:
            self._set_status(t("status.import_fail") % err)
            return
        if data is None:
            self._set_status(t("status.import_fail") % "config.json not found")
            return

        ok, msg, warnings = self.app.config_file.apply_config_dict(self.config, data)
        if not ok:
            self._set_status(t("status.import_fail") % msg)
            return

        # Apply immediately
        self.app.on_config_applied(warnings=warnings)
        self._refresh_ui_state()
        self._set_status(t("status.import_ok"))

    # ---- capture callback ----
    def __onCapturedHotkey(self, keycode: int, modifiers: int):
        if not self._capture_active:
            return

        self._capture_active = False
        self.capture_view.setCapturing_(False)

        t = self.app.t
        if modifiers == 0:
            self._set_status(t("status.rejected_modifier"))
            self.panel.makeFirstResponder_(None)
            return

        self._apply_hotkey_candidate(keycode, modifiers, is_reset=False)

    def _apply_hotkey_candidate(self, keycode: int, modifiers: int, is_reset: bool):
        t = self.app.t
        ok, err = self.apply_callback("hotkey_candidate", (keycode, modifiers))
        if ok:
            self.config.set_hotkey(keycode, modifiers)
            self._refresh_ui_state()
            self._set_status(t("status.hotkey_reset_applied") if is_reset else t("status.hotkey_applied"))
        else:
            self._set_status(t("status.hotkey_failed") % (err or "conflict/unavailable"))
            self._refresh_ui_state()


# ----------------------------
# UI: Overlay Bubble (Floating Button)
# ----------------------------
class OverlayBubbleView(NSView):
    """
    Simple draggable bubble view.
    Left click -> primary action
    Right click -> context menu
    """

    def initWithController_(self, controller):
        self = objc.super(OverlayBubbleView, self).init()
        if self is None:
            return None
        self.controller = controller
        self._drag_start_window_origin = None
        self._drag_start_mouse_screen = None
        return self

    def isFlipped(self):
        return True

    def drawRect_(self, rect):
        # Transparent background + rounded bubble + label
        bounds = self.bounds()
        r = min(bounds.size.width, bounds.size.height)
        bubble_rect = NSMakeRect(0, 0, r, r)

        NSColor.clearColor().set()
        NSBezierPath.fillRect_(bounds)

        # bubble fill
        NSColor.colorWithCalibratedWhite_alpha_(0.12, 0.92).set()
        path = NSBezierPath.bezierPathWithOvalInRect_(bubble_rect)
        path.fill()

        # outline
        NSColor.colorWithCalibratedWhite_alpha_(0.2, 0.9).set()
        path.setLineWidth_(1.0)
        path.stroke()

        # label "{ }"
        label = "{ }"
        attrs = {
            # use system font; keep readable
        }
        # Minimal: use NSTextField? We'll just rely on drawAtPoint_ via NSString
        try:
            from Foundation import NSString
            from AppKit import NSFontAttributeName, NSForegroundColorAttributeName
            attrs = {
                NSFontAttributeName: NSFont.systemFontOfSize_(13),
                NSForegroundColorAttributeName: NSColor.colorWithCalibratedWhite_alpha_(0.05, 1.0),
            }
            s = NSString.stringWithString_(label)
            size = s.sizeWithAttributes_(attrs)
            x = (bounds.size.width - size.width) / 2.0
            y = (bounds.size.height - size.height) / 2.0 + 1.0
            s.drawAtPoint_withAttributes_((x, y), attrs)
        except Exception:
            pass

    def mouseDown_(self, event):
        # Start drag
        win = self.window()
        if win is None:
            return
        self._drag_start_window_origin = win.frame().origin
        loc = NSEvent.mouseLocation()  # screen coords
        self._drag_start_mouse_screen = (loc.x, loc.y)

    def mouseDragged_(self, event):
        win = self.window()
        if win is None or self._drag_start_window_origin is None or self._drag_start_mouse_screen is None:
            return
        loc = NSEvent.mouseLocation()
        dx = loc.x - self._drag_start_mouse_screen[0]
        dy = loc.y - self._drag_start_mouse_screen[1]
        new_x = self._drag_start_window_origin.x + dx
        new_y = self._drag_start_window_origin.y + dy
        win.setFrameOrigin_((new_x, new_y))

    def mouseUp_(self, event):
        # Persist position (and treat as click if minimal movement)
        self.controller.persist_position()

        # Detect click vs drag: if movement small, treat as click
        # We'll approximate by checking if current origin differs minimally
        win = self.window()
        if win is None or self._drag_start_window_origin is None:
            return
        cur = win.frame().origin
        dist = abs(cur.x - self._drag_start_window_origin.x) + abs(cur.y - self._drag_start_window_origin.y)
        if dist < 2.5:
            self.controller.on_primary_click()

    def rightMouseDown_(self, event):
        self.controller.show_context_menu(event, self)


class OverlayBubbleController(NSObject):
    """
    Manages the floating bubble window and integrates with AppController.
    """

    def initWithApp_(self, app):
        self = objc.super(OverlayBubbleController, self).init()
        if self is None:
            return None
        self.app = app
        self.window = None
        self.view = None
        return self

    def is_visible(self) -> bool:
        return self.window is not None and self.window.isVisible()

    def show(self):
        if self.window is None:
            self._create_window()
        self.apply_behavior()
        self.restore_position()
        self.window.makeKeyAndOrderFront_(None)

    def hide(self):
        if self.window is not None:
            self.window.orderOut_(None)

    def _create_window(self):
        size = 56
        rect = NSMakeRect(200, 200, size, size)
        self.window = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            rect,
            NSWindowStyleMaskBorderless,
            NSBackingStoreBuffered,
            False,
        )
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(NSColor.clearColor())
        self.window.setHasShadow_(True)
        try:
            self.window.setLevel_(NSStatusWindowLevel)
        except Exception:
            self.window.setLevel_(NSFloatingWindowLevel)

        self.view = OverlayBubbleView.alloc().initWithController_(self)
        self.view.setFrame_(NSMakeRect(0, 0, size, size))
        self.window.setContentView_(self.view)

    def apply_behavior(self):
        if self.window is None:
            return

        # Spaces/fullscreen behavior (best-effort)
        behavior = 0

        if self.app.config.overlay_show_all_spaces:
            behavior |= NSWindowCollectionBehaviorCanJoinAllSpaces
        else:
            behavior |= NSWindowCollectionBehaviorMoveToActiveSpace

        # Hide in fullscreen: if false, allow as fullscreen auxiliary
        if not self.app.config.overlay_hide_in_fullscreen:
            behavior |= NSWindowCollectionBehaviorFullScreenAuxiliary

        try:
            self.window.setCollectionBehavior_(behavior)
        except Exception:
            pass

    def _screen_index_for_point(self, x: float, y: float) -> int:
        screens = NSScreen.screens()
        for idx, s in enumerate(screens):
            f = s.frame()
            if (x >= f.origin.x and x <= f.origin.x + f.size.width and y >= f.origin.y and y <= f.origin.y + f.size.height):
                return idx
        return -1

    def persist_position(self):
        if self.window is None:
            return
        origin = self.window.frame().origin
        self.app.config.set_overlay_pos(origin.x, origin.y)
        idx = self._screen_index_for_point(origin.x, origin.y)
        self.app.config.set_overlay_screen_hint(idx)

    def _clamp_to_visible_frame(self, x: float, y: float, screen: NSScreen) -> Tuple[float, float]:
        vf = screen.visibleFrame()
        w = self.window.frame().size.width if self.window is not None else 56
        h = self.window.frame().size.height if self.window is not None else 56

        # Clamp so window stays visible
        cx = max(vf.origin.x, min(x, vf.origin.x + vf.size.width - w))
        cy = max(vf.origin.y, min(y, vf.origin.y + vf.size.height - h))
        return cx, cy

    def restore_position(self):
        if self.window is None:
            return

        x, y = self.app.config.overlay_pos
        screens = NSScreen.screens()

        # If no saved position, default top-right-ish of main screen
        if abs(x) < 1e-6 and abs(y) < 1e-6:
            main = NSScreen.mainScreen() or (screens[0] if screens else None)
            if main is None:
                return
            vf = main.visibleFrame()
            x = vf.origin.x + vf.size.width - 76
            y = vf.origin.y + vf.size.height - 96

        hint = self.app.config.overlay_screen_hint
        screen = None
        if hint is not None and hint >= 0 and hint < len(screens):
            screen = screens[hint]
        if screen is None:
            screen = NSScreen.mainScreen() or (screens[0] if screens else None)
        if screen is None:
            return

        x, y = self._clamp_to_visible_frame(x, y, screen)
        self.window.setFrameOrigin_((x, y))

    def on_primary_click(self):
        # Dispatch per click action
        action = self.app.config.overlay_click_action
        if action == "open_prompt_panel":
            self.app.open_prompt_panel()
        else:
            self.app.generate_and_copy(source="overlay")

    def show_context_menu(self, event, view):
        menu = self.app.build_overlay_context_menu()
        try:
            NSMenu.popUpContextMenu_withEvent_forView_(menu, event, view)
        except Exception:
            # fallback: show at mouse location
            menu.popUpMenuPositioningItem_atLocation_inView_(None, (0, 0), view)


# ----------------------------
# App Controller
# ----------------------------
class AppController(NSObject):
    def init(self):
        self = objc.super(AppController, self).init()
        if self is None:
            return None

        self.config = AppConfig()
        self.config_file = ConfigFileService(APP_NAME)

        self.id_service = IdService(strategy=self.config.id_strategy)
        self.dt_service = DateTimeService()
        self.formatter = EntryFormatter()
        self.clipboard = ClipboardService()
        self.notifier = NotificationService()

        self.status_item = None
        self.menu = None

        self.hotkey = None
        self.prompt_panel = None
        self.settings_panel = None

        self.overlay = None  # OverlayBubbleController

        # menu item references (for runtime i18n refresh)
        self.mi_gen = None
        self.mi_prompt = None

        self.mi_role_user = None
        self.mi_role_system = None
        self.mi_role_user_and_system = None
        self.role_root = None

        self.mi_mode_loose = None
        self.mi_mode_strict = None
        self.mode_root = None

        self.mi_notif_all = None
        self.mi_notif_hotkey = None
        self.mi_notif_off = None
        self.notif_root = None

        # overlay menu references
        self.overlay_root = None
        self.mi_overlay_enabled = None
        self.overlay_click_root = None
        self.mi_overlay_click_blank = None
        self.mi_overlay_click_prompt = None
        self.mi_overlay_all_spaces = None
        self.mi_overlay_hide_fullscreen = None

        self.mi_settings = None
        self.mi_hotkey = None
        self.mi_quit = None

        return self

    # -------- i18n --------
    def get_string(self, key: str) -> str:
        lang = self.config.ui_language
        table = STRINGS.get(lang) or STRINGS["af"]
        return table.get(key) or STRINGS["af"].get(key) or key

    def refresh_all_ui_texts(self):
        # Refresh menu texts
        self._refresh_menu_texts()

        # Refresh open panels
        if self.prompt_panel is not None:
            try:
                self.prompt_panel.refresh_texts()
            except Exception:
                pass
        if self.settings_panel is not None:
            try:
                self.settings_panel.refresh_texts()
            except Exception:
                pass

        # Overlay context menu is built on-demand (localized via t()),
        # but overlay behavior toggles may need refresh states:
        self._refresh_menu_states()

    # -------- lifecycle --------
    def applicationDidFinishLaunching_(self, notification):
        NSLog("%@ v%@ (%@) launching", APP_NAME, APP_VERSION, APP_BUILD_DATE)

        # Apply config from JSON at startup (best-effort)
        self._apply_config_on_startup()

        self._setup_menu_bar()
        self.refresh_all_ui_texts()

        # Best-effort hotkey
        if self.config.hotkey_enabled:
            self._start_hotkey()

        # Notifications: request permission if enabled
        if self.config.notifications_mode != "off":
            self.notifier.ensure_permission()

        # Overlay: show if enabled
        self._apply_overlay_visibility()

    def applicationWillTerminate_(self, notification):
        try:
            if self.hotkey is not None:
                self.hotkey.stop()
                self.hotkey = None
        except Exception:
            pass

    def _apply_config_on_startup(self):
        data, err = self.config_file.import_config()
        if err is not None or data is None:
            return
        ok, msg, warnings = self.config_file.apply_config_dict(self.config, data)
        if not ok:
            NSLog("Config apply failed: %@", str(msg))
            return
        if warnings:
            for w in warnings:
                NSLog("Config warning: %@", w)

    def on_config_applied(self, warnings: Optional[List[str]] = None):
        # Called after manual import; re-apply runtime behaviors
        self.refresh_all_ui_texts()

        # Hotkey
        if self.config.hotkey_enabled:
            self._start_hotkey()
        else:
            self._stop_hotkey()

        # Notifications
        if self.config.notifications_mode != "off":
            self.notifier.ensure_permission()

        # Overlay
        self._apply_overlay_visibility()
        self._apply_overlay_behavior()

    # ---------- UI setup ----------
    def _setup_menu_bar(self):
        self.status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
        self.status_item.setTitle_("{ }")

        self.menu = NSMenu.alloc().init()

        # Generate Entry
        self.mi_gen = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.generate"), "onGenerateEntry:", "")
        self.mi_gen.setTarget_(self)
        self.menu.addItem_(self.mi_gen)

        # Generate with Prompt...
        self.mi_prompt = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.generate_prompt"), "onGenerateWithPrompt:", "")
        self.mi_prompt.setTarget_(self)
        self.menu.addItem_(self.mi_prompt)

        self.menu.addItem_(NSMenuItem.separatorItem())

        # Role submenu
        role_menu = NSMenu.alloc().init()
        self.mi_role_user = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.role.user"), "onSetRoleUser:", "")
        self.mi_role_user.setTarget_(self)
        role_menu.addItem_(self.mi_role_user)

        self.mi_role_system = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.role.system"), "onSetRoleSystem:", "")
        self.mi_role_system.setTarget_(self)
        role_menu.addItem_(self.mi_role_system)

        self.mi_role_user_and_system = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.role.user_and_system"), "onSetRoleUserAndSystem:", "")
        self.mi_role_user_and_system.setTarget_(self)
        role_menu.addItem_(self.mi_role_user_and_system)

        self.role_root = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.role"), None, "")
        self.role_root.setSubmenu_(role_menu)
        self.menu.addItem_(self.role_root)

        # Output mode submenu
        mode_menu = NSMenu.alloc().init()
        self.mi_mode_loose = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.mode.a"), "onSetModeLoose:", "")
        self.mi_mode_loose.setTarget_(self)
        mode_menu.addItem_(self.mi_mode_loose)

        self.mi_mode_strict = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.mode.b"), "onSetModeStrict:", "")
        self.mi_mode_strict.setTarget_(self)
        mode_menu.addItem_(self.mi_mode_strict)

        self.mode_root = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.output_mode"), None, "")
        self.mode_root.setSubmenu_(mode_menu)
        self.menu.addItem_(self.mode_root)

        # Notifications submenu
        notif_menu = NSMenu.alloc().init()
        self.mi_notif_all = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.notif.all"), "onSetNotifAll:", "")
        self.mi_notif_all.setTarget_(self)
        notif_menu.addItem_(self.mi_notif_all)

        self.mi_notif_hotkey = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.notif.hotkey"), "onSetNotifHotkeyOnly:", "")
        self.mi_notif_hotkey.setTarget_(self)
        notif_menu.addItem_(self.mi_notif_hotkey)

        self.mi_notif_off = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.notif.off"), "onSetNotifOff:", "")
        self.mi_notif_off.setTarget_(self)
        notif_menu.addItem_(self.mi_notif_off)

        self.notif_root = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.notifications"), None, "")
        self.notif_root.setSubmenu_(notif_menu)
        self.menu.addItem_(self.notif_root)

        # Overlay submenu
        overlay_menu = NSMenu.alloc().init()
        self.mi_overlay_enabled = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.overlay.enabled"), "onToggleOverlayEnabled:", "")
        self.mi_overlay_enabled.setTarget_(self)
        overlay_menu.addItem_(self.mi_overlay_enabled)

        # Click action submenu
        click_menu = NSMenu.alloc().init()
        self.mi_overlay_click_blank = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.overlay.click_blank"), "onSetOverlayClickBlank:", "")
        self.mi_overlay_click_blank.setTarget_(self)
        click_menu.addItem_(self.mi_overlay_click_blank)

        self.mi_overlay_click_prompt = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.overlay.click_prompt"), "onSetOverlayClickPrompt:", "")
        self.mi_overlay_click_prompt.setTarget_(self)
        click_menu.addItem_(self.mi_overlay_click_prompt)

        self.overlay_click_root = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.overlay.click_action"), None, "")
        self.overlay_click_root.setSubmenu_(click_menu)
        overlay_menu.addItem_(self.overlay_click_root)

        self.mi_overlay_all_spaces = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.overlay.all_spaces"), "onToggleOverlayAllSpaces:", "")
        self.mi_overlay_all_spaces.setTarget_(self)
        overlay_menu.addItem_(self.mi_overlay_all_spaces)

        self.mi_overlay_hide_fullscreen = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.overlay.hide_fullscreen"), "onToggleOverlayHideFullscreen:", "")
        self.mi_overlay_hide_fullscreen.setTarget_(self)
        overlay_menu.addItem_(self.mi_overlay_hide_fullscreen)

        self.overlay_root = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.overlay"), None, "")
        self.overlay_root.setSubmenu_(overlay_menu)
        self.menu.addItem_(self.overlay_root)

        self.menu.addItem_(NSMenuItem.separatorItem())

        # Settings…
        self.mi_settings = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.settings"), "onOpenSettings:", "")
        self.mi_settings.setTarget_(self)
        self.menu.addItem_(self.mi_settings)

        # Hotkey quick toggle
        self.mi_hotkey = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.hotkey_enabled"), "onToggleHotkey:", "")
        self.mi_hotkey.setTarget_(self)
        self.menu.addItem_(self.mi_hotkey)

        self.menu.addItem_(NSMenuItem.separatorItem())

        # Quit
        self.mi_quit = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.quit"), "terminate:", "q")
        self.menu.addItem_(self.mi_quit)

        self.status_item.setMenu_(self.menu)
        self._refresh_menu_states()

    def _refresh_menu_texts(self):
        # Update existing menu item titles in-place (runtime language switching)
        if self.menu is None:
            return

        if self.mi_gen is not None:
            self.mi_gen.setTitle_(self.get_string("menu.generate"))
        if self.mi_prompt is not None:
            self.mi_prompt.setTitle_(self.get_string("menu.generate_prompt"))

        if self.role_root is not None:
            self.role_root.setTitle_(self.get_string("menu.role"))
        if self.mi_role_user is not None:
            self.mi_role_user.setTitle_(self.get_string("menu.role.user"))
        if self.mi_role_system is not None:
            self.mi_role_system.setTitle_(self.get_string("menu.role.system"))
        if self.mi_role_user_and_system is not None:
            self.mi_role_user_and_system.setTitle_(self.get_string("menu.role.user_and_system"))

        if self.mode_root is not None:
            self.mode_root.setTitle_(self.get_string("menu.output_mode"))
        if self.mi_mode_loose is not None:
            self.mi_mode_loose.setTitle_(self.get_string("menu.mode.a"))
        if self.mi_mode_strict is not None:
            self.mi_mode_strict.setTitle_(self.get_string("menu.mode.b"))

        if self.notif_root is not None:
            self.notif_root.setTitle_(self.get_string("menu.notifications"))
        if self.mi_notif_all is not None:
            self.mi_notif_all.setTitle_(self.get_string("menu.notif.all"))
        if self.mi_notif_hotkey is not None:
            self.mi_notif_hotkey.setTitle_(self.get_string("menu.notif.hotkey"))
        if self.mi_notif_off is not None:
            self.mi_notif_off.setTitle_(self.get_string("menu.notif.off"))

        if self.overlay_root is not None:
            self.overlay_root.setTitle_(self.get_string("menu.overlay"))
        if self.mi_overlay_enabled is not None:
            self.mi_overlay_enabled.setTitle_(self.get_string("menu.overlay.enabled"))
        if self.overlay_click_root is not None:
            self.overlay_click_root.setTitle_(self.get_string("menu.overlay.click_action"))
        if self.mi_overlay_click_blank is not None:
            self.mi_overlay_click_blank.setTitle_(self.get_string("menu.overlay.click_blank"))
        if self.mi_overlay_click_prompt is not None:
            self.mi_overlay_click_prompt.setTitle_(self.get_string("menu.overlay.click_prompt"))
        if self.mi_overlay_all_spaces is not None:
            self.mi_overlay_all_spaces.setTitle_(self.get_string("menu.overlay.all_spaces"))
        if self.mi_overlay_hide_fullscreen is not None:
            self.mi_overlay_hide_fullscreen.setTitle_(self.get_string("menu.overlay.hide_fullscreen"))

        if self.mi_settings is not None:
            self.mi_settings.setTitle_(self.get_string("menu.settings"))
        if self.mi_hotkey is not None:
            self.mi_hotkey.setTitle_(self.get_string("menu.hotkey_enabled"))
        if self.mi_quit is not None:
            self.mi_quit.setTitle_(self.get_string("menu.quit"))

    def _refresh_menu_states(self):
        role = self.config.default_role
        self.mi_role_user.setState_(NSControlStateValueOn if role == "user" else NSControlStateValueOff)
        self.mi_role_system.setState_(NSControlStateValueOn if role == "system" else NSControlStateValueOff)
        self.mi_role_user_and_system.setState_(NSControlStateValueOn if role == "UserAndSystem" else NSControlStateValueOff)

        mode = self.config.output_mode
        self.mi_mode_loose.setState_(NSControlStateValueOn if mode == "loose_diary" else NSControlStateValueOff)
        self.mi_mode_strict.setState_(NSControlStateValueOn if mode == "strict_json" else NSControlStateValueOff)

        nmode = self.config.notifications_mode
        self.mi_notif_all.setState_(NSControlStateValueOn if nmode == "all" else NSControlStateValueOff)
        self.mi_notif_hotkey.setState_(NSControlStateValueOn if nmode == "hotkey_only" else NSControlStateValueOff)
        self.mi_notif_off.setState_(NSControlStateValueOn if nmode == "off" else NSControlStateValueOff)

        self.mi_hotkey.setState_(NSControlStateValueOn if self.config.hotkey_enabled else NSControlStateValueOff)

        # overlay states
        self.mi_overlay_enabled.setState_(NSControlStateValueOn if self.config.overlay_enabled else NSControlStateValueOff)

        click = self.config.overlay_click_action
        self.mi_overlay_click_blank.setState_(NSControlStateValueOn if click == "generate_blank" else NSControlStateValueOff)
        self.mi_overlay_click_prompt.setState_(NSControlStateValueOn if click == "open_prompt_panel" else NSControlStateValueOff)

        self.mi_overlay_all_spaces.setState_(NSControlStateValueOn if self.config.overlay_show_all_spaces else NSControlStateValueOff)
        self.mi_overlay_hide_fullscreen.setState_(NSControlStateValueOn if self.config.overlay_hide_in_fullscreen else NSControlStateValueOff)

    # ---------- Core ----------
    def _make_entries(self, role_selection: str, prompt: str) -> List[EntryModel]:
        self.id_service.strategy = self.config.id_strategy
        shared_id = self.id_service.generate()
        datumtijd = self.dt_service.datumtijd_yyyymmdd()

        if role_selection == "UserAndSystem":
            return [
                EntryModel(id=shared_id, role="user", prompt=prompt, datumtijd=datumtijd),
                EntryModel(id=shared_id, role="system", prompt=prompt, datumtijd=datumtijd),
            ]
        # single
        role = role_selection if role_selection in ("user", "system") else "user"
        return [EntryModel(id=shared_id, role=role, prompt=prompt, datumtijd=datumtijd)]

    def _format_entry(self, entry: EntryModel) -> str:
        if self.config.output_mode == "strict_json":
            return self.formatter.format_strict_json(entry, pretty=self.config.json_pretty)
        return self.formatter.format_loose_diary(entry)

    def _format_entries(self, entries: List[EntryModel]) -> str:
        blocks = [self._format_entry(e) for e in entries]
        return "\n\n".join(blocks)

    def _should_notify(self, source: str) -> bool:
        nmode = self.config.notifications_mode
        if nmode == "off":
            return False
        if nmode == "hotkey_only":
            return source == "hotkey"
        return True  # all

    def generate_and_copy(self, role_override: Optional[str] = None, prompt: str = "", source: str = "menu") -> None:
        role_sel = role_override or self.config.default_role
        entries = self._make_entries(role_selection=role_sel, prompt=prompt or "")
        out = self._format_entries(entries)

        self.clipboard.copy_text(out)
        NSLog("Copied entry(s) (role_sel=%@, mode=%@, blocks=%d)", role_sel, self.config.output_mode, len(entries))

        if self._should_notify(source):
            mode_label = "A" if self.config.output_mode == "loose_diary" else "B"
            body = self.get_string("notify.body") % (role_sel, mode_label, len(entries))
            self.notifier.notify(self.get_string("notify.title"), body)

    # ---------- Hotkey ----------
    def _start_hotkey(self) -> bool:
        if not CARBON_AVAILABLE:
            NSLog("Carbon not available; hotkey disabled.")
            return False

        if self.hotkey is not None:
            self.hotkey.stop()
            self.hotkey = None

        def _trigger():
            try:
                self.generate_and_copy(source="hotkey")
            except Exception as e:
                NSLog("Hotkey generate error: %@", str(e))

        self.hotkey = HotkeyService(
            keycode=self.config.hotkey_keycode,
            modifiers=self.config.hotkey_modifiers,
            on_trigger=_trigger,
        )
        ok = self.hotkey.start()
        if not ok:
            NSLog("Hotkey registration failed; continuing without hotkey.")
        return ok

    def _stop_hotkey(self):
        if self.hotkey is not None:
            try:
                self.hotkey.stop()
            except Exception:
                pass
            self.hotkey = None

    # Apply callbacks from settings panel:
    # - "hotkey": enable/disable
    # - "hotkey_candidate": attempt register candidate (keycode, modifiers) -> returns (ok, err)
    # - "notifications": update permission best-effort
    # - "json": refresh only
    def apply_settings(self, reason: str, payload=None):
        if reason == "hotkey":
            if self.config.hotkey_enabled:
                ok = self._start_hotkey()
                if not ok:
                    return (False, "conflict/unavailable")
            else:
                self._stop_hotkey()
            self._refresh_menu_states()
            return (True, None)

        if reason == "hotkey_candidate":
            if not self.config.hotkey_enabled:
                self._refresh_menu_states()
                return (True, None)

            keycode, modifiers = payload
            if not CARBON_AVAILABLE:
                return (False, "Carbon missing")

            self._stop_hotkey()

            def _trigger():
                try:
                    self.generate_and_copy(source="hotkey")
                except Exception as e:
                    NSLog("Hotkey generate error: %@", str(e))

            tmp = HotkeyService(keycode=keycode, modifiers=modifiers, on_trigger=_trigger)
            ok = tmp.start()
            if ok:
                self.hotkey = tmp
                self._refresh_menu_states()
                return (True, None)

            # Revert to previous
            self.hotkey = None
            reverted_ok = False
            if self.config.hotkey_enabled:
                reverted_ok = self._start_hotkey()
            self._refresh_menu_states()
            return (False, "conflict/unavailable" if not reverted_ok else "conflict")

        if reason == "notifications":
            if self.config.notifications_mode != "off":
                self.notifier.ensure_permission()
            self._refresh_menu_states()
            return (True, None)

        if reason == "json":
            self._refresh_menu_states()
            return (True, None)

        return (True, None)

    # ---------- Overlay ----------
    def _ensure_overlay(self):
        if self.overlay is None:
            self.overlay = OverlayBubbleController.alloc().initWithApp_(self)

    def _apply_overlay_visibility(self):
        self._ensure_overlay()
        if self.config.overlay_enabled:
            self.overlay.show()
        else:
            self.overlay.hide()
        self._refresh_menu_states()

    def _apply_overlay_behavior(self):
        self._ensure_overlay()
        try:
            self.overlay.apply_behavior()
        except Exception:
            pass

    def build_overlay_context_menu(self) -> NSMenu:
        menu = NSMenu.alloc().init()

        mi_gen = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.generate"), "onGenerateEntry:", "")
        mi_gen.setTarget_(self)
        menu.addItem_(mi_gen)

        mi_prompt = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.generate_prompt"), "onGenerateWithPrompt:", "")
        mi_prompt.setTarget_(self)
        menu.addItem_(mi_prompt)

        menu.addItem_(NSMenuItem.separatorItem())

        # Mode toggles
        mi_mode_a = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.mode.a"), "onSetModeLoose:", "")
        mi_mode_a.setTarget_(self)
        mi_mode_a.setState_(NSControlStateValueOn if self.config.output_mode == "loose_diary" else NSControlStateValueOff)
        menu.addItem_(mi_mode_a)

        mi_mode_b = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.mode.b"), "onSetModeStrict:", "")
        mi_mode_b.setTarget_(self)
        mi_mode_b.setState_(NSControlStateValueOn if self.config.output_mode == "strict_json" else NSControlStateValueOff)
        menu.addItem_(mi_mode_b)

        menu.addItem_(NSMenuItem.separatorItem())

        mi_settings = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.settings"), "onOpenSettings:", "")
        mi_settings.setTarget_(self)
        menu.addItem_(mi_settings)

        mi_hide = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.overlay.enabled"), "onToggleOverlayEnabled:", "")
        mi_hide.setTarget_(self)
        # This item is a toggle; title already says enabled; we keep it simple.
        menu.addItem_(mi_hide)

        menu.addItem_(NSMenuItem.separatorItem())

        mi_quit = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.get_string("menu.quit"), "terminate:", "")
        menu.addItem_(mi_quit)
        return menu

    # ---------- UI helpers ----------
    def _show_error(self, title: str, message: str) -> None:
        alert = NSAlert.alloc().init()
        alert.setAlertStyle_(2)  # critical
        alert.setMessageText_(title)
        alert.setInformativeText_(message)
        alert.addButtonWithTitle_("OK")
        alert.runModal()

    def open_prompt_panel(self):
        if self.prompt_panel is None:
            def _cb(role_sel, prompt):
                if role_sel is None and prompt is None:
                    return
                try:
                    self.generate_and_copy(role_override=str(role_sel), prompt=str(prompt), source="menu")
                except Exception as e:
                    self._show_error("Error", str(e))

            self.prompt_panel = PromptPanelController.alloc().initWithApp_callback_(self, _cb)

        try:
            self.prompt_panel.refresh_texts()
        except Exception:
            pass
        self.prompt_panel.show()

    # ---------- Menu handlers ----------
    def onGenerateEntry_(self, sender):
        try:
            self.generate_and_copy(source="menu")
        except Exception as e:
            self._show_error(self.get_string("alert.clipboard.title"), str(e))

    def onGenerateWithPrompt_(self, sender):
        try:
            self.open_prompt_panel()
        except Exception as e:
            self._show_error("Error", str(e))

    def onOpenSettings_(self, sender):
        try:
            if self.settings_panel is None:
                self.settings_panel = SettingsPanelController.alloc().initWithApp_applyCallback_(self, self.apply_settings)
            else:
                try:
                    self.settings_panel._refresh_ui_state()
                except Exception:
                    pass
            self.settings_panel.refresh_texts()
            self.settings_panel.show()
        except Exception as e:
            self._show_error("Error", str(e))

    # Role
    def onSetRoleUser_(self, sender):
        self.config.set_default_role("user")
        self._refresh_menu_states()
        if self.prompt_panel is not None:
            try:
                self.prompt_panel.refresh_texts()
            except Exception:
                pass

    def onSetRoleSystem_(self, sender):
        self.config.set_default_role("system")
        self._refresh_menu_states()
        if self.prompt_panel is not None:
            try:
                self.prompt_panel.refresh_texts()
            except Exception:
                pass

    def onSetRoleUserAndSystem_(self, sender):
        self.config.set_default_role("UserAndSystem")
        self._refresh_menu_states()
        if self.prompt_panel is not None:
            try:
                self.prompt_panel.refresh_texts()
            except Exception:
                pass

    # Output mode
    def onSetModeLoose_(self, sender):
        self.config.set_output_mode("loose_diary")
        self._refresh_menu_states()

    def onSetModeStrict_(self, sender):
        self.config.set_output_mode("strict_json")
        self._refresh_menu_states()

    # Notifications
    def onSetNotifAll_(self, sender):
        self.config.set_notifications_mode("all")
        if self.config.notifications_mode != "off":
            self.notifier.ensure_permission()
        self._refresh_menu_states()

    def onSetNotifHotkeyOnly_(self, sender):
        self.config.set_notifications_mode("hotkey_only")
        if self.config.notifications_mode != "off":
            self.notifier.ensure_permission()
        self._refresh_menu_states()

    def onSetNotifOff_(self, sender):
        self.config.set_notifications_mode("off")
        self._refresh_menu_states()

    # Hotkey toggle
    def onToggleHotkey_(self, sender):
        new_state = not self.config.hotkey_enabled
        self.config.set_hotkey_enabled(new_state)
        if new_state:
            ok = self._start_hotkey()
            if not ok:
                self._show_error(self.get_string("alert.hotkey.title"), self.get_string("alert.hotkey.msg"))
        else:
            self._stop_hotkey()
        self._refresh_menu_states()

    # Overlay toggles
    def onToggleOverlayEnabled_(self, sender):
        self.config.set_overlay_enabled(not self.config.overlay_enabled)
        self._apply_overlay_visibility()

    def onSetOverlayClickBlank_(self, sender):
        self.config.set_overlay_click_action("generate_blank")
        self._apply_overlay_behavior()
        self._refresh_menu_states()

    def onSetOverlayClickPrompt_(self, sender):
        self.config.set_overlay_click_action("open_prompt_panel")
        self._apply_overlay_behavior()
        self._refresh_menu_states()

    def onToggleOverlayAllSpaces_(self, sender):
        self.config.set_overlay_show_all_spaces(not self.config.overlay_show_all_spaces)
        self._apply_overlay_behavior()
        self._refresh_menu_states()

    def onToggleOverlayHideFullscreen_(self, sender):
        self.config.set_overlay_hide_in_fullscreen(not self.config.overlay_hide_in_fullscreen)
        self._apply_overlay_behavior()
        self._refresh_menu_states()


def main():
    app = NSApplication.sharedApplication()
    delegate = AppController.alloc().init()
    app.setDelegate_(delegate)
    AppHelper.runEventLoop()


if __name__ == "__main__":
    main()
    