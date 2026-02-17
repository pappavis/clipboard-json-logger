# Clipboard JSON Logger
# Version: 0.3.1
# Date: 2026-02-18
#
# macOS Menu Bar utility (PyObjC) to generate a "chatlog entry"
# and copy it to the clipboard.
#
# Output modes:
# - Mode A: loose diary format (default)
# - Mode B: strict JSON (toggle)
#
# v0.3 adds:
# - Multiline prompt panel (NSPanel + NSTextView)
# - Notifications (UserNotifications) with policy: All / Hotkey only / Off
# - Settings panel with hotkey capture + apply
# v0,3.1 adds:
# - Fix: robust NSObject imports (prefer Cocoa; fallback to Foundation) to avoid venv collisions

from __future__ import annotations

import json
import secrets
import string
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional, Tuple

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
    NSWindowStyleMaskTitled,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskUtilityWindow,
    NSWindowStyleMaskResizable,
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
    NSMakeRect,
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
    # Provided via pyobjc-framework-UserNotifications (often included with pyobjc)
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
APP_VERSION = "0.3.1"
APP_BUILD_DATE = "2026-02-18"
DEFAULT_TIMEZONE = "Europe/Amsterdam"

# NSUserDefaults keys
K_DEFAULT_ROLE = "default_role"
K_ID_STRATEGY = "id_strategy"  # short_id | uuid4
K_OUTPUT_MODE = "output_mode"  # loose_diary | strict_json
K_DATUMTIJD_STRATEGY = "datumtijd_strategy"  # date_yyyymmdd
K_HOTKEY_ENABLED = "hotkey_enabled"
K_HOTKEY_KEYCODE = "hotkey_keycode"
K_HOTKEY_MODIFIERS = "hotkey_modifiers"

# v0.3.1 settings
K_NOTIFICATIONS_MODE = "notifications_mode"  # all | hotkey_only | off
K_JSON_PRETTY = "json_pretty"  # bool


# ----------------------------
# Domain
# ----------------------------
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
            self.ud.setInteger_forKey_(HIToolbox.kVK_ANSI_J if CARBON_AVAILABLE else 38, K_HOTKEY_KEYCODE)

        if self.ud.objectForKey_(K_HOTKEY_MODIFIERS) is None:
            default_mods = 0
            if CARBON_AVAILABLE:
                default_mods = HIToolbox.controlKey | HIToolbox.optionKey | HIToolbox.cmdKey
            self.ud.setInteger_forKey_(int(default_mods), K_HOTKEY_MODIFIERS)

        # v0.3 notifications: default hotkey_only (spam mitigation)
        if self.ud.objectForKey_(K_NOTIFICATIONS_MODE) is None:
            self.ud.setObject_forKey_("hotkey_only", K_NOTIFICATIONS_MODE)

        if self.ud.objectForKey_(K_JSON_PRETTY) is None:
            self.ud.setBool_forKey_(True, K_JSON_PRETTY)

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
    Mode A: loose diary format
    Mode B: strict JSON (valid JSON)
    """

    @staticmethod
    def format_loose_diary(entry: EntryModel) -> str:
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


# ----------------------------
# OS services
# ----------------------------
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
    we degrade gracefully (no crash).
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

        # Request permission async; we don't block app usage if user denies.
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

    def notify_copied(self, title: str, body: str) -> None:
        if not self.is_available():
            return

        # Attempt permission request (idempotent best-effort)
        self.ensure_permission()

        try:
            content = UNMutableNotificationContent.alloc().init()
            content.setTitle_(title)
            content.setBody_(body)

            # Deliver immediately (no trigger)
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


# ----------------------------
# UI: Prompt panel
# ----------------------------
class PromptPanelController(NSObject):
    """
    Reusable multiline prompt panel: NSPanel + NSTextView.
    Calls back with (role_override, prompt) or None if cancelled.
    """

    def initWithDefaults_callback_(self, default_role: str, callback):
        self = objc.super(PromptPanelController, self).init()
        if self is None:
            return None

        self._callback = callback
        self._default_role = default_role

        self.panel = None
        self.role_popup = None
        self.text_view = None

        self._build_ui()
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
        self.panel.setTitle_("Generate with Prompt")

        content = self.panel.contentView()

        # Role label + popup
        lbl_role = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 320, 60, 22))
        lbl_role.setStringValue_("Role:")
        lbl_role.setEditable_(False)
        lbl_role.setBordered_(False)
        lbl_role.setDrawsBackground_(False)
        content.addSubview_(lbl_role)

        self.role_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(80, 316, 140, 26))
        self.role_popup.addItemWithTitle_("user")
        self.role_popup.addItemWithTitle_("system")
        # Default role selection
        if self._default_role == "system":
            self.role_popup.selectItemWithTitle_("system")
        else:
            self.role_popup.selectItemWithTitle_("user")
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
        btn_copy = NSButton.alloc().initWithFrame_(NSMakeRect(320, 20, 180, 32))
        btn_copy.setTitle_("Copy Entry")
        btn_copy.setButtonType_(NSMomentaryPushInButton)
        btn_copy.setBezelStyle_(NSBezelStyleRounded)
        btn_copy.setTarget_(self)
        btn_copy.setAction_("onCopy:")
        content.addSubview_(btn_copy)

        btn_cancel = NSButton.alloc().initWithFrame_(NSMakeRect(220, 20, 90, 32))
        btn_cancel.setTitle_("Cancel")
        btn_cancel.setButtonType_(NSMomentaryPushInButton)
        btn_cancel.setBezelStyle_(NSBezelStyleRounded)
        btn_cancel.setTarget_(self)
        btn_cancel.setAction_("onCancel:")
        content.addSubview_(btn_cancel)

    def show(self):
        # Make text view first responder
        self.panel.makeKeyAndOrderFront_(None)
        self.panel.makeFirstResponder_(self.text_view)

    def onCopy_(self, sender):
        try:
            role = str(self.role_popup.titleOfSelectedItem())
            prompt = str(self.text_view.string() or "")
            self.panel.orderOut_(None)
            if self._callback:
                self._callback(role, prompt)
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
        # These bitmasks are stable in NSEventModifierFlags; use integer comparisons.
        # Control: 1<<18, Option: 1<<19, Shift: 1<<17, Command: 1<<20 (typical)
        # We'll map to Carbon masks when available; otherwise store 0 and rely on menu-only usage.
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
    """

    def initWithConfig_applyCallback_(self, config: AppConfig, apply_callback):
        self = objc.super(SettingsPanelController, self).init()
        if self is None:
            return None

        self.config = config
        self.apply_callback = apply_callback

        self.panel = None
        self.chk_hotkey = None
        self.lbl_hotkey = None
        self.btn_capture = None
        self.btn_reset = None
        self.mode_popup = None
        self.chk_json_pretty = None
        self.lbl_status = None

        self.capture_view = None
        self._capture_active = False

        self._build_ui()
        self._refresh_ui()
        return self

    def _build_ui(self):
        style = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskUtilityWindow
        self.panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(260, 260, 520, 240), style, NSBackingStoreBuffered, False
        )
        self.panel.setTitle_("Settings")

        content = self.panel.contentView()

        # Hotkey enabled switch
        self.chk_hotkey = NSButton.alloc().initWithFrame_(NSMakeRect(20, 190, 240, 24))
        self.chk_hotkey.setButtonType_(NSSwitchButton)
        self.chk_hotkey.setTitle_("Hotkey Enabled")
        self.chk_hotkey.setTarget_(self)
        self.chk_hotkey.setAction_("onToggleHotkeyEnabled:")
        content.addSubview_(self.chk_hotkey)

        # Current hotkey label
        lbl = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 160, 120, 22))
        lbl.setStringValue_("Current hotkey:")
        lbl.setEditable_(False)
        lbl.setBordered_(False)
        lbl.setDrawsBackground_(False)
        content.addSubview_(lbl)

        self.lbl_hotkey = NSTextField.alloc().initWithFrame_(NSMakeRect(140, 156, 360, 24))
        self.lbl_hotkey.setEditable_(False)
        self.lbl_hotkey.setBordered_(True)
        self.lbl_hotkey.setDrawsBackground_(True)
        content.addSubview_(self.lbl_hotkey)

        # Capture/reset buttons
        self.btn_capture = NSButton.alloc().initWithFrame_(NSMakeRect(20, 120, 160, 30))
        self.btn_capture.setTitle_("Capture Hotkey…")
        self.btn_capture.setBezelStyle_(NSBezelStyleRounded)
        self.btn_capture.setTarget_(self)
        self.btn_capture.setAction_("onCaptureHotkey:")
        content.addSubview_(self.btn_capture)

        self.btn_reset = NSButton.alloc().initWithFrame_(NSMakeRect(190, 120, 120, 30))
        self.btn_reset.setTitle_("Reset")
        self.btn_reset.setBezelStyle_(NSBezelStyleRounded)
        self.btn_reset.setTarget_(self)
        self.btn_reset.setAction_("onResetHotkey:")
        content.addSubview_(self.btn_reset)

        # Notifications mode
        lbl_n = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 82, 120, 22))
        lbl_n.setStringValue_("Notifications:")
        lbl_n.setEditable_(False)
        lbl_n.setBordered_(False)
        lbl_n.setDrawsBackground_(False)
        content.addSubview_(lbl_n)

        self.mode_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(140, 78, 200, 26))
        self.mode_popup.addItemWithTitle_("All")
        self.mode_popup.addItemWithTitle_("Hotkey only")
        self.mode_popup.addItemWithTitle_("Off")
        self.mode_popup.setTarget_(self)
        self.mode_popup.setAction_("onNotificationsModeChanged:")
        content.addSubview_(self.mode_popup)

        # JSON pretty (strict mode)
        self.chk_json_pretty = NSButton.alloc().initWithFrame_(NSMakeRect(20, 46, 240, 24))
        self.chk_json_pretty.setButtonType_(NSSwitchButton)
        self.chk_json_pretty.setTitle_("Pretty JSON (Mode B)")
        self.chk_json_pretty.setTarget_(self)
        self.chk_json_pretty.setAction_("onToggleJsonPretty:")
        content.addSubview_(self.chk_json_pretty)

        # Status line
        self.lbl_status = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 16, 480, 22))
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
        self.panel.makeKeyAndOrderFront_(None)

    def _refresh_ui(self):
        self.chk_hotkey.setState_(NSControlStateValueOn if self.config.hotkey_enabled else NSControlStateValueOff)
        self.lbl_hotkey.setStringValue_(format_hotkey_display(self.config.hotkey_keycode, self.config.hotkey_modifiers))
        self.chk_json_pretty.setState_(NSControlStateValueOn if self.config.json_pretty else NSControlStateValueOff)

        # Notifications mode -> popup
        mode = self.config.notifications_mode
        if mode == "all":
            self.mode_popup.selectItemWithTitle_("All")
        elif mode == "off":
            self.mode_popup.selectItemWithTitle_("Off")
        else:
            self.mode_popup.selectItemWithTitle_("Hotkey only")

    def _set_status(self, msg: str):
        self.lbl_status.setStringValue_(msg)

    # ---- handlers ----
    def onToggleHotkeyEnabled_(self, sender):
        enabled = sender.state() == NSControlStateValueOn
        self.config.set_hotkey_enabled(enabled)
        self._refresh_ui()
        self.apply_callback("hotkey")

    def onNotificationsModeChanged_(self, sender):
        title = str(self.mode_popup.titleOfSelectedItem())
        if title == "All":
            mode = "all"
        elif title == "Off":
            mode = "off"
        else:
            mode = "hotkey_only"
        self.config.set_notifications_mode(mode)
        self._refresh_ui()
        self.apply_callback("notifications")

    def onToggleJsonPretty_(self, sender):
        pretty = sender.state() == NSControlStateValueOn
        self.config.set_json_pretty(pretty)
        self._refresh_ui()
        self.apply_callback("json")

    def onResetHotkey_(self, sender):
        if not CARBON_AVAILABLE:
            self._set_status("Hotkey not available (Carbon missing).")
            return

        # Reset to Ctrl+Opt+Cmd+J
        keycode = HIToolbox.kVK_ANSI_J
        modifiers = HIToolbox.controlKey | HIToolbox.optionKey | HIToolbox.cmdKey
        self._apply_hotkey_candidate(keycode, modifiers, is_reset=True)

    def onCaptureHotkey_(self, sender):
        if not CARBON_AVAILABLE:
            self._set_status("Hotkey capture not available (Carbon missing).")
            return

        self._capture_active = True
        self.capture_view.setCapturing_(True)
        self._set_status("Press a key combo now… (requires at least 1 modifier)")
        # Make capture view first responder so it gets keyDown events
        self.panel.makeFirstResponder_(self.capture_view)

    # ---- capture callback ----
    def __onCapturedHotkey(self, keycode: int, modifiers: int):
        if not self._capture_active:
            return

        self._capture_active = False
        self.capture_view.setCapturing_(False)

        # Validate: at least one modifier
        if modifiers == 0:
            self._set_status("Rejected: add at least 1 modifier (Ctrl/Opt/Cmd/Shift).")
            # Return focus to panel
            self.panel.makeFirstResponder_(None)
            return

        self._apply_hotkey_candidate(keycode, modifiers, is_reset=False)

    def _apply_hotkey_candidate(self, keycode: int, modifiers: int, is_reset: bool):
        # Attempt apply via callback (register hotkey). If ok, persist.
        ok, err = self.apply_callback("hotkey_candidate", (keycode, modifiers))
        if ok:
            self.config.set_hotkey(keycode, modifiers)
            self._refresh_ui()
            self._set_status("Hotkey applied." if not is_reset else "Hotkey reset + applied.")
        else:
            self._set_status(f"Hotkey failed: {err or 'conflict/unavailable'}")
            self._refresh_ui()


# ----------------------------
# Helpers: hotkey display
# ----------------------------
KEYCODE_TO_CHAR = {
    # ANSI letters
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
    # digits row
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
# App Controller
# ----------------------------
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
        self.notifier = NotificationService()

        self.status_item = None
        self.menu = None

        self.hotkey = None
        self.prompt_panel = None
        self.settings_panel = None

        return self

    def applicationDidFinishLaunching_(self, notification):
        NSLog("%@ v%@ (%@) launching", APP_NAME, APP_VERSION, APP_BUILD_DATE)
        self._setup_menu_bar()

        # Best-effort hotkey
        if self.config.hotkey_enabled:
            self._start_hotkey()

        # If notifications are enabled (not off) prepare permission best-effort
        if self.config.notifications_mode != "off":
            self.notifier.ensure_permission()

    def applicationWillTerminate_(self, notification):
        # Best-effort cleanup
        try:
            if self.hotkey is not None:
                self.hotkey.stop()
                self.hotkey = None
        except Exception:
            pass

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

        # Notifications submenu
        notif_menu = NSMenu.alloc().init()
        self.mi_notif_all = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("All", "onSetNotifAll:", "")
        self.mi_notif_all.setTarget_(self)
        notif_menu.addItem_(self.mi_notif_all)

        self.mi_notif_hotkey = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Hotkey only", "onSetNotifHotkeyOnly:", "")
        self.mi_notif_hotkey.setTarget_(self)
        notif_menu.addItem_(self.mi_notif_hotkey)

        self.mi_notif_off = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Off", "onSetNotifOff:", "")
        self.mi_notif_off.setTarget_(self)
        notif_menu.addItem_(self.mi_notif_off)

        notif_root = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Notifications", None, "")
        notif_root.setSubmenu_(notif_menu)
        self.menu.addItem_(notif_root)

        self.menu.addItem_(NSMenuItem.separatorItem())

        # Settings…
        mi_settings = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Settings…", "onOpenSettings:", "")
        mi_settings.setTarget_(self)
        self.menu.addItem_(mi_settings)

        # Hotkey quick toggle in menu (optional convenience)
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
        role = self.config.default_role
        self.mi_role_user.setState_(NSControlStateValueOn if role == "user" else NSControlStateValueOff)
        self.mi_role_system.setState_(NSControlStateValueOn if role == "system" else NSControlStateValueOff)

        mode = self.config.output_mode
        self.mi_mode_loose.setState_(NSControlStateValueOn if mode == "loose_diary" else NSControlStateValueOff)
        self.mi_mode_strict.setState_(NSControlStateValueOn if mode == "strict_json" else NSControlStateValueOff)

        nmode = self.config.notifications_mode
        self.mi_notif_all.setState_(NSControlStateValueOn if nmode == "all" else NSControlStateValueOff)
        self.mi_notif_hotkey.setState_(NSControlStateValueOn if nmode == "hotkey_only" else NSControlStateValueOff)
        self.mi_notif_off.setState_(NSControlStateValueOn if nmode == "off" else NSControlStateValueOff)

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
            return self.formatter.format_strict_json(entry, pretty=self.config.json_pretty)
        return self.formatter.format_loose_diary(entry)

    def _should_notify(self, source: str) -> bool:
        nmode = self.config.notifications_mode
        if nmode == "off":
            return False
        if nmode == "hotkey_only":
            return source == "hotkey"
        return True  # all

    def generate_and_copy(self, role_override: Optional[str] = None, prompt: str = "", source: str = "menu") -> None:
        role = role_override or self.config.default_role
        entry = self._make_entry(role=role, prompt=prompt)
        out = self._format_entry(entry)

        self.clipboard.copy_text(out)

        NSLog("Copied entry (role=%@, mode=%@, id_strategy=%@)", role, self.config.output_mode, self.config.id_strategy)

        if self._should_notify(source):
            title = "Copied entry"
            body = f"role={role}, mode={'A' if self.config.output_mode=='loose_diary' else 'B'}"
            self.notifier.notify_copied(title, body)

    # ---------- Hotkey ----------
    def _start_hotkey(self) -> bool:
        if not CARBON_AVAILABLE:
            NSLog("Carbon not available; hotkey disabled.")
            return False

        # Stop existing
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
                # If hotkey is disabled, we still accept saving but can't validate registration.
                self._refresh_menu_states()
                return (True, None)

            # Try start with candidate without persisting yet
            keycode, modifiers = payload
            # Temporarily register
            if not CARBON_AVAILABLE:
                return (False, "Carbon missing")

            # Stop existing and attempt candidate
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

    # ---------- Menu handlers ----------
    def onGenerateEntry_(self, sender):
        try:
            self.generate_and_copy(source="menu")
        except Exception as e:
            self._show_error("Clipboard error", str(e))

    def onGenerateWithPrompt_(self, sender):
        try:
            if self.prompt_panel is None:
                # Callback receives (role, prompt) or (None, None)
                def _cb(role, prompt):
                    if role is None and prompt is None:
                        return
                    try:
                        self.generate_and_copy(role_override=str(role), prompt=str(prompt), source="menu")
                    except Exception as e:
                        self._show_error("Error", str(e))

                self.prompt_panel = PromptPanelController.alloc().initWithDefaults_callback_(self.config.default_role, _cb)

            # Always refresh default role selection before showing
            # (If user changed role in menu)
            try:
                if self.config.default_role == "system":
                    self.prompt_panel.role_popup.selectItemWithTitle_("system")
                else:
                    self.prompt_panel.role_popup.selectItemWithTitle_("user")
            except Exception:
                pass

            self.prompt_panel.show()
        except Exception as e:
            self._show_error("Error", str(e))

    def onOpenSettings_(self, sender):
        try:
            if self.settings_panel is None:
                self.settings_panel = SettingsPanelController.alloc().initWithConfig_applyCallback_(
                    self.config, self.apply_settings
                )
            else:
                # refresh current values
                try:
                    self.settings_panel._refresh_ui()
                except Exception:
                    pass
            self.settings_panel.show()
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

    def onToggleHotkey_(self, sender):
        new_state = not self.config.hotkey_enabled
        self.config.set_hotkey_enabled(new_state)
        if new_state:
            ok = self._start_hotkey()
            if not ok:
                self._show_error("Hotkey", "Hotkey conflict/unavailable. Try another combo in Settings…")
        else:
            self._stop_hotkey()
        self._refresh_menu_states()

    # ---------- UI helpers ----------
    def _show_error(self, title: str, message: str) -> None:
        alert = NSAlert.alloc().init()
        alert.setAlertStyle_(2)  # critical
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