#!/usr/bin/env python3
"""
Tongfang/AiStone Keyboard RGB Controller
=========================================
A fast, comprehensive RGB control program for ITE 8291 keyboard controller.

Hardware: ITE Device(8291) - USB ID: 048d:600b
Zones: 126 (0-125)
Color Range: 0-50 per channel (NOT 0-255!)

Author: Aineasg
License: MIT
"""

import os
import sys
import time
import signal
import argparse
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Tuple
import random

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

# Key zone mapping
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
    "tab": 42,
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

# Sectors
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

# Rows
ROWS = {
    "row_fn": [105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124],
    "row_num": [84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 98],
    "row_qwerty": [42, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 55, 77],
    "row_home": [44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54],
    "row_zxcv": [22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 35],
    "row_bottom": [0, 2, 3, 4, 7, 10, 11, 12],
    "row_arrows": [13, 14, 15, 18],
}


# ============================================================================
# LED CONTROLLER
# ============================================================================

class KeyboardController:
    def __init__(self):
        self.led_paths: Dict[int, Path] = {}
        self._cache_led_paths()
        self._running = True
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        self._running = False
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        sys.exit(0)
    
    def _cache_led_paths(self):
        base = Path(SYSFS_BASE)
        zone0_path = base / LED_PREFIX
        if zone0_path.exists():
            self.led_paths[0] = zone0_path
        for i in range(1, TOTAL_ZONES):
            path = base / f"{LED_PREFIX}_{i}"
            if path.exists():
                self.led_paths[i] = path
    
    def _write_zone(self, zone: int, r: int, g: int, b: int) -> bool:
        if zone not in self.led_paths:
            return False
        r, g, b = max(0, min(MAX_BRIGHTNESS, r)), max(0, min(MAX_BRIGHTNESS, g)), max(0, min(MAX_BRIGHTNESS, b))
        try:
            (self.led_paths[zone] / "multi_intensity").write_text(f"{r} {g} {b}")
            return True
        except:
            return False
    
    def _write_frame(self, zone_colors: Dict[int, Tuple[int, int, int]]):
        def write_one(item):
            zone, (r, g, b) = item
            return self._write_zone(zone, r, g, b)
        with ThreadPoolExecutor(max_workers=32) as executor:
            list(executor.map(write_one, zone_colors.items()))
    
    def get_all_zones(self) -> List[int]:
        return list(self.led_paths.keys())
    
    def set_all(self, r: int, g: int, b: int):
        zone_colors = {z: (r, g, b) for z in self.led_paths}
        self._write_frame(zone_colors)
    
    def set_zones(self, zones: List[int], r: int, g: int, b: int):
        zone_colors = {z: (r, g, b) for z in zones if z in self.led_paths}
        self._write_frame(zone_colors)
    
    def set_key(self, key_name: str, r: int, g: int, b: int) -> bool:
        key = key_name.lower().replace(" ", "_").replace("-", "_")
        if key in KEY_MAP:
            return self._write_zone(KEY_MAP[key], r, g, b)
        return False
    
    def set_keys(self, key_names: List[str], r: int, g: int, b: int):
        zones = [KEY_MAP[k.lower().replace(" ", "_")] for k in key_names if k.lower().replace(" ", "_") in KEY_MAP]
        self.set_zones(zones, r, g, b)
    
    def set_sector(self, sector_name: str, r: int, g: int, b: int):
        sector = sector_name.lower().replace("-", "_")
        if sector in SECTORS:
            self.set_keys(SECTORS[sector], r, g, b)
    
    def set_row(self, row_name: str, r: int, g: int, b: int):
        row = row_name.lower().replace("-", "_")
        if row in ROWS:
            self.set_zones(ROWS[row], r, g, b)
    
    def _hsv_to_rgb(self, h: float, s: float = 1.0, v: float = 1.0) -> Tuple[int, int, int]:
        h = h % 360
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c
        if h < 60: r, g, b = c, x, 0
        elif h < 120: r, g, b = x, c, 0
        elif h < 180: r, g, b = 0, c, x
        elif h < 240: r, g, b = 0, x, c
        elif h < 300: r, g, b = x, 0, c
        else: r, g, b = c, 0, x
        return (int((r + m) * MAX_BRIGHTNESS), int((g + m) * MAX_BRIGHTNESS), int((b + m) * MAX_BRIGHTNESS))
    
    # Animations
    def animate_rainbow(self, speed: float = 1.0):
        all_zones = sorted(self.get_all_zones())
        total = len(all_zones)
        zone_positions = {z: i / total for i, z in enumerate(all_zones)}
        hue_offset = 0.0
        while self._running:
            frame = {}
            for zone in all_zones:
                hue = (zone_positions[zone] * 360 + hue_offset) % 360
                frame[zone] = self._hsv_to_rgb(hue, 1.0, 1.0)
            self._write_frame(frame)
            hue_offset = (hue_offset + 4) % 360
            time.sleep(0.025 / speed)
    
    def animate_breathe(self, r: int, g: int, b: int, speed: float = 1.0):
        import math
        step = 0
        while self._running:
            ratio = (math.sin(step * 0.05) + 1) / 2
            self.set_all(int(r * ratio), int(g * ratio), int(b * ratio))
            step += 1
            time.sleep(0.02 / speed)
    
    def animate_wave(self, color: Tuple[int, int, int], speed: float = 1.0):
        import math
        all_zones = sorted(self.get_all_zones())
        total = len(all_zones)
        offset = 0.0
        while self._running:
            frame = {}
            for i, zone in enumerate(all_zones):
                pos = (i / total + offset) % 1.0
                wave = 0.5 + 0.5 * math.sin(pos * math.pi * 4)
                frame[zone] = (int(color[0] * wave), int(color[1] * wave), int(color[2] * wave))
            self._write_frame(frame)
            offset = (offset + 0.02) % 1.0
            time.sleep(0.02 / speed)
    
    def animate_party(self, speed: float = 1.0):
        all_zones = self.get_all_zones()
        while self._running:
            frame = {}
            for zone in all_zones:
                hue = random.random() * 360
                frame[zone] = self._hsv_to_rgb(hue, 1.0, 1.0)
            self._write_frame(frame)
            time.sleep(0.08 / speed)
    
    def animate_fire(self, speed: float = 1.0):
        all_zones = self.get_all_zones()
        while self._running:
            frame = {}
            for zone in all_zones:
                choice = random.random()
                if choice < 0.4:
                    frame[zone] = (50, random.randint(0, 10), 0)
                elif choice < 0.7:
                    frame[zone] = (50, random.randint(10, 25), 0)
                else:
                    frame[zone] = (50, random.randint(25, 40), 0)
            self._write_frame(frame)
            time.sleep(0.04 / speed)
    
    def animate_matrix(self, speed: float = 1.0):
        all_zones = sorted(self.get_all_zones())
        total = len(all_zones)
        columns = 14
        drops = [random.randint(0, total - 1) for _ in range(columns)]
        brightness = {z: 0 for z in all_zones}
        while self._running:
            for z in all_zones:
                brightness[z] = max(0, brightness[z] - 3)
            for i, drop in enumerate(drops):
                if drop < total:
                    brightness[all_zones[drop]] = 50
                    for t in range(1, 5):
                        if drop - t >= 0:
                            brightness[all_zones[drop - t]] = max(brightness[all_zones[drop - t]], 50 - t * 10)
                drops[i] = (drop + 2) % total
                if random.random() < 0.03:
                    drops[i] = random.randint(0, total // 2)
            frame = {z: (0, brightness[z], 0) for z in all_zones}
            self._write_frame(frame)
            time.sleep(0.03 / speed)
    
    def animate_stars(self, speed: float = 1.0):
        all_zones = self.get_all_zones()
        brightness = {z: 0 for z in all_zones}
        while self._running:
            for z in all_zones:
                if random.random() < 0.02:
                    brightness[z] = random.randint(30, 50)
                else:
                    brightness[z] = max(0, brightness[z] - 2)
            frame = {z: (brightness[z], brightness[z], min(50, brightness[z] + 5)) for z in all_zones}
            self._write_frame(frame)
            time.sleep(0.03 / speed)
    
    def animate_lightning(self, speed: float = 1.0):
        while self._running:
            self.set_all(0, 0, 5)
            time.sleep(random.uniform(0.5, 2.0) / speed)
            for _ in range(random.randint(1, 3)):
                self.set_all(50, 50, 50)
                time.sleep(0.02)
                self.set_all(0, 0, 10)
                time.sleep(0.05)
    
    def animate_pulse(self, speed: float = 1.0):
        hue = 0
        while self._running:
            r, g, b = self._hsv_to_rgb(hue, 1.0, 1.0)
            self.set_all(r, g, b)
            hue = (hue + 3) % 360
            time.sleep(0.02 / speed)


# ============================================================================
# DAEMON FUNCTIONS
# ============================================================================

def stop_animation():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            print(f"\033[33mStopped animation (PID {pid})\033[0m")
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
        except ProcessLookupError:
            print("\033[33mNo running animation found\033[0m")
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
        except Exception as e:
            print(f"\033[31mError: {e}\033[0m")
    else:
        print("\033[33mNo animation running\033[0m")

def start_daemon(animation_name: str, color: Tuple[int, int, int], speed: float):
    stop_animation()
    time.sleep(0.2)
    
    pid = os.fork()
    if pid > 0:
        print(f"\033[32mStarted {animation_name} animation in background (PID {pid})\033[0m")
        print(f"\033[36mUse 'kbd-rgb stop' to stop it\033[0m")
        return
    
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    
    state = {"animation": animation_name, "color": color, "speed": speed}
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)
    
    controller = KeyboardController()
    
    animations = {
        "rainbow": lambda: controller.animate_rainbow(speed),
        "breathe": lambda: controller.animate_breathe(*color, speed),
        "wave": lambda: controller.animate_wave(color, speed),
        "party": lambda: controller.animate_party(speed),
        "fire": lambda: controller.animate_fire(speed),
        "matrix": lambda: controller.animate_matrix(speed),
        "stars": lambda: controller.animate_stars(speed),
        "lightning": lambda: controller.animate_lightning(speed),
        "pulse": lambda: controller.animate_pulse(speed),
    }
    
    if animation_name in animations:
        animations[animation_name]()
    
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)


# ============================================================================
# CLI
# ============================================================================

def parse_color(color_str: str) -> Tuple[int, int, int]:
    if color_str.lower() in COLORS:
        return COLORS[color_str.lower()]
    for sep in [",", " "]:
        if sep in color_str:
            parts = [int(x.strip()) for x in color_str.split(sep) if x.strip()]
            if len(parts) == 3:
                return tuple(max(0, min(MAX_BRIGHTNESS, p)) for p in parts)
    print(f"\033[31mInvalid color: {color_str}\033[0m")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Tongfang/AiStone Keyboard RGB Controller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  kbd-rgb all violet              # Set all keys to violet
  kbd-rgb keys q w e r t y green  # Set multiple keys
  kbd-rgb sector wasd gold        # Set WASD to gold
  kbd-rgb animate rainbow         # Rainbow animation (foreground)
  kbd-rgb animate rainbow -d      # Rainbow animation (background)
  kbd-rgb stop                    # Stop background animation

GitHub: https://github.com/aineasg/tongfang-rgb
        """
    )
    
    subparsers = parser.add_subparsers(dest="command")
    
    subparsers.add_parser("off")
    subparsers.add_parser("colors")
    subparsers.add_parser("sectors")
    subparsers.add_parser("status")
    subparsers.add_parser("stop")
    
    p_all = subparsers.add_parser("all")
    p_all.add_argument("color")
    
    p_key = subparsers.add_parser("key")
    p_key.add_argument("key")
    p_key.add_argument("color")
    
    p_keys = subparsers.add_parser("keys")
    p_keys.add_argument("keys", nargs="+")
    p_keys.add_argument("color")
    
    p_sector = subparsers.add_parser("sector")
    p_sector.add_argument("sector")
    p_sector.add_argument("color")
    
    p_row = subparsers.add_parser("row")
    p_row.add_argument("row")
    p_row.add_argument("color")
    
    p_animate = subparsers.add_parser("animate")
    p_animate.add_argument("name", choices=["rainbow", "breathe", "wave", "party", "fire", "matrix", "stars", "lightning", "pulse"])
    p_animate.add_argument("color", nargs="?", default="white")
    p_animate.add_argument("--speed", "-s", type=float, default=1.0)
    p_animate.add_argument("--daemon", "-d", action="store_true", help="Run in background")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "stop":
        stop_animation()
        return
    
    if args.command == "status":
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, 'r') as f:
                    pid = int(f.read().strip())
                os.kill(pid, 0)
                if os.path.exists(STATE_FILE):
                    with open(STATE_FILE, 'r') as f:
                        state = json.load(f)
                    print(f"\033[32mAnimation running: {state['animation']} (PID {pid})\033[0m")
                else:
                    print(f"\033[32mAnimation running (PID {pid})\033[0m")
            except (ProcessLookupError, ValueError):
                if os.path.exists(PID_FILE):
                    os.remove(PID_FILE)
                print("\033[33mNo animation running\033[0m")
        else:
            print("\033[33mNo animation running\033[0m")
        return
    
    if args.command == "colors":
        print("\nAvailable colors:\n")
        for i, c in enumerate(sorted(COLORS.keys())):
            print(f"  {c:15}", end="")
            if (i + 1) % 5 == 0:
                print()
        print("\n")
        return
    
    if args.command == "sectors":
        print("\nAvailable sectors:\n")
        for s in sorted(SECTORS.keys()):
            print(f"  {s}")
        print()
        return
    
    if os.geteuid() != 0:
        print("\033[33mPlease run with sudo.\033[0m")
        sys.exit(1)
    
    controller = KeyboardController()
    
    if args.command == "off":
        stop_animation()
        controller.set_all(0, 0, 0)
        print("\033[32mLights off.\033[0m")
    elif args.command == "all":
        stop_animation()
        r, g, b = parse_color(args.color)
        controller.set_all(r, g, b)
        print(f"\033[32mSet all to ({r}, {g}, {b})\033[0m")
    elif args.command == "key":
        r, g, b = parse_color(args.color)
        controller.set_key(args.key, r, g, b)
    elif args.command == "keys":
        r, g, b = parse_color(args.color)
        controller.set_keys(args.keys, r, g, b)
        print(f"\033[32mSet keys to ({r}, {g}, {b})\033[0m")
    elif args.command == "sector":
        r, g, b = parse_color(args.color)
        controller.set_sector(args.sector, r, g, b)
        print(f"\033[32mSet sector to ({r}, {g}, {b})\033[0m")
    elif args.command == "row":
        r, g, b = parse_color(args.color)
        controller.set_row(args.row, r, g, b)
        print(f"\033[32mSet row to ({r}, {g}, {b})\033[0m")
    elif args.command == "animate":
        color = parse_color(args.color)
        speed = args.speed
        if args.daemon:
            start_daemon(args.name, color, speed)
        else:
            print(f"\033[32mStarting {args.name} animation (Ctrl+C to stop)...\033[0m")
            animations = {
                "rainbow": lambda: controller.animate_rainbow(speed),
                "breathe": lambda: controller.animate_breathe(*color, speed),
                "wave": lambda: controller.animate_wave(color, speed),
                "party": lambda: controller.animate_party(speed),
                "fire": lambda: controller.animate_fire(speed),
                "matrix": lambda: controller.animate_matrix(speed),
                "stars": lambda: controller.animate_stars(speed),
                "lightning": lambda: controller.animate_lightning(speed),
                "pulse": lambda: controller.animate_pulse(speed),
            }
            animations[args.name]()


if __name__ == "__main__":
    main()
