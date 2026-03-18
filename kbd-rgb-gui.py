#!/usr/bin/env python3
"""
Tongfang/AiStone Keyboard RGB Controller - GUI Edition
=======================================================
A beautiful graphical interface for controlling ITE 8291 keyboard RGB.

Author: Aineasg
License: MIT

Requirements:
- Python 3 with PyGObject (GTK4)
- Installation: sudo pacman -S python-gobject gtk4 (Arch)
                sudo apt install python3-gi gir1.2-gtk-4.0 (Debian/Ubuntu)
"""

import os
import sys
import json
import signal
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set

try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, Gdk, GLib, Pango
except ImportError:
    print("ERROR: PyGObject not found!")
    print("\nInstall dependencies:")
    print("  Arch/Manjaro:    sudo pacman -S python-gobject gtk4")
    print("  Debian/Ubuntu:   sudo apt install python3-gi gir1.2-gtk-4.0")
    print("  Fedora:          sudo dnf install python3-gobject gtk4")
    print("  openSUSE:        sudo zypper install python3-gobject gtk4")
    sys.exit(1)

# ============================================================================
# CONFIGURATION
# ============================================================================

SYSFS_BASE = "/sys/class/leds"
LED_PREFIX = "rgb:kbd_backlight"
MAX_BRIGHTNESS = 50
TOTAL_ZONES = 126
PID_FILE = "/tmp/kbd-rgb.pid"
STATE_FILE = "/tmp/kbd-rgb-state.json"

# Color presets
COLORS = {
    "off": (0, 0, 0), "black": (0, 0, 0),
    "red": (50, 0, 0), "green": (0, 50, 0), "blue": (0, 0, 50),
    "yellow": (50, 50, 0), "purple": (50, 0, 50), "cyan": (0, 50, 50),
    "white": (50, 50, 50), "orange": (50, 25, 0), "pink": (50, 0, 25),
    "lime": (25, 50, 0), "teal": (0, 50, 25), "navy": (0, 0, 35),
    "violet": (35, 0, 50), "magenta": (50, 0, 45), "indigo": (25, 0, 50),
    "lavender": (40, 20, 50), "plum": (40, 10, 40),
    "amber": (50, 35, 0), "gold": (50, 40, 0), "lemon": (50, 50, 10),
    "citrine": (50, 40, 10), "copper": (50, 25, 10), "bronze": (45, 30, 10),
    "coral": (50, 25, 20), "peach": (50, 35, 25), "tangerine": (50, 30, 0),
    "cream": (50, 50, 35),
    "forest": (0, 35, 15), "emerald": (0, 45, 25), "jade": (0, 40, 30),
    "mint": (20, 50, 35), "chartreuse": (35, 50, 0),
    "sky": (20, 40, 50), "cobalt": (0, 25, 50), "sapphire": (10, 20, 50),
    "royal": (15, 15, 50), "midnight": (5, 5, 30),
    "turquoise": (0, 45, 45),
    "crimson": (50, 0, 10), "scarlet": (50, 5, 0), "ruby": (50, 0, 20),
    "cherry": (50, 10, 15), "rose": (50, 15, 25), "salmon": (50, 30, 30),
    "hot_pink": (50, 10, 35),
    "neon_green": (20, 50, 10), "neon_blue": (10, 30, 50),
    "neon_pink": (50, 10, 40), "neon_orange": (50, 30, 0),
    "ice": (30, 45, 50), "sunset": (50, 25, 10), "ocean": (0, 30, 45),
    "silver": (35, 35, 35), "gray": (25, 25, 25), "grey": (25, 25, 25),
    "dim": (10, 10, 10), "dark": (5, 5, 5),
}

KEY_MAP = {
    "ctrl": 0, "lctrl": 0, "fn": 2, "lwin": 3, "win": 3,
    "lalt": 4, "alt": 4, "space": 7, "ralt": 10, "altgr": 10,
    "rctrl": 11, "copilot": 12,
    "left": 13, "up": 14, "right": 15, "down": 18,
    "numpad_0": 16, "numpad_dot": 17,
    "lshift": 22, "shift": 22, "backslash_left": 23,
    "z": 24, "x": 25, "c": 26, "v": 27, "b": 28, "n": 29, "m": 30,
    "comma": 31, ",": 31, "period": 32, ".": 32, "slash": 33, "/": 33,
    "rshift": 35,
    "numpad_1": 36, "numpad_2": 37, "numpad_3": 38, "numpad_enter": 39,
    "capstk": 42, "tab": 42,
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

ZONE_TO_KEY = {v: k for k, v in KEY_MAP.items()}

SECTORS = {
    "wasd": ["w", "a", "s", "d"],
    "wasdqe": ["w", "a", "s", "d", "q", "e"],
    "arrows": ["up", "down", "left", "right"],
    "qwerty": ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
    "qwertyuiop": ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
    "asdfghjkl": ["a", "s", "d", "f", "g", "h", "j", "k", "l"],
    "zxcvbnm": ["z", "x", "c", "v", "b", "n", "m"],
    "letters": ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "a", "s", "d", "f", "g", "h", "j", "k", "l", "z", "x", "c", "v", "b", "n", "m"],
    "numbers": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
    "function": ["f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12", "esc"],
    "numpad": ["numpad_0", "numpad_1", "numpad_2", "numpad_3", "numpad_4", "numpad_5", "numpad_6", "numpad_7", "numpad_8", "numpad_9", "numpad_dot", "numpad_slash", "numpad_multiply", "numpad_minus", "numpad_plus", "numpad_enter", "numlock"],
    "modifiers": ["lctrl", "lshift", "lalt", "lwin", "rctrl", "rshift", "ralt", "fn"],
    "space": ["space"], "enter": ["enter"], "tab": ["tab"], "esc": ["esc"],
    "backspace": ["backspace"], "navigation": ["home", "end", "pgup", "pgdn", "del"],
}

ROWS = {
    "row_fn": [105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124],
    "row_num": [84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 98],
    "row_qwerty": [42, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 55, 77],
    "row_home": [44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54],
    "row_zxcv": [22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 35],
    "row_bottom": [0, 2, 3, 4, 7, 10, 11, 12],
    "row_arrows": [13, 14, 15, 18],
}

KEYBOARD_LAYOUT = [
    ("fn", [
        ("Esc", "esc", 1), ("F1", "f1", 1), ("F2", "f2", 1), ("F3", "f3", 1), ("F4", "f4", 1),
        ("F5", "f5", 1), ("F6", "f6", 1), ("F7", "f7", 1), ("F8", "f8", 1),
        ("F9", "f9", 1), ("F10", "f10", 1), ("F11", "f11", 1), ("F12", "f12", 1),
        ("PrtSc", "prtsc", 1), ("ScrLk", "scrlock", 1), ("Del", "del", 1),
    ]),
    ("num", [
        ("`", "grave", 1), ("1", "1", 1), ("2", "2", 1), ("3", "3", 1), ("4", "4", 1),
        ("5", "5", 1), ("6", "6", 1), ("7", "7", 1), ("8", "8", 1), ("9", "9", 1),
        ("0", "0", 1), ("-", "minus", 1), ("=", "equal", 1), ("⌫", "backspace", 2),
    ]),
    ("qwerty", [
        ("Tab", "tab", 1.5), ("Q", "q", 1), ("W", "w", 1), ("E", "e", 1), ("R", "r", 1),
        ("T", "t", 1), ("Y", "y", 1), ("U", "u", 1), ("I", "i", 1), ("O", "o", 1),
        ("P", "p", 1), ("[", "lbracket", 1), ("]", "rbracket", 1), ("\\", "backslash", 1.5),
    ]),
    ("home", [
        ("Caps", "capstk", 1.75), ("A", "a", 1), ("S", "s", 1), ("D", "d", 1), ("F", "f", 1),
        ("G", "g", 1), ("H", "h", 1), ("J", "j", 1), ("K", "k", 1), ("L", "l", 1),
        (";", "semicolon", 1), ("'", "quote", 1), ("Enter", "enter", 2.25),
    ]),
    ("zxcv", [
        ("Shift", "lshift", 2.25), ("\\", "backslash_left", 1), ("Z", "z", 1), ("X", "x", 1),
        ("C", "c", 1), ("V", "v", 1), ("B", "b", 1), ("N", "n", 1), ("M", "m", 1),
        (",", "comma", 1), (".", "period", 1), ("/", "slash", 1), ("Shift", "rshift", 2.75),
    ]),
    ("bottom", [
        ("Ctrl", "lctrl", 1.25), ("Fn", "fn", 1), ("Win", "lwin", 1.25), ("Alt", "lalt", 1.25),
        ("", "space", 6.25), ("Alt", "ralt", 1.25), ("Ctrl", "rctrl", 1.25), ("Copilot", "copilot", 1),
    ]),
    ("arrows", [
        ("", "", 13), ("↑", "up", 1), ("", "", 2),
    ]),
    ("arrows2", [
        ("", "", 12), ("←", "left", 1), ("↓", "down", 1), ("→", "right", 1),
    ]),
]


class KeyboardController:
    def __init__(self):
        self.led_paths: Dict[int, Path] = {}
        self._cache_led_paths()
        self._running = True
    
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
        except Exception as e:
            print(f"Error writing zone {zone}: {e}")
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


def apply_css(widget: Gtk.Widget, css: str):
    provider = Gtk.CssProvider()
    provider.load_from_data(css.encode())
    widget.get_style_context().add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)


class KeyButton(Gtk.Button):
    def __init__(self, label: str, key_name: str, zone: Optional[int]):
        super().__init__(label=label if label else " ")
        self.key_name = key_name
        self.zone = zone
        self.current_color = (0, 0, 0)
        self.selected = False
        self.add_css_class("key-button")
        self.update_style()
    
    def set_color(self, r: int, g: int, b: int):
        self.current_color = (r, g, b)
        self.update_style()
    
    def set_selected(self, selected: bool):
        self.selected = selected
        self.update_style()
    
    def update_style(self):
        r, g, b = self.current_color
        r_disp = int(r * 255 / 50)
        g_disp = int(g * 255 / 50)
        b_disp = int(b * 255 / 50)
        border_color = "#ffffff" if self.selected else "#555555"
        border_width = "2px" if self.selected else "1px"
        brightness = (r + g + b) / 3
        text_color = "#000000" if brightness > 25 else "#ffffff"
        css = f"""
        .key-button {{
            background-color: rgb({r_disp}, {g_disp}, {b_disp});
            color: {text_color};
            border: {border_width} solid {border_color};
            border-radius: 4px;
            padding: 2px;
            min-width: 24px;
            min-height: 24px;
            font-size: 11px;
            font-weight: bold;
        }}
        """
        apply_css(self, css)


class KeyboardWidget(Gtk.Box):
    def __init__(self, controller: KeyboardController):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.controller = controller
        self.key_buttons: Dict[str, KeyButton] = {}
        self.selected_keys: Set[str] = set()
        self.selection_callback = None
        self._build_keyboard()
    
    def _build_keyboard(self):
        for row_name, keys in KEYBOARD_LAYOUT:
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
            row_box.set_halign(Gtk.Align.CENTER)
            for label, key_name, width in keys:
                if key_name == "":
                    spacer = Gtk.Box()
                    spacer.set_size_request(int(width * 32), 32)
                    row_box.append(spacer)
                else:
                    zone = KEY_MAP.get(key_name)
                    btn = KeyButton(label, key_name, zone)
                    btn.set_size_request(int(width * 32), 32)
                    btn.connect("clicked", self._on_key_clicked)
                    self.key_buttons[key_name] = btn
                    row_box.append(btn)
            self.append(row_box)
        self.refresh_colors()
    
    def _on_key_clicked(self, button: KeyButton):
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
        self.selected_keys.clear()
        for btn in self.key_buttons.values():
            btn.set_selected(False)
    
    def select_all(self):
        self.selected_keys = set(self.key_buttons.keys())
        for btn in self.key_buttons.values():
            btn.set_selected(True)
    
    def refresh_colors(self):
        for key_name, btn in self.key_buttons.items():
            if btn.zone is not None:
                color = self.controller.get_zone_color(btn.zone)
                if color:
                    btn.current_color = color
                    btn.update_style()
    
    def set_selected_keys_color(self, r: int, g: int, b: int):
        for key_name in self.selected_keys:
            btn = self.key_buttons.get(key_name)
            if btn and btn.zone is not None:
                self.controller.write_zone(btn.zone, r, g, b)
                btn.set_color(r, g, b)
    
    def set_all_keys_color(self, r: int, g: int, b: int):
        self.controller.set_all(r, g, b)
        for btn in self.key_buttons.values():
            if btn.zone is not None:
                btn.set_color(r, g, b)
    
    def set_sector_color(self, sector_name: str, r: int, g: int, b: int):
        if sector_name.lower() in SECTORS:
            keys = SECTORS[sector_name.lower()]
            for key_name in keys:
                btn = self.key_buttons.get(key_name)
                if btn and btn.zone is not None:
                    self.controller.write_zone(btn.zone, r, g, b)
                    btn.set_color(r, g, b)
    
    def set_row_color(self, row_name: str, r: int, g: int, b: int):
        if row_name.lower() in ROWS:
            zones = ROWS[row_name.lower()]
            for zone in zones:
                self.controller.write_zone(zone, r, g, b)
                key_name = ZONE_TO_KEY.get(zone)
                if key_name and key_name in self.key_buttons:
                    self.key_buttons[key_name].set_color(r, g, b)


class ColorPickerWidget(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.current_color = (50, 50, 50)
        self.color_callback = None
        self._build_widgets()
    
    def _build_widgets(self):
        self.preview = Gtk.DrawingArea()
        self.preview.set_size_request(100, 40)
        self.preview.set_draw_func(self._draw_preview)
        self.append(self.preview)
        
        slider_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        
        for color, label in [("r", "R:"), ("g", "G:"), ("b", "B:")]:
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            lbl = Gtk.Label(label=label)
            lbl.set_width_chars(2)
            adj = Gtk.Adjustment(value=50, lower=0, upper=50, step_increment=1)
            slider = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
            slider.set_hexpand(True)
            slider.connect("value-changed", self._on_slider_changed)
            setattr(self, f"{color}_adjustment", adj)
            box.append(lbl)
            box.append(slider)
            slider_box.append(box)
        
        self.append(slider_box)
        
        preset_label = Gtk.Label()
        preset_label.set_markup("<b>Color Presets</b>")
        self.append(preset_label)
        
        preset_grid = Gtk.Grid()
        preset_grid.set_column_spacing(4)
        preset_grid.set_row_spacing(4)
        
        popular_colors = [
            "red", "orange", "yellow", "lime", "green", "cyan",
            "blue", "navy", "violet", "purple", "magenta", "pink",
            "white", "silver", "gray", "off", "gold", "coral",
        ]
        
        for i, color_name in enumerate(popular_colors):
            color = COLORS.get(color_name, (0, 0, 0))
            btn = Gtk.Button()
            btn.set_size_request(32, 28)
            btn.set_tooltip_text(color_name.capitalize())
            btn.connect("clicked", self._on_preset_clicked, color_name)
            r, g, b = color
            css = f"button {{ background-color: rgb({r*5}, {g*5}, {b*5}); min-height: 24px; }}"
            apply_css(btn, css)
            preset_grid.attach(btn, i % 6, i // 6, 1, 1)
        
        self.append(preset_grid)
        
        entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        entry_label = Gtk.Label(label="Custom:")
        self.color_entry = Gtk.Entry()
        self.color_entry.set_placeholder_text("e.g., 25,30,40")
        self.color_entry.connect("activate", self._on_entry_activate)
        entry_box.append(entry_label)
        entry_box.append(self.color_entry)
        self.append(entry_box)
    
    def _draw_preview(self, area, cr, width, height):
        r, g, b = self.current_color
        cr.set_source_rgb(r / 50, g / 50, b / 50)
        cr.rectangle(0, 0, width, height)
        cr.fill()
    
    def _on_slider_changed(self, _):
        r = int(self.r_adjustment.get_value())
        g = int(self.g_adjustment.get_value())
        b = int(self.b_adjustment.get_value())
        self.current_color = (r, g, b)
        self.preview.queue_draw()
        if self.color_callback:
            self.color_callback(r, g, b)
    
    def _on_preset_clicked(self, _, color_name: str):
        if color_name in COLORS:
            self.set_color(*COLORS[color_name])
    
    def _on_entry_activate(self, _):
        text = self.color_entry.get_text().strip()
        try:
            parts = [int(x.strip()) for x in text.replace(",", " ").split()]
            if len(parts) == 3:
                self.set_color(*[max(0, min(50, p)) for p in parts])
        except:
            pass
    
    def set_color(self, r: int, g: int, b: int):
        self.current_color = (r, g, b)
        self.r_adjustment.set_value(r)
        self.g_adjustment.set_value(g)
        self.b_adjustment.set_value(b)
        self.preview.queue_draw()
        if self.color_callback:
            self.color_callback(r, g, b)
    
    def get_color(self) -> Tuple[int, int, int]:
        return self.current_color


class KbdRgbGui(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Keyboard RGB Controller")
        self.set_default_size(950, 750)
        
        if os.geteuid() != 0:
            dialog = Gtk.AlertDialog()
            dialog.set_message("Root privileges required")
            dialog.set_detail("Please run with: sudo kbd-rgb-gui")
            dialog.set_buttons(["OK"])
            dialog.choose(self, None, None, None)
            sys.exit(1)
        
        self.controller = KeyboardController()
        self._build_ui()
        self._check_animation_status()
    
    def _build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        main_box.set_margin_start(10)
        main_box.set_margin_end(10)
        
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        title = Gtk.Label()
        title.set_markup("<big><b>⌨️ Keyboard RGB Controller</b></big>")
        header.append(title)
        
        self.status_label = Gtk.Label(label="Ready")
        self.status_label.set_hexpand(True)
        self.status_label.set_halign(Gtk.Align.END)
        header.append(self.status_label)
        main_box.append(header)
        
        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        # Left panel - Keyboard
        left_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        keyboard_label = Gtk.Label()
        keyboard_label.set_markup("<b>Virtual Keyboard</b>")
        keyboard_label.set_halign(Gtk.Align.START)
        left_panel.append(keyboard_label)
        
        instr = Gtk.Label()
        instr.set_markup("<small>Click keys to select, then choose a color.</small>")
        instr.set_halign(Gtk.Align.START)
        left_panel.append(instr)
        
        scroll_window = Gtk.ScrolledWindow()
        scroll_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll_window.set_min_content_height(320)
        scroll_window.set_vexpand(True)
        
        self.keyboard = KeyboardWidget(self.controller)
        self.keyboard.selection_callback = self._on_selection_changed
        scroll_window.set_child(self.keyboard)
        left_panel.append(scroll_window)
        
        sel_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.selection_label = Gtk.Label(label="No keys selected")
        self.selection_label.set_hexpand(True)
        sel_box.append(self.selection_label)
        
        select_all_btn = Gtk.Button(label="Select All")
        select_all_btn.connect("clicked", lambda _: self.keyboard.select_all())
        sel_box.append(select_all_btn)
        
        clear_btn = Gtk.Button(label="Clear")
        clear_btn.connect("clicked", lambda _: self.keyboard.clear_selection())
        sel_box.append(clear_btn)
        left_panel.append(sel_box)
        
        content.append(left_panel)
        
        # Right panel - Controls
        right_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        right_panel.set_size_request(280, -1)
        
        # Color picker
        color_frame = Gtk.Frame(label="Color Picker")
        self.color_picker = ColorPickerWidget()
        self.color_picker.set_margin_start(8)
        self.color_picker.set_margin_end(8)
        self.color_picker.set_margin_top(8)
        self.color_picker.set_margin_bottom(8)
        color_frame.set_child(self.color_picker)
        right_panel.append(color_frame)
        
        # Action buttons
        action_frame = Gtk.Frame(label="Apply Color")
        action_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        action_box.set_margin_start(8)
        action_box.set_margin_end(8)
        action_box.set_margin_top(8)
        action_box.set_margin_bottom(8)
        
        btn_box1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.apply_selected_btn = Gtk.Button(label="Apply to Selected")
        self.apply_selected_btn.connect("clicked", self._on_apply_selected)
        self.apply_selected_btn.set_sensitive(False)
        btn_box1.append(self.apply_selected_btn)
        action_box.append(btn_box1)
        
        btn_box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        apply_all_btn = Gtk.Button(label="Apply to All")
        apply_all_btn.connect("clicked", self._on_apply_all)
        btn_box2.append(apply_all_btn)
        off_btn = Gtk.Button(label="All Off")
        off_btn.connect("clicked", self._on_all_off)
        btn_box2.append(off_btn)
        action_box.append(btn_box2)
        action_frame.set_child(action_box)
        right_panel.append(action_frame)
        
        # Sectors
        sector_frame = Gtk.Frame(label="Quick Sectors")
        sector_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        sector_box.set_margin_start(8)
        sector_box.set_margin_end(8)
        sector_box.set_margin_top(8)
        sector_box.set_margin_bottom(8)
        
        sector_grid = Gtk.Grid()
        sector_grid.set_column_spacing(4)
        sector_grid.set_row_spacing(4)
        for i, sector in enumerate(["wasd", "qwerty", "letters", "numbers", "function", "numpad", "arrows", "modifiers"]):
            btn = Gtk.Button(label=sector.upper())
            btn.connect("clicked", self._on_sector_clicked, sector)
            sector_grid.attach(btn, i % 2, i // 2, 1, 1)
        sector_box.append(sector_grid)
        sector_frame.set_child(sector_box)
        right_panel.append(sector_frame)
        
        # Rows
        row_frame = Gtk.Frame(label="Quick Rows")
        row_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        row_box.set_margin_start(8)
        row_box.set_margin_end(8)
        row_box.set_margin_top(8)
        row_box.set_margin_bottom(8)
        
        row_grid = Gtk.Grid()
        row_grid.set_column_spacing(4)
        row_grid.set_row_spacing(4)
        for i, row in enumerate(["row_fn", "row_num", "row_qwerty", "row_home", "row_zxcv", "row_bottom"]):
            btn = Gtk.Button(label=row.replace("row_", "").upper())
            btn.connect("clicked", self._on_row_clicked, row)
            row_grid.attach(btn, i % 2, i // 2, 1, 1)
        row_box.append(row_grid)
        row_frame.set_child(row_box)
        right_panel.append(row_frame)
        
        # Animations
        anim_frame = Gtk.Frame(label="Animations")
        anim_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        anim_box.set_margin_start(8)
        anim_box.set_margin_end(8)
        anim_box.set_margin_top(8)
        anim_box.set_margin_bottom(8)
        
        anim_grid = Gtk.Grid()
        anim_grid.set_column_spacing(4)
        anim_grid.set_row_spacing(4)
        for i, anim in enumerate(["rainbow", "breathe", "wave", "party", "fire", "matrix", "stars", "lightning", "pulse"]):
            btn = Gtk.Button(label=anim.capitalize())
            btn.connect("clicked", self._on_animation_clicked, anim)
            anim_grid.attach(btn, i % 3, i // 3, 1, 1)
        anim_box.append(anim_grid)
        
        speed_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        speed_label = Gtk.Label(label="Speed:")
        self.speed_adjustment = Gtk.Adjustment(value=1.0, lower=0.25, upper=3.0, step_increment=0.25)
        self.speed_slider = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.speed_adjustment)
        self.speed_slider.set_hexpand(True)
        speed_box.append(speed_label)
        speed_box.append(self.speed_slider)
        anim_box.append(speed_box)
        
        ctrl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.stop_btn = Gtk.Button(label="⏹ Stop")
        self.stop_btn.connect("clicked", self._on_stop_animation)
        ctrl_box.append(self.stop_btn)
        self.daemon_btn = Gtk.CheckButton(label="Background")
        ctrl_box.append(self.daemon_btn)
        anim_box.append(ctrl_box)
        
        anim_frame.set_child(anim_box)
        right_panel.append(anim_frame)
        
        content.append(right_panel)
        main_box.append(content)
        
        zone_count = len(self.controller.get_all_zones())
        status_text = f"Zones detected: {zone_count}" if zone_count > 0 else "⚠️ No LED zones detected!"
        self.zone_status = Gtk.Label(label=status_text)
        main_box.append(self.zone_status)
        
        self.set_child(main_box)
    
    def _on_selection_changed(self, selected_keys):
        count = len(selected_keys)
        self.selection_label.set_text(f"{count} key(s) selected" if count > 0 else "No keys selected")
        self.apply_selected_btn.set_sensitive(count > 0)
    
    def _on_apply_selected(self, _):
        r, g, b = self.color_picker.get_color()
        self.keyboard.set_selected_keys_color(r, g, b)
        self._stop_animation_if_running()
        self.status_label.set_text(f"Applied to {len(self.keyboard.selected_keys)} keys")
    
    def _on_apply_all(self, _):
        r, g, b = self.color_picker.get_color()
        self.keyboard.set_all_keys_color(r, g, b)
        self._stop_animation_if_running()
        self.status_label.set_text("Applied to all keys")
    
    def _on_all_off(self, _):
        self.keyboard.set_all_keys_color(0, 0, 0)
        self._stop_animation_if_running()
        self.status_label.set_text("All lights off")
    
    def _on_sector_clicked(self, _, sector):
        r, g, b = self.color_picker.get_color()
        self.keyboard.set_sector_color(sector, r, g, b)
        self._stop_animation_if_running()
        self.status_label.set_text(f"Applied to: {sector}")
    
    def _on_row_clicked(self, _, row):
        r, g, b = self.color_picker.get_color()
        self.keyboard.set_row_color(row, r, g, b)
        self._stop_animation_if_running()
        self.status_label.set_text(f"Applied to: {row}")
    
    def _on_animation_clicked(self, _, animation):
        speed = self.speed_adjustment.get_value()
        color = self.color_picker.get_color()
        if self.daemon_btn.get_active():
            self._start_daemon_animation(animation, speed)
        else:
            dialog = Gtk.AlertDialog()
            dialog.set_message("Foreground Animation")
            dialog.set_detail(f"Starting {animation} animation.\n\nFor background mode, check 'Background' option.")
            dialog.set_buttons(["Cancel", "OK"])
            def on_response(dialog, result):
                if dialog.choose_finish(result) == 1:
                    subprocess.run(["kbd-rgb", "animate", animation, "--speed", str(speed)])
            dialog.choose(self, None, on_response, None)
    
    def _stop_animation_if_running(self):
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, 'r') as f:
                    pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
                os.remove(PID_FILE)
                if os.path.exists(STATE_FILE):
                    os.remove(STATE_FILE)
            except:
                pass
    
    def _start_daemon_animation(self, animation, speed):
        self._stop_animation_if_running()
        try:
            subprocess.run(["kbd-rgb", "animate", animation, "--daemon", "--speed", str(speed)], check=True)
            self.status_label.set_text(f"Started {animation} in background")
        except:
            self.status_label.set_text("Error: kbd-rgb CLI not found")
    
    def _on_stop_animation(self, _):
        self._stop_animation_if_running()
        self.status_label.set_text("Animation stopped")
        self.keyboard.refresh_colors()
    
    def _check_animation_status(self):
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, 'r') as f:
                    pid = int(f.read().strip())
                os.kill(pid, 0)
                if os.path.exists(STATE_FILE):
                    with open(STATE_FILE, 'r') as f:
                        state = json.load(f)
                    self.status_label.set_text(f"Animation: {state.get('animation', 'unknown')}")
            except:
                pass


class KbdRgbApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='com.tongfang.kbd-rgb-gui')
    
    def do_activate(self):
        win = KbdRgbGui(self)
        win.present()


def main():
    app = KbdRgbApp()
    app.run(sys.argv)


if __name__ == "__main__":
    main()
