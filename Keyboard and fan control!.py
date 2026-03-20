#!/usr/bin/env python3
"""
Tongfang/AiStone X6RP57TW - System Controller
==============================================
Complete system control: RGB Keyboard + Fan Controller with GTK4 GUI
All controls in ONE panel - Keyboard on top, Fans below

Features:
- 126-zone keyboard RGB control
- Visual keyboard layout with per-key colors
- Dual fan control (CPU/GPU)
- Chassis visualization
- Safe EC operations with validation

Requirements:
- Python 3 with PyGObject (GTK4)
- acpi_call kernel module (for fan control)
- ec_sys kernel module (for fan monitoring)

Author: Aineasg
License: MIT
"""

import os
import sys
import json
import signal
import subprocess
import time
import re
import shutil
import math
import random
import threading
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import IntEnum

try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, Gdk, GLib, Pango, cairo
except ImportError:
    print("ERROR: PyGObject not found!")
    print("\nInstall dependencies:")
    print("  Arch/Manjaro:    sudo pacman -S python-gobject gtk4")
    print("  Debian/Ubuntu:   sudo apt install python3-gi gir1.2-gtk-4.0")
    print("  Fedora:          sudo dnf install python3-gobject gtk4")
    sys.exit(1)

# ============================================================================
# CONFIGURATION
# ============================================================================

# RGB Configuration
SYSFS_BASE = "/sys/class/leds"
LED_PREFIX = "rgb:kbd_backlight"
MAX_BRIGHTNESS = 50
TOTAL_ZONES = 126
PID_FILE = "/tmp/kbd-rgb.pid"
STATE_FILE = "/tmp/kbd-rgb-state.json"

# Fan Controller Configuration
class FanMode(IntEnum):
    INTELLIGENT = 0x00
    TURBO = 0x10
    BOOST = 0x40
    CUSTOM = 0xA0

# EC Addresses (DO NOT MODIFY unless you know what you're doing!)
EC_ADDR_MAFAN_CONTROL = 1873
EC_ADDR_CPU_FAN_L1_PWM = 1859  # +0 to +4 for L1-L5
EC_ADDR_FAN_MIN_SPEED = 1950
EC_ADDR_FAN_MIN_TEMP = 1951
EC_ADDR_FAN_EXTRA_SPEED = 1952
EC_ADDR_SUPPORT_BYTE5 = 1858

# EC Read offsets (from sysfs)
EC_CPU_RPM_LO = 0x08
EC_CPU_RPM_HI = 0x09
EC_CPU_TEMP = 0x3E
EC_FAN_DUTY = 0x60
EC_FAN_STEP = 0x64
EC_FAN_MODE = 0x8D
EC_GPU_RPM_LO = 0xC8
EC_GPU_RPM_HI = 0xC9

# Safety limits
MIN_PWM = 0
MAX_PWM = 200  # Maximum safe PWM value
MIN_TEMP = 30
MAX_TEMP = 95
SAFE_PRESETS = {
    "silent": (20, 40, 70, 90, 110),
    "balanced": (60, 80, 100, 120, 140),
    "performance": (80, 100, 120, 150, 180),
    "gaming": (100, 130, 160, 180, 200),
}

# Color presets for RGB
COLORS = {
    "off": (0, 0, 0), "black": (0, 0, 0),
    "red": (50, 0, 0), "green": (0, 50, 0), "blue": (0, 0, 50),
    "yellow": (50, 50, 0), "purple": (50, 0, 50), "cyan": (0, 50, 50),
    "white": (50, 50, 50), "orange": (50, 25, 0), "pink": (50, 0, 25),
    "lime": (25, 50, 0), "teal": (0, 50, 25), "navy": (0, 0, 35),
    "violet": (35, 0, 50), "magenta": (50, 0, 45), "indigo": (25, 0, 50),
    "gold": (50, 40, 0), "coral": (50, 25, 20), "silver": (35, 35, 35),
    "gray": (25, 25, 25), "dim": (10, 10, 10),
}

KEY_MAP = {
    "ctrl": 0, "lctrl": 0, "fn": 2, "lwin": 3, "win": 3,
    "lalt": 4, "alt": 4, "space": 7, "ralt": 10, "altgr": 10,
    # NOTE: zone 11 (rctrl) is absent from sysfs on this laptop –
    #       the right-Ctrl button shows in the GUI but has no physical LED.
    "rctrl": 11, "copilot": 12,
    "left": 13, "up": 14, "right": 15, "down": 18,
    "numpad_0": 16, "numpad_dot": 17,
    "lshift": 22, "shift": 22, "backslash_left": 23,
    "z": 24, "x": 25, "c": 26, "v": 27, "b": 28, "n": 29, "m": 30,
    "comma": 31, ",": 31, "period": 32, ".": 32, "slash": 33, "/": 33,
    "rshift": 35,
    "numpad_1": 36, "numpad_2": 37, "numpad_3": 38, "numpad_enter": 39,
    "tab": 42,
    # NOTE: zone 43 is "non" on this laptop (CapsLock has no backlight LED).
    "caps": 43, "capslock": 43,
    "a": 44, "s": 45, "d": 46, "f": 47, "g": 48,
    "h": 49, "j": 50, "k": 51, "l": 52,
    "semicolon": 53, ";": 53, "quote": 54, "'": 54,
    "backslash": 55,
    "numpad_4": 57, "numpad_5": 58, "numpad_6": 59,
    "q": 65, "w": 66, "e": 67, "r": 68, "t": 69,
    "y": 70, "u": 71, "i": 72, "o": 73, "p": 74,
    "lbracket": 75, "[": 75, "rbracket": 76, "]": 76, "enter": 77,
    "numpad_7": 78, "numpad_8": 79, "numpad_9": 80, "numpad_plus": 81,
    "grave": 84, "`": 84,
    "1": 85, "2": 86, "3": 87, "4": 88, "5": 89,
    "6": 90, "7": 91, "8": 92, "9": 93, "0": 94,
    "minus": 95, "-": 95, "equal": 96, "=": 96,
    "backspace": 98, "numlock": 99,
    "numpad_slash": 100, "numpad_divide": 100,
    "numpad_multiply": 101, "numpad_minus": 102,
    "esc": 105, "escape": 105,
    "f1": 106, "f2": 107, "f3": 108, "f4": 109, "f5": 110,
    "f6": 111, "f7": 112, "f8": 113, "f9": 114, "f10": 115,
    "f11": 116, "f12": 117,
    "scrlock": 118, "prtsc": 119,
    "del": 120, "delete": 120, "home": 121, "pgup": 122,
    "pgdn": 123, "end": 124,
}

# Some physical keys span two separate LED zones.
# Map the primary key name to any extra zone(s) so all zones are written
# when a per-key color is applied.
# keyboard_map.txt: zone 42 = "tab" AND zone 63 = "tab" (Tab key has two zones)
SECONDARY_ZONES = {
    "tab": [63],
}

ZONE_TO_KEY = {v: k for k, v in KEY_MAP.items()}

SECTORS = {
    "wasd": ["w", "a", "s", "d"],
    "arrows": ["up", "down", "left", "right"],
    "qwerty": ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
    "letters": ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "a", "s", "d", "f", "g", "h", "j", "k", "l", "z", "x", "c", "v", "b", "n", "m"],
    "numbers": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
    "function": ["f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12", "esc"],
    "numpad": ["numpad_0", "numpad_1", "numpad_2", "numpad_3", "numpad_4", "numpad_5", "numpad_6", "numpad_7", "numpad_8", "numpad_9", "numlock"],
    "modifiers": ["lctrl", "lshift", "lalt", "lwin", "rctrl", "rshift", "ralt", "fn"],
}

KEYBOARD_LAYOUT = [
    ("fn", [("Esc", "esc", 1), ("F1", "f1", 1), ("F2", "f2", 1), ("F3", "f3", 1), ("F4", "f4", 1),
            ("F5", "f5", 1), ("F6", "f6", 1), ("F7", "f7", 1), ("F8", "f8", 1),
            ("F9", "f9", 1), ("F10", "f10", 1), ("F11", "f11", 1), ("F12", "f12", 1),
            ("PrtSc", "prtsc", 1), ("Ins", "home", 1), ("Del", "del", 1)]),
    ("num", [("`", "grave", 1), ("1", "1", 1), ("2", "2", 1), ("3", "3", 1), ("4", "4", 1),
             ("5", "5", 1), ("6", "6", 1), ("7", "7", 1), ("8", "8", 1), ("9", "9", 1),
             ("0", "0", 1), ("-", "minus", 1), ("=", "equal", 1), ("⌫", "backspace", 2),
             ("", "", 0.5), ("Num", "numlock", 1), ("/", "numpad_divide", 1), ("*", "numpad_multiply", 1), ("-", "numpad_minus", 1)]),
    ("qwerty", [("Tab", "tab", 1.5), ("Q", "q", 1), ("W", "w", 1), ("E", "e", 1), ("R", "r", 1),
                ("T", "t", 1), ("Y", "y", 1), ("U", "u", 1), ("I", "i", 1), ("O", "o", 1),
                ("P", "p", 1), ("[", "lbracket", 1), ("]", "rbracket", 1), ("\\", "backslash", 1.5),
                ("", "", 0.5), ("7", "numpad_7", 1), ("8", "numpad_8", 1), ("9", "numpad_9", 1), ("+", "numpad_plus", 1)]),
    ("home", [("Caps", "caps", 1.75), ("A", "a", 1), ("S", "s", 1), ("D", "d", 1), ("F", "f", 1),
              ("G", "g", 1), ("H", "h", 1), ("J", "j", 1), ("K", "k", 1), ("L", "l", 1),
              (";", "semicolon", 1), ("'", "quote", 1), ("Enter", "enter", 2.25),
              ("", "", 0.5), ("4", "numpad_4", 1), ("5", "numpad_5", 1), ("6", "numpad_6", 1), ("", "", 1)]),
    ("zxcv", [("Shift", "lshift", 2.25), ("Z", "z", 1), ("X", "x", 1), ("C", "c", 1),
              ("V", "v", 1), ("B", "b", 1), ("N", "n", 1), ("M", "m", 1),
              (",", "comma", 1), (".", "period", 1), ("/", "slash", 1), ("Shift", "rshift", 2.75),
              ("", "", 0.5), ("1", "numpad_1", 1), ("2", "numpad_2", 1), ("3", "numpad_3", 1), ("Ent", "numpad_enter", 1)]),
    ("bottom", [("Ctrl", "lctrl", 1.25), ("Fn", "fn", 1), ("Win", "lwin", 1.25), ("Alt", "lalt", 1.25),
                ("", "space", 6.25), ("Alt", "ralt", 1.25), ("Ctrl", "rctrl", 1.25),
                ("", "", 0.5), ("0", "numpad_0", 2), (".", "numpad_dot", 1)]),
    ("arrows", [("", "", 13), ("↑", "up", 1), ("", "", 2)]),
    ("arrows2", [("", "", 12), ("←", "left", 1), ("↓", "down", 1), ("→", "right", 1)]),
]


# ============================================================================
# EMBEDDED CONTROLLER (SAFE OPERATIONS)
# ============================================================================

class ECController:
    """Safe Embedded Controller interface for fan control."""

    def __init__(self):
        self.acpi_available = os.path.exists('/proc/acpi/call')
        self.ec_sysfs_available = os.path.exists('/sys/kernel/debug/ec/ec0/io')
        self._last_mode = None
        self._backup_state = {}

    def check_requirements(self) -> Tuple[bool, List[str]]:
        """Check if all requirements are met for EC access."""
        errors = []

        if os.geteuid() != 0:
            errors.append("Root access required (run with sudo)")

        if not self.acpi_available:
            errors.append("acpi_call module not loaded (sudo modprobe acpi_call)")

        if not self.ec_sysfs_available:
            errors.append("ec_sys module not loaded (sudo modprobe ec_sys)")

        return len(errors) == 0, errors

    def _acpi_call(self, data: int) -> int:
        """Execute ACPI call with error handling."""
        if not self.acpi_available:
            raise RuntimeError("acpi_call not available")

        try:
            subprocess.check_call(
                f"echo '\\_SB.AMW0.WMBC 0 4 {data}' > /proc/acpi/call",
                shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            raw = subprocess.check_output(
                "cat /proc/acpi/call", shell=True, stderr=subprocess.DEVNULL
            )[:-1].decode()

            try:
                return int(raw, 16)
            except ValueError:
                # Handle different return formats
                for ch in ('{', '}'):
                    raw = raw.replace(ch, '')
                parts = raw.split(', ')
                parts.reverse()
                return int.from_bytes(bytearray(int(x, 16) for x in parts), 'big')
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ACPI call failed: {e}")

    def ec_read(self, addr: int) -> int:
        """Safely read from EC address."""
        if addr < 0 or addr > 65535:
            raise ValueError(f"Invalid EC address: {addr}")
        return self._acpi_call(0x10000000000 + addr) & 0xFF

    def ec_write(self, addr: int, val: int) -> bool:
        """Safely write to EC address with validation."""
        # Validate address
        if addr < 0 or addr > 65535:
            raise ValueError(f"Invalid EC address: {addr}")

        # Validate value
        if val < 0 or val > 255:
            raise ValueError(f"Invalid EC value: {val} (must be 0-255)")

        # Extra safety for fan control addresses
        if addr == EC_ADDR_MAFAN_CONTROL:
            if val not in [FanMode.INTELLIGENT, FanMode.TURBO, FanMode.BOOST, FanMode.CUSTOM]:
                raise ValueError(f"Invalid fan mode: {val}")

        if addr >= EC_ADDR_CPU_FAN_L1_PWM and addr <= EC_ADDR_CPU_FAN_L1_PWM + 4:
            if val > MAX_PWM:
                raise ValueError(f"PWM value {val} exceeds safe maximum ({MAX_PWM})")

        try:
            self._acpi_call((val << 16) + addr)
            return True
        except Exception as e:
            print(f"EC write error: {e}")
            return False

    def read_status(self) -> Optional[Dict]:
        """Read fan status from sysfs."""
        if not self.ec_sysfs_available:
            return None

        try:
            with open('/sys/kernel/debug/ec/ec0/io', 'rb') as f:
                data = f.read()

            mode_byte = data[EC_FAN_MODE]
            mode_map = {
                0x00: "Intelligent",
                0x10: "Turbo",
                0x40: "Boost",
                0xA0: "Custom"
            }

            return {
                "cpu_rpm": data[EC_CPU_RPM_LO] | (data[EC_CPU_RPM_HI] << 8),
                "gpu_rpm": data[EC_GPU_RPM_LO] | (data[EC_GPU_RPM_HI] << 8),
                "cpu_temp": data[EC_CPU_TEMP],
                "fan_duty": data[EC_FAN_DUTY],
                "fan_mode": mode_map.get(mode_byte, f"Unknown (0x{mode_byte:02X})"),
                "fan_mode_id": mode_byte,
            }
        except Exception as e:
            print(f"Error reading EC status: {e}")
            return None

    def set_fan_mode(self, mode: int) -> bool:
        """Set fan mode with safety checks."""
        if mode not in [FanMode.INTELLIGENT, FanMode.TURBO, FanMode.BOOST, FanMode.CUSTOM]:
            raise ValueError(f"Invalid fan mode: {mode}")

        # Backup current state before changing
        self._backup_state['last_mode'] = mode

        return self.ec_write(EC_ADDR_MAFAN_CONTROL, mode)

    def set_custom_curve(self, l1: int, l2: int, l3: int, l4: int, l5: int) -> bool:
        """Set custom fan curve with validation."""
        # Validate all values
        values = [l1, l2, l3, l4, l5]
        for i, v in enumerate(values):
            if v < MIN_PWM or v > MAX_PWM:
                raise ValueError(f"Level {i+1} PWM value {v} out of range ({MIN_PWM}-{MAX_PWM})")

        # First set mode to custom
        if not self.set_fan_mode(FanMode.CUSTOM):
            return False

        # Write each level
        for i, pwm in enumerate(values):
            if not self.ec_write(EC_ADDR_CPU_FAN_L1_PWM + i, pwm):
                return False

        return True

    def set_fan_percent(self, percent: int) -> bool:
        """Set fan to a fixed percentage."""
        if percent < 0 or percent > 100:
            raise ValueError(f"Invalid percentage: {percent}")

        pwm = min(int(percent * 2), MAX_PWM)
        return self.set_custom_curve(pwm, pwm, pwm, pwm, pwm)

    def apply_preset(self, preset_name: str) -> bool:
        """Apply a safe preset curve."""
        if preset_name not in SAFE_PRESETS:
            raise ValueError(f"Unknown preset: {preset_name}")

        values = SAFE_PRESETS[preset_name]
        return self.set_custom_curve(*values)

    def restore_safe_mode(self) -> bool:
        """Restore to intelligent/safe mode."""
        return self.set_fan_mode(FanMode.INTELLIGENT)


# ============================================================================
# RGB KEYBOARD CONTROLLER
# ============================================================================

class KeyboardController:
    """Keyboard RGB controller."""

    def __init__(self):
        self.led_paths: Dict[int, Path] = {}
        self._cache_led_paths()

    def _cache_led_paths(self):
        base = Path(SYSFS_BASE)
        zone0_path = base / LED_PREFIX
        if zone0_path.exists():
            self.led_paths[0] = zone0_path
        for i in range(1, TOTAL_ZONES):
            path = base / f"{LED_PREFIX}_{i}"
            if path.exists():
                self.led_paths[i] = path

    def get_all_zones(self) -> List[int]:
        return list(self.led_paths.keys())

    def write_zone(self, zone: int, r: int, g: int, b: int) -> bool:
        if zone not in self.led_paths:
            return False
        r = max(0, min(MAX_BRIGHTNESS, r))
        g = max(0, min(MAX_BRIGHTNESS, g))
        b = max(0, min(MAX_BRIGHTNESS, b))
        try:
            (self.led_paths[zone] / "multi_intensity").write_text(f"{r} {g} {b}")
            return True
        except:
            return False

    def set_all(self, r: int, g: int, b: int):
        for zone in self.led_paths:
            self.write_zone(zone, r, g, b)

    def get_zone_color(self, zone: int) -> Optional[Tuple[int, int, int]]:
        if zone not in self.led_paths:
            return None
        try:
            content = (self.led_paths[zone] / "multi_intensity").read_text().strip()
            parts = content.split()
            if len(parts) == 3:
                return (int(parts[0]), int(parts[1]), int(parts[2]))
        except:
            pass
        return None


# ============================================================================
# GTK4 CSS HELPER - Using widget-specific names to avoid global style conflicts
# ============================================================================

# Global CSS provider (loaded once)
_global_css_provider = None
_css_initialized = False

def init_global_css():
    """Initialize global CSS provider with base styles."""
    global _global_css_provider, _css_initialized
    if _css_initialized:
        return

    _global_css_provider = Gtk.CssProvider()
    base_css = b"""
    .key-button {
        border-radius: 4px;
        padding: 2px;
        min-width: 22px;
        min-height: 22px;
        font-size: 10px;
        font-weight: bold;
    }
    .key-button:selected {
        border: 2px solid #ffffff;
    }
    .color-swatch {
        min-width: 24px;
        min-height: 20px;
        border-radius: 3px;
        border: 1px solid #555;
    }
    """
    _global_css_provider.load_from_data(base_css)
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(),
        _global_css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
    _css_initialized = True


# Counter for unique widget names
_widget_counter = 0

def get_unique_name(prefix: str = "widget") -> str:
    """Generate a unique widget name."""
    global _widget_counter
    _widget_counter += 1
    return f"{prefix}_{_widget_counter}"


def apply_widget_css(widget: Gtk.Widget, css: str):
    """Apply CSS to a specific widget using its name as selector.

    Reuses a single per-widget CssProvider instead of creating a new one on
    every call.  The old code added a fresh provider to the global display on
    every style update, so after a handful of key-clicks hundreds of competing
    providers accumulated – causing selection highlights to appear unreliable
    and slowing GTK down progressively.
    """
    # Ensure the widget has a unique name
    widget_name = widget.get_name()
    if not widget_name or widget_name == widget.__class__.__name__:
        widget_name = get_unique_name("w")
        widget.set_name(widget_name)

    # Create the provider once per widget and register it with the display
    # once.  On subsequent calls we just update the existing provider's data.
    if not hasattr(widget, '_css_provider'):
        widget._css_provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            widget._css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

    # Update the existing provider – no new provider is added to the display
    widget._css_provider.load_from_data(css.encode())


# ============================================================================
# CAIRO HELPER - rounded_rectangle fix
# ============================================================================

def draw_rounded_rect(cr, x, y, width, height, radius):
    """Draw a rounded rectangle - Cairo doesn't have this built-in."""
    # Ensure valid dimensions
    width = max(1, width)
    height = max(1, height)
    radius = max(0, min(radius, min(width, height) / 2))

    cr.new_sub_path()
    cr.arc(x + radius, y + radius, radius, math.pi, 3 * math.pi / 2)
    cr.arc(x + width - radius, y + radius, radius, 3 * math.pi / 2, 2 * math.pi)
    cr.arc(x + width - radius, y + height - radius, radius, 0, math.pi / 2)
    cr.arc(x + radius, y + height - radius, radius, math.pi / 2, math.pi)
    cr.close_path()


# ============================================================================
# FAN DISPLAY WIDGET
# ============================================================================

class FanDisplayWidget(Gtk.Box):
    """Visual representation of fans with controls."""

    def __init__(self, ec_controller: ECController):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.ec = ec_controller
        self.cpu_rpm = 0
        self.gpu_rpm = 0
        self.cpu_temp = 0
        self.fan_duty = 0
        self.fan_mode = "Unknown"
        self.rotation_angle = 0
        self._build_ui()

    def _build_ui(self):
        # Title
        title = Gtk.Label()
        title.set_markup("<b>🌡️ Fan Control</b>")
        title.set_halign(Gtk.Align.START)
        self.append(title)

        # Drawing area for fans
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(400, 160)
        self.drawing_area.set_draw_func(self._draw_fans)
        self.drawing_area.set_halign(Gtk.Align.CENTER)
        self.append(self.drawing_area)

        # Status labels
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        status_box.set_halign(Gtk.Align.CENTER)

        self.cpu_label = Gtk.Label(label="CPU: -- RPM")
        self.gpu_label = Gtk.Label(label="GPU: -- RPM")
        self.temp_label = Gtk.Label(label="Temp: --°C")
        self.mode_label = Gtk.Label(label="Mode: --")

        status_box.append(self.cpu_label)
        status_box.append(self.gpu_label)
        status_box.append(self.temp_label)
        status_box.append(self.mode_label)
        self.append(status_box)

        # Fan mode buttons (Auto and Boost only)
        modes_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        modes_box.set_halign(Gtk.Align.CENTER)

        for mode, label in [("auto", "Auto"), ("boost", "Boost")]:
            btn = Gtk.Button(label=label)
            btn.connect("clicked", self._on_mode_clicked, mode)
            modes_box.append(btn)

        self.append(modes_box)

        # Warning
        warning = Gtk.Label()
        warning.set_markup("<small>⚠️ Fan control writes to EC. Changes are reversible.</small>")
        warning.set_halign(Gtk.Align.CENTER)
        self.append(warning)

    def _draw_fans(self, area, cr, width, height):
        # Background
        cr.set_source_rgb(0.08, 0.08, 0.1)
        cr.rectangle(0, 0, width, height)
        cr.fill()

        # Draw two fans
        fan_size = min(55, height // 3)
        center_y = height // 2

        # CPU Fan (left)
        cpu_x = width // 4
        self._draw_single_fan(cr, cpu_x, center_y, fan_size,
                              self.cpu_rpm, "#3498db", "CPU")

        # GPU Fan (right)
        gpu_x = 3 * width // 4
        self._draw_single_fan(cr, gpu_x, center_y, fan_size,
                              self.gpu_rpm, "#9b59b6", "GPU")

        # Connection line
        cr.set_source_rgba(0.3, 0.3, 0.35, 0.5)
        cr.set_line_width(1)
        cr.move_to(cpu_x + fan_size + 10, center_y)
        cr.line_to(gpu_x - fan_size - 10, center_y)
        cr.stroke()

    def _draw_single_fan(self, cr, x, y, size, rpm, color, label):
        # Fan housing with rounded rectangle (FIXED)
        cr.set_source_rgb(0.15, 0.15, 0.18)
        draw_rounded_rect(cr, x - size - 5, y - size - 5, size * 2 + 10, size * 2 + 10, 8)
        cr.fill()

        # Fan circle
        cr.set_source_rgb(0.2, 0.2, 0.25)
        cr.arc(x, y, size, 0, 2 * math.pi)
        cr.fill()

        # Fan blades with rotation
        cr.save()
        cr.translate(x, y)
        cr.rotate(self.rotation_angle)

        num_blades = 7
        cr.set_source_rgb(0.4, 0.4, 0.45)
        for i in range(num_blades):
            angle = i * 2 * math.pi / num_blades
            cr.move_to(0, 0)
            cr.arc(0, 0, size * 0.8, angle - 0.15, angle + 0.15)
            cr.line_to(0, 0)
            cr.fill()

        cr.restore()

        # Center hub
        cr.set_source_rgb(0.12, 0.12, 0.15)
        cr.arc(x, y, size * 0.2, 0, 2 * math.pi)
        cr.fill()

        # Label
        cr.set_source_rgb(0.7, 0.7, 0.7)
        cr.set_font_size(10)
        extents = cr.text_extents(label)
        cr.move_to(x - extents.width/2, y - size - 15)
        cr.show_text(label)

        # RPM
        cr.set_font_size(11)
        rpm_text = f"{rpm} RPM"
        extents = cr.text_extents(rpm_text)
        cr.move_to(x - extents.width/2, y + size + 18)
        cr.show_text(rpm_text)

    def _on_mode_clicked(self, _, mode: str):
        try:
            mode_map = {
                "auto": FanMode.INTELLIGENT,
                "boost": FanMode.BOOST,
            }
            if mode in mode_map:
                self.ec.set_fan_mode(mode_map[mode])
        except Exception as e:
            print(f"Error: {e}")

    def update_status(self, status: Dict):
        if status:
            self.cpu_rpm = status.get('cpu_rpm', 0)
            self.gpu_rpm = status.get('gpu_rpm', 0)
            self.cpu_temp = status.get('cpu_temp', 0)
            self.fan_duty = status.get('fan_duty', 0)
            self.fan_mode = status.get('fan_mode', 'Unknown')

            # Update labels
            self.cpu_label.set_text(f"CPU: {self.cpu_rpm} RPM")
            self.gpu_label.set_text(f"GPU: {self.gpu_rpm} RPM")
            self.temp_label.set_text(f"Temp: {self.cpu_temp}°C")
            self.mode_label.set_text(f"Mode: {self.fan_mode}")

            # Update rotation angle for animation
            self.rotation_angle += 0.2 * (self.cpu_rpm / 1000)

            self.drawing_area.queue_draw()


# ============================================================================
# KEYBOARD WIDGET - Per-key color display
# ============================================================================

class KeyButton(Gtk.Button):
    """A single key button that shows its current color."""

    def __init__(self, label: str, key_name: str, zone: Optional[int]):
        super().__init__(label=label if label else " ")
        self.key_name = key_name
        self.zone = zone
        self.current_color = (0, 0, 0)
        self.selected = False

        # Set a unique name for this button for CSS targeting
        self.set_name(get_unique_name("key"))
        self.add_css_class("key-button")
        self.update_style()

    def set_color(self, r: int, g: int, b: int):
        """Set the color of this key (updates display only)."""
        self.current_color = (r, g, b)
        self.update_style()

    def set_selected(self, selected: bool):
        """Set selection state."""
        self.selected = selected
        self.update_style()

    def update_style(self):
        """Update the button's visual style based on color and selection."""
        r, g, b = self.current_color
        # Convert 0-50 range to 0-255 for display
        r_disp = int(r * 5.1)
        g_disp = int(g * 5.1)
        b_disp = int(b * 5.1)

        # Border styling based on selection
        border_color = "#ffffff" if self.selected else "#555555"
        border_width = "2px" if self.selected else "1px"

        # Text color based on background brightness
        brightness = (r + g + b) / 3
        text_color = "#000000" if brightness > 25 else "#ffffff"

        # Build CSS for this specific widget using its name
        widget_name = self.get_name()
        css = f"""
        #{widget_name} {{
            background-color: rgb({r_disp}, {g_disp}, {b_disp});
            color: {text_color};
            border: {border_width} solid {border_color};
            border-radius: 4px;
            padding: 2px;
            min-width: 22px;
            min-height: 22px;
            font-size: 10px;
            font-weight: bold;
        }}
        """
        apply_widget_css(self, css)


class KeyboardWidget(Gtk.Box):
    """Visual keyboard widget showing per-key colors."""

    def __init__(self, controller: KeyboardController):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.controller = controller
        self.key_buttons: Dict[str, KeyButton] = {}
        self.selected_keys: Set[str] = set()
        self.selection_callback = None
        self._build_keyboard()

    def _build_keyboard(self):
        """Build the keyboard layout."""
        for row_name, keys in KEYBOARD_LAYOUT:
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
            row_box.set_halign(Gtk.Align.CENTER)
            for label, key_name, width in keys:
                if key_name == "":
                    # Empty spacer
                    spacer = Gtk.Box()
                    spacer.set_size_request(int(width * 28), 28)
                    row_box.append(spacer)
                else:
                    zone = KEY_MAP.get(key_name)
                    btn = KeyButton(label, key_name, zone)
                    btn.set_size_request(int(width * 28), 28)
                    btn.connect("clicked", self._on_key_clicked)
                    self.key_buttons[key_name] = btn
                    row_box.append(btn)
            self.append(row_box)

        # Load current colors from hardware
        self.refresh_colors()

    def _on_key_clicked(self, button: KeyButton):
        """Handle key click - toggle selection."""
        key_name = button.key_name
        if key_name in self.selected_keys:
            self.selected_keys.remove(key_name)
            button.set_selected(False)
        else:
            self.selected_keys.add(key_name)
            button.set_selected(True)

        if self.selection_callback:
            self.selection_callback(self.selected_keys)

    def clear_selection(self):
        """Clear all selections."""
        self.selected_keys.clear()
        for btn in self.key_buttons.values():
            btn.set_selected(False)

    def select_all(self):
        """Select all keys."""
        self.selected_keys = set(self.key_buttons.keys())
        for btn in self.key_buttons.values():
            btn.set_selected(True)

    def refresh_colors(self):
        """Refresh colors from hardware - show actual per-key colors."""
        for key_name, btn in self.key_buttons.items():
            if btn.zone is not None:
                color = self.controller.get_zone_color(btn.zone)
                if color:
                    btn.set_color(*color)

    def set_selected_keys_color(self, r: int, g: int, b: int):
        """Set color of selected keys (writes to hardware and updates display)."""
        for key_name in self.selected_keys:
            btn = self.key_buttons.get(key_name)
            if btn and btn.zone is not None:
                self.controller.write_zone(btn.zone, r, g, b)
                btn.set_color(r, g, b)
            # Write any secondary zones for this key (e.g. Tab spans zones 42+63)
            for extra_zone in SECONDARY_ZONES.get(key_name, []):
                self.controller.write_zone(extra_zone, r, g, b)

    def set_all_keys_color(self, r: int, g: int, b: int):
        """Set all keys to a color (writes to hardware and updates display)."""
        self.controller.set_all(r, g, b)
        for btn in self.key_buttons.values():
            if btn.zone is not None:
                btn.set_color(r, g, b)

    def set_sector_color(self, sector_name: str, r: int, g: int, b: int):
        """Set a sector to a color (writes to hardware and updates display)."""
        if sector_name.lower() in SECTORS:
            keys = SECTORS[sector_name.lower()]
            for key_name in keys:
                btn = self.key_buttons.get(key_name)
                if btn and btn.zone is not None:
                    self.controller.write_zone(btn.zone, r, g, b)
                    btn.set_color(r, g, b)
                # Write any secondary zones for this key
                for extra_zone in SECONDARY_ZONES.get(key_name, []):
                    self.controller.write_zone(extra_zone, r, g, b)

    def get_all_zones(self) -> List[int]:
        """Get all zone IDs that have buttons."""
        zones = []
        for btn in self.key_buttons.values():
            if btn.zone is not None:
                zones.append(btn.zone)
        return zones

    def set_zone_color(self, zone: int, r: int, g: int, b: int):
        """Set a specific zone color."""
        self.controller.write_zone(zone, r, g, b)
        # Update the button display
        for btn in self.key_buttons.values():
            if btn.zone == zone:
                btn.set_color(r, g, b)


# ============================================================================
# ANIMATION ENGINE
# ============================================================================

class AnimationEngine:
    """Handles keyboard RGB animations.

    All sysfs writes run in a dedicated background thread so the GTK main
    thread (and therefore the UI) is never blocked.  The only GTK call made
    from the background thread is GLib.idle_add(), which is explicitly
    thread-safe and schedules refresh_colors() back on the main thread.
    """

    # Target frame interval in seconds.  50 ms ≈ 20 FPS which looks smooth
    # without hammering sysfs.
    FRAME_INTERVAL = 0.05

    def __init__(self, controller: KeyboardController, keyboard_widget: KeyboardWidget):
        self.controller = controller
        self.keyboard = keyboard_widget
        self.animation_type = "fire"

        # Pre-compute zone list for animation
        self.zones = list(range(126))

        # Threading primitives
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, animation_type: str = "fire"):
        """Start (or restart) an animation."""
        self.stop()  # Cleanly stop any running animation first
        self.animation_type = animation_type
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the animation and wait for the thread to finish."""
        if self._thread and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join(timeout=1.0)  # Should finish within one frame
        self._thread = None

    # ------------------------------------------------------------------
    # Background thread – NO direct GTK calls here except GLib.idle_add
    # ------------------------------------------------------------------

    def _loop(self):
        """Main animation loop running in the background thread."""
        frame = 0
        while not self._stop_event.is_set():
            t_start = time.monotonic()

            if self.animation_type == "fire":
                self._fire_frame(frame)
            elif self.animation_type == "rainbow":
                self._rainbow_frame(frame)
            elif self.animation_type == "wave":
                self._wave_frame(frame)

            frame += 1

            # Refresh the GUI preview every 3 frames.
            # GLib.idle_add is safe to call from any thread.
            if frame % 3 == 0:
                GLib.idle_add(self.keyboard.refresh_colors)

            # Sleep for the remainder of the frame interval so we don't
            # busy-spin and eat CPU between sysfs writes.
            elapsed = time.monotonic() - t_start
            sleep_for = self.FRAME_INTERVAL - elapsed
            if sleep_for > 0:
                # Use the stop_event as a sleeper so stop() wakes us up
                # immediately instead of waiting out the full interval.
                self._stop_event.wait(timeout=sleep_for)

    # ------------------------------------------------------------------
    # Frame calculators (pure computation + sysfs writes, no GTK)
    # ------------------------------------------------------------------

    def _fire_frame(self, frame: int):
        """Fire animation - flames rising from bottom."""
        fire_colors = [
            (50, 0, 0),   # Deep red
            (50, 10, 0),  # Red-orange
            (50, 20, 0),  # Orange
            (50, 30, 0),  # Orange-yellow
            (50, 40, 0),  # Yellow-orange
            (50, 50, 0),  # Yellow
            (30, 10, 0),  # Dark orange
            (20, 5, 0),   # Dark red
        ]

        for zone in self.zones:
            key_name = ZONE_TO_KEY.get(zone, "")

            if key_name in ["f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8",
                            "f9", "f10", "f11", "f12", "esc", "prtsc", "del"]:
                row = 0
            elif key_name in ["1", "2", "3", "4", "5", "6", "7", "8", "9",
                               "0", "minus", "equal", "backspace", "grave"]:
                row = 1
            elif key_name in ["q", "w", "e", "r", "t", "y", "u", "i", "o",
                               "p", "lbracket", "rbracket", "backslash", "tab"]:
                row = 2
            elif key_name in ["a", "s", "d", "f", "g", "h", "j", "k", "l",
                               "semicolon", "quote", "enter", "caps"]:
                row = 3
            elif key_name in ["z", "x", "c", "v", "b", "n", "m", "comma",
                               "period", "slash", "lshift", "rshift"]:
                row = 4
            elif key_name in ["lctrl", "fn", "lwin", "lalt", "space", "ralt", "rctrl"]:
                row = 5
            else:
                row = 3

            flicker = random.randint(-2, 2)
            intensity = (5 - row) / 5.0
            intensity = max(0.0, min(1.0, intensity + random.uniform(-0.1, 0.1)))
            color_idx = int(intensity * (len(fire_colors) - 1))
            color_idx = max(0, min(len(fire_colors) - 1, color_idx + flicker))
            r, g, b = fire_colors[color_idx]

            if random.random() < 0.1 and row >= 3:
                r = min(50, r + random.randint(0, 10))
                g = min(50, g + random.randint(0, 15))

            self.controller.write_zone(zone, r, g, b)

    def _rainbow_frame(self, frame: int):
        """Rainbow wave animation."""
        for zone in self.zones:
            hue = (zone * 3 + frame * 2) % 360
            h = hue / 60.0
            i = int(h)
            f = h - i

            if i == 0:
                r, g, b = 50, int(50 * f), 0
            elif i == 1:
                r, g, b = int(50 * (1 - f)), 50, 0
            elif i == 2:
                r, g, b = 0, 50, int(50 * f)
            elif i == 3:
                r, g, b = 0, int(50 * (1 - f)), 50
            elif i == 4:
                r, g, b = int(50 * f), 0, 50
            else:
                r, g, b = 50, 0, int(50 * (1 - f))

            self.controller.write_zone(zone, r, g, b)

    def _wave_frame(self, frame: int):
        """Color wave animation."""
        for zone in self.zones:
            wave = math.sin((zone * 0.2) + (frame * 0.15))
            wave = (wave + 1) / 2

            r = int(50 * wave)
            g = int(25 * (1 - wave))
            b = int(50 * abs(math.sin(frame * 0.1)))

            self.controller.write_zone(zone, r, g, b)


# ============================================================================
# COLOR PICKER WIDGET
# ============================================================================

class ColorPickerWidget(Gtk.Box):
    """Color picker with sliders and preset swatches."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.current_color = (50, 50, 50)
        self.color_callback = None
        self._build_widgets()

    def _build_widgets(self):
        # Color preview
        self.preview = Gtk.DrawingArea()
        self.preview.set_size_request(80, 30)
        self.preview.set_draw_func(self._draw_preview)
        self.append(self.preview)

        # RGB Sliders
        for color, label in [("r", "R:"), ("g", "G:"), ("b", "B:")]:
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            lbl = Gtk.Label(label=label)
            lbl.set_width_chars(2)
            adj = Gtk.Adjustment(value=50, lower=0, upper=50, step_increment=1)
            slider = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
            slider.set_hexpand(True)
            slider.set_size_request(100, -1)
            slider.connect("value-changed", self._on_slider_changed)
            setattr(self, f"{color}_adjustment", adj)
            box.append(lbl)
            box.append(slider)
            self.append(box)

        # Color preset swatches - STATIC colors, don't change when clicked
        preset_grid = Gtk.Grid()
        preset_grid.set_column_spacing(3)
        preset_grid.set_row_spacing(3)

        popular = ["red", "orange", "yellow", "green", "cyan", "blue",
                   "purple", "violet", "pink", "white", "gray", "off"]

        for i, color_name in enumerate(popular):
            btn = Gtk.Button()
            btn.set_size_request(24, 20)
            btn.set_tooltip_text(color_name.capitalize())
            btn.connect("clicked", self._on_preset_clicked, color_name)

            # Set a unique name and static styling for this color swatch
            btn.set_name(get_unique_name("swatch"))
            btn.add_css_class("color-swatch")

            # Apply static color styling - this won't change
            r, g, b = COLORS.get(color_name, (0, 0, 0))
            r_disp = int(r * 5.1)
            g_disp = int(g * 5.1)
            b_disp = int(b * 5.1)

            widget_name = btn.get_name()
            css = f"""
            #{widget_name} {{
                background-color: rgb({r_disp}, {g_disp}, {b_disp});
                min-width: 24px;
                min-height: 20px;
                border-radius: 3px;
                border: 1px solid #555;
            }}
            """
            apply_widget_css(btn, css)
            preset_grid.attach(btn, i % 6, i // 6, 1, 1)

        self.append(preset_grid)

    def _draw_preview(self, area, cr, width, height):
        """Draw the color preview."""
        r, g, b = self.current_color
        cr.set_source_rgb(r / 50, g / 50, b / 50)
        cr.rectangle(0, 0, width, height)
        cr.fill()

    def _on_slider_changed(self, _):
        """Handle slider change."""
        r = int(self.r_adjustment.get_value())
        g = int(self.g_adjustment.get_value())
        b = int(self.b_adjustment.get_value())
        self.current_color = (r, g, b)
        self.preview.queue_draw()
        if self.color_callback:
            self.color_callback(r, g, b)

    def _on_preset_clicked(self, _, color_name: str):
        """Handle preset click - update the picker, don't change the swatch."""
        if color_name in COLORS:
            self.set_color(*COLORS[color_name])

    def set_color(self, r: int, g: int, b: int):
        """Set the current color."""
        self.current_color = (r, g, b)
        self.r_adjustment.set_value(r)
        self.g_adjustment.set_value(g)
        self.b_adjustment.set_value(b)
        self.preview.queue_draw()

    def get_color(self) -> Tuple[int, int, int]:
        """Get the current color."""
        return self.current_color


# ============================================================================
# MAIN APPLICATION WINDOW - ALL IN ONE PANEL
# ============================================================================

class SystemControllerGui(Gtk.ApplicationWindow):
    """Main window - Keyboard on top, Fans below, all in one panel."""

    def __init__(self, app):
        super().__init__(application=app, title="RGB + Fan Controller")
        self.set_default_size(900, 900)

        # Initialize global CSS
        init_global_css()

        # Initialize controllers
        self.kbd_controller = KeyboardController()
        self.ec_controller = ECController()

        # Animation engine (will be initialized after keyboard widget)
        self.animation_engine = None

        # Check EC requirements
        self.ec_available, self.ec_errors = self.ec_controller.check_requirements()

        # Status update timer
        self.status_timeout_id = None

        self._build_ui()

        # Start status updates
        if self.ec_available:
            self._start_status_updates()

    def _build_ui(self):
        # Main scrollable container
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        main_box.set_margin_top(8)
        main_box.set_margin_bottom(8)
        main_box.set_margin_start(8)
        main_box.set_margin_end(8)

        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        title = Gtk.Label()
        title.set_markup("<big><b>🖥️ RGB + Fan Controller</b></big>")
        header.append(title)

        self.status_label = Gtk.Label(label="Ready")
        self.status_label.set_hexpand(True)
        self.status_label.set_halign(Gtk.Align.END)
        header.append(self.status_label)

        main_box.append(header)

        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.append(sep)

        # ============ RGB KEYBOARD SECTION ============
        rgb_frame = Gtk.Frame(label="⌨️ Keyboard RGB")
        rgb_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        rgb_box.set_margin_start(6)
        rgb_box.set_margin_end(6)
        rgb_box.set_margin_top(6)
        rgb_box.set_margin_bottom(6)

        # Left: Keyboard
        kbd_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

        instr = Gtk.Label()
        instr.set_markup("<small>Click keys to select, then apply color. Colors shown are actual key colors.</small>")
        instr.set_halign(Gtk.Align.START)
        kbd_box.append(instr)

        self.keyboard = KeyboardWidget(self.kbd_controller)
        self.keyboard.selection_callback = self._on_key_selection
        kbd_box.append(self.keyboard)

        # Initialize animation engine
        self.animation_engine = AnimationEngine(self.kbd_controller, self.keyboard)

        # Selection controls
        sel_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.selection_label = Gtk.Label(label="No keys selected")
        self.selection_label.set_hexpand(True)
        sel_box.append(self.selection_label)

        sel_all = Gtk.Button(label="All")
        sel_all.connect("clicked", lambda _: self.keyboard.select_all())
        sel_box.append(sel_all)

        sel_clear = Gtk.Button(label="Clear")
        sel_clear.connect("clicked", lambda _: self.keyboard.clear_selection())
        sel_box.append(sel_clear)

        # Refresh button to reload colors from hardware
        refresh_btn = Gtk.Button(label="🔄 Refresh")
        refresh_btn.connect("clicked", lambda _: self.keyboard.refresh_colors())
        sel_box.append(refresh_btn)

        kbd_box.append(sel_box)
        rgb_box.append(kbd_box)

        # Right: Color controls
        ctrl_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        ctrl_box.set_size_request(200, -1)

        # Color picker
        color_frame = Gtk.Frame(label="Color")
        self.color_picker = ColorPickerWidget()
        self.color_picker.set_margin_start(6)
        self.color_picker.set_margin_end(6)
        self.color_picker.set_margin_top(6)
        self.color_picker.set_margin_bottom(6)
        color_frame.set_child(self.color_picker)
        ctrl_box.append(color_frame)

        # Apply buttons
        apply_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.apply_selected_btn = Gtk.Button(label="Selected")
        self.apply_selected_btn.set_sensitive(False)
        self.apply_selected_btn.connect("clicked", self._on_apply_selected)
        apply_box.append(self.apply_selected_btn)

        apply_all_btn = Gtk.Button(label="All Keys")
        apply_all_btn.connect("clicked", self._on_apply_all)
        apply_box.append(apply_all_btn)

        ctrl_box.append(apply_box)

        # Sectors
        sector_frame = Gtk.Frame(label="Sectors")
        sector_grid = Gtk.Grid()
        sector_grid.set_column_spacing(3)
        sector_grid.set_row_spacing(3)
        sector_grid.set_margin_start(6)
        sector_grid.set_margin_end(6)
        sector_grid.set_margin_top(6)
        sector_grid.set_margin_bottom(6)

        sectors_list = ["wasd", "arrows", "letters", "numbers", "function", "numpad"]
        for i, sector in enumerate(sectors_list):
            btn = Gtk.Button(label=sector.capitalize())
            btn.connect("clicked", self._on_sector_clicked, sector)
            sector_grid.attach(btn, i % 3, i // 3, 1, 1)

        sector_frame.set_child(sector_grid)
        ctrl_box.append(sector_frame)

        # Quick colors
        quick_frame = Gtk.Frame(label="Quick Colors (All Keys)")
        quick_grid = Gtk.Grid()
        quick_grid.set_column_spacing(3)
        quick_grid.set_row_spacing(3)
        quick_grid.set_margin_start(6)
        quick_grid.set_margin_end(6)
        quick_grid.set_margin_top(6)
        quick_grid.set_margin_bottom(6)

        quick_colors = ["red", "blue", "green", "cyan", "purple", "white"]
        for i, color_name in enumerate(quick_colors):
            btn = Gtk.Button(label=color_name.capitalize())
            btn.connect("clicked", self._on_quick_color, color_name)
            quick_grid.attach(btn, i % 3, i // 3, 1, 1)

        quick_frame.set_child(quick_grid)
        ctrl_box.append(quick_frame)

        # Off button
        off_btn = Gtk.Button(label="💡 Turn Off All")
        off_btn.connect("clicked", self._on_turn_off)
        ctrl_box.append(off_btn)

        # Animations
        anim_frame = Gtk.Frame(label="🔥 Animations")
        anim_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        anim_box.set_margin_start(6)
        anim_box.set_margin_end(6)
        anim_box.set_margin_top(6)
        anim_box.set_margin_bottom(6)

        # Animation buttons row
        anim_btns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)

        fire_btn = Gtk.Button(label="🔥 Fire")
        fire_btn.connect("clicked", lambda _: self._on_animation_start("fire"))
        anim_btns.append(fire_btn)

        rainbow_btn = Gtk.Button(label="🌈 Rainbow")
        rainbow_btn.connect("clicked", lambda _: self._on_animation_start("rainbow"))
        anim_btns.append(rainbow_btn)

        wave_btn = Gtk.Button(label="🌊 Wave")
        wave_btn.connect("clicked", lambda _: self._on_animation_start("wave"))
        anim_btns.append(wave_btn)

        anim_box.append(anim_btns)

        # Stop animation button
        stop_btn = Gtk.Button(label="⏹️ Stop Animation")
        stop_btn.connect("clicked", self._on_animation_stop)
        anim_box.append(stop_btn)

        anim_frame.set_child(anim_box)
        ctrl_box.append(anim_frame)

        rgb_box.append(ctrl_box)
        rgb_frame.set_child(rgb_box)
        main_box.append(rgb_frame)

        # Separator
        sep2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.append(sep2)

        # ============ FAN CONTROL SECTION ============
        fan_frame = Gtk.Frame(label="🌡️ Fan Control")
        fan_frame.set_margin_top(4)

        self.fan_display = FanDisplayWidget(self.ec_controller)
        self.fan_display.set_margin_start(6)
        self.fan_display.set_margin_end(6)
        self.fan_display.set_margin_top(6)
        self.fan_display.set_margin_bottom(6)

        # Show EC errors if any
        if not self.ec_available and self.ec_errors:
            error_label = Gtk.Label()
            error_label.set_markup(f"<span foreground='orange'>⚠️ Fan control unavailable: {', '.join(self.ec_errors)}</span>")
            error_label.set_margin_top(6)
            self.fan_display.append(error_label)

        fan_frame.set_child(self.fan_display)
        main_box.append(fan_frame)

        scroll.set_child(main_box)
        self.set_child(scroll)

    def _on_key_selection(self, selected: Set[str]):
        """Handle key selection change."""
        count = len(selected)
        if count == 0:
            self.selection_label.set_text("No keys selected")
            self.apply_selected_btn.set_sensitive(False)
        else:
            self.selection_label.set_text(f"{count} key(s) selected")
            self.apply_selected_btn.set_sensitive(True)

    def _on_apply_selected(self, _):
        """Apply current color to selected keys."""
        r, g, b = self.color_picker.get_color()
        self.keyboard.set_selected_keys_color(r, g, b)

    def _on_apply_all(self, _):
        """Apply current color to all keys."""
        r, g, b = self.color_picker.get_color()
        self.keyboard.set_all_keys_color(r, g, b)

    def _on_sector_clicked(self, _, sector: str):
        """Apply current color to a sector."""
        r, g, b = self.color_picker.get_color()
        self.keyboard.set_sector_color(sector, r, g, b)

    def _on_quick_color(self, _, color_name: str):
        """Quick color - set all keys to this color."""
        if color_name in COLORS:
            r, g, b = COLORS[color_name]
            self.color_picker.set_color(r, g, b)
            self.keyboard.set_all_keys_color(r, g, b)

    def _on_turn_off(self, _):
        """Turn off all keys and stop any animation."""
        if self.animation_engine:
            self.animation_engine.stop()
        self.keyboard.set_all_keys_color(0, 0, 0)

    def _on_animation_start(self, animation_type: str):
        """Start an animation."""
        if self.animation_engine:
            self.animation_engine.start(animation_type)

    def _on_animation_stop(self, _):
        """Stop the current animation."""
        if self.animation_engine:
            self.animation_engine.stop()

    def _start_status_updates(self):
        """Start periodic fan status updates."""
        self._update_fan_status()
        self.status_timeout_id = GLib.timeout_add(1000, self._update_fan_status)

    def _update_fan_status(self) -> bool:
        """Update fan status display."""
        if self.ec_available:
            try:
                status = self.ec_controller.read_status()
                if status:
                    self.fan_display.update_status(status)
                    self.status_label.set_text(f"CPU: {status['cpu_temp']}°C | {status['fan_mode']}")
            except Exception as e:
                print(f"Status update error: {e}")
        return True  # Continue timer

    def do_close_request(self) -> bool:
        """Clean up on close."""
        if self.status_timeout_id:
            GLib.source_remove(self.status_timeout_id)
        if self.animation_engine:
            self.animation_engine.stop()
        return False


# ============================================================================
# APPLICATION
# ============================================================================

class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='com.tongfang.rgb-fan-controller')

    def do_activate(self):
        win = SystemControllerGui(self)
        win.present()


def main():
    app = App()
    app.run(None)


if __name__ == "__main__":
    main()
