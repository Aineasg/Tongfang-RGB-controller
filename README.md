# Tongfang/AiStone Keyboard RGB Controller

A fast, feature-rich RGB keyboard lighting controller for Tongfang/AiStone laptops with ITE 8291 keyboard controller. Includes both a powerful CLI tool and a modern GTK4 GUI application.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Linux-informational.svg)
![Python](https://img.shields.io/badge/python-3.8+-success.svg)

## ✨ Features

### 🎨 Per-Key RGB Control
- **126 individual LED zones** - Control every key independently
- **Visual keyboard GUI** - Click on keys to select and color them
- **Real-time preview** - See colors change instantly on both GUI and keyboard

### 🎯 Quick Controls
- **Sectors** - WASD, QWERTY, letters, numbers, function keys, numpad, arrows, modifiers
- **Rows** - Function row, number row, QWERTY row, home row, ZXCV row, bottom row
- **All keys** - Set entire keyboard to one color with a single command

### 🌈 60+ Color Presets
Including: red, orange, yellow, green, cyan, blue, purple, violet, magenta, pink, white, gold, coral, amber, emerald, sapphire, ruby, neon variants, and many more.

### ✨ 9 Animation Effects
| Animation | Description |
|-----------|-------------|
| **Rainbow** | Flowing rainbow wave across all keys |
| **Breathe** | Smooth pulsing effect with your chosen color |
| **Wave** | Wave effect propagating across the keyboard |
| **Party** | Random colors on all keys - great for parties! |
| **Fire** | Realistic fire/flame effect with orange/red tones |
| **Matrix** | Matrix-style green falling code effect |
| **Stars** | Twinkling stars appearing randomly |
| **Lightning** | Random lightning flash effects |
| **Pulse** | Color cycling through the spectrum |

### 🖥️ Dual Interface
- **CLI** - Fast terminal commands for scripting and quick changes
- **GUI** - Visual GTK4 application with interactive keyboard layout

### 🔄 Background Mode
- Run animations in the background (daemon mode)
- Continue using your terminal or close it - animation keeps running
- Easy start/stop controls

## 📋 Requirements

### Hardware
- **Tongfang/AiStone laptop** with ITE 8291 keyboard controller
- Compatible models: X6RP57TW, GK5CN5Z, GK5CP6Z, and other Tongfang chassis
- **USB ID**: `048d:600b`
- **LED zones**: 126 (numbered 0-125)

### Software
- Linux kernel with LED sysfs support
- Python 3.8 or higher
- Root/sudo access (required for hardware control)

## 📦 Installation

### Quick Install (One Command)

```bash
# Arch / CachyOS / Manjaro
git clone https://github.com/aineasg/tongfang-rgb.git && cd tongfang-rgb && sudo ./setup.sh

# Debian / Ubuntu / Mint / Pop!_OS
git clone https://github.com/aineasg/tongfang-rgb.git && cd tongfang-rgb && sudo ./setup.sh

# Fedora / RHEL
git clone https://github.com/aineasg/tongfang-rgb.git && cd tongfang-rgb && sudo ./setup.sh
```

### Dependencies by Distribution

| Distribution | Install Command |
|-------------|-----------------|
| **Arch / CachyOS / Manjaro** | `sudo pacman -S python python-gobject gtk4` |
| **Debian / Ubuntu / Mint / Pop!_OS** | `sudo apt install python3 python3-gi gir1.2-gtk-4.0` |
| **Fedora / RHEL / CentOS** | `sudo dnf install python3 python3-gobject gtk4` |
| **openSUSE** | `sudo zypper install python3 python3-gobject gtk4` |

### Manual Install

```bash
# Clone the repository
git clone https://github.com/aineasg/tongfang-rgb.git
cd tongfang-rgb

# Make the setup script executable
chmod +x setup.sh

# Run setup (auto-detects your distribution)
sudo ./setup.sh

# Reload your shell
source ~/.config/fish/config.fish  # Fish
source ~/.bashrc                    # Bash
source ~/.zshrc                     # Zsh
```

The setup script will:
1. Install the CLI tool to `/usr/local/bin/kbd-rgb`
2. Install the GUI to `/usr/local/bin/kbd-rgb-gui`
3. Install required dependencies for your distribution
4. Create sudoers rules for passwordless execution
5. Add shell aliases for easy access
6. Create a desktop entry for the GUI

## 🚀 Usage

### GUI Application

```bash
# Launch the GUI
sudo kbd-rgb-gui
```

Or find **"Keyboard RGB Controller"** in your application menu.

**GUI Features:**
- Click on the virtual keyboard to select keys
- Use the color picker or preset colors
- Apply colors to selected keys, sectors, or all keys
- Start/stop animations with speed control
- Enable background mode for persistent animations

### CLI Commands

#### Basic Color Control
```bash
# Set all keys to a color
kbd-rgb all violet
kbd-rgb all gold
kbd-rgb all 25,30,40    # Custom RGB (0-50 range)

# Turn off all lights
kbd-rgb off

# Set individual keys
kbd-rgb key w cyan
kbd-rgb keys q w e r t y green

# Set sectors
kbd-rgb sector wasd gold
kbd-rgb sector function red
kbd-rgb sector letters blue

# Set rows
kbd-rgb row row_qwerty magenta
kbd-rgb row row_home cyan
```

#### Animations
```bash
# Foreground animations (Ctrl+C to stop)
kbd-rgb animate rainbow
kbd-rgb animate fire
kbd-rgb animate matrix

# With speed adjustment (0.25 - 3.0)
kbd-rgb animate rainbow -s 2.0

# Background mode (continues after closing terminal)
kbd-rgb animate rainbow -d
kbd-rgb animate breathe cyan -d -s 1.5

# Control background animations
kbd-rgb status          # Check running animation
kbd-rgb stop            # Stop background animation
```

#### Information
```bash
kbd-rgb colors          # List all available colors
kbd-rgb sectors         # List all available sectors
kbd-rgb --help          # Show help
```

### Available Colors

| Basic | Warm | Cool | Special |
|-------|------|------|---------|
| red | orange | blue | white |
| green | yellow | navy | silver |
| cyan | gold | violet | gray |
| purple | amber | indigo | dim |
| magenta | coral | sapphire | dark |
| pink | peach | emerald | off |
| lime | tangerine | turquoise | |
| teal | copper | sky | |
| | bronze | ocean | |

Plus many more including neon variants (neon_green, neon_blue, neon_pink, neon_orange).

### Available Sectors

| Sector | Keys Included |
|--------|---------------|
| wasd | W, A, S, D |
| wasdqe | W, A, S, D, Q, E |
| qwerty | Q, W, E, R, T, Y, U, I, O, P |
| asdfghjkl | A, S, D, F, G, H, J, K, L |
| zxcvbnm | Z, X, C, V, B, N, M |
| letters | All letter keys |
| numbers | 1, 2, 3, 4, 5, 6, 7, 8, 9, 0 |
| function | F1-F12, Esc |
| numpad | All numpad keys |
| arrows | Arrow keys |
| modifiers | Ctrl, Alt, Shift, Win, Fn |
| space | Spacebar |
| enter | Enter key |
| navigation | Home, End, PgUp, PgDn, Del |

## 📁 Project Structure

```
tongfang-rgb/
├── kbd-rgb.py          # Main CLI application
├── kbd-rgb-gui.py      # GTK4 GUI application
├── setup.sh            # Universal installation script
├── install-deps.sh     # Dependency installer
├── Makefile            # Make-based installation
├── README.md           # This file
├── QUICK-START.md      # Quick start guide
└── CONTRIBUTING.md     # Contribution guidelines
```

## ⚙️ Technical Details

### Hardware Communication
- Uses Linux sysfs interface at `/sys/class/leds/rgb:kbd_backlight_*/`
- Each zone has a `multi_intensity` file accepting "R G B" values (0-50)
- No kernel modules required - works with standard Linux LED class

### Color Range
- **Important**: The ITE 8291 uses a **0-50** color range, NOT 0-255!
- This is a hardware limitation of the controller
- The software handles conversion automatically

### Zone Mapping
- Zone 0: Left Ctrl key
- Zones 1-125: Other keys (see KEY_MAP in source)
- Total: 126 controllable zones

## 🔧 Troubleshooting

### "No LED zones detected"
1. Check if your device is recognized:
   ```bash
   ls /sys/class/leds/ | grep kbd_backlight
   ```
2. Ensure ITE 8291 controller is present:
   ```bash
   lsusb | grep 048d:600b
   ```

### GUI doesn't start
1. Verify GTK4 is installed:
   ```bash
   python3 -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk; print('OK')"
   ```
2. Install missing dependencies (see Installation section)

### Colors don't change
- Ensure you're running with `sudo` or the sudoers rule is active
- Check your user is in the sudoers file:
   ```bash
   cat /etc/sudoers.d/kbd-rgb
   ```

### Animation won't stop
```bash
kbd-rgb stop
# Or manually:
sudo pkill -f kbd-rgb
sudo rm /tmp/kbd-rgb.pid
```

## 🤝 Compatibility

### Tested On
- Arch Linux / CachyOS
- Ubuntu 22.04 / 24.04
- Fedora 39/40
- Linux Mint 21

### Laptops Known to Work
- Tongfang X6RP57TW
- Tongfang GK5CN5Z
- Tongfang GK5CP6Z
- AiStone gaming laptops
- Other Tongfang chassis laptops with ITE 8291

### Should Work On
Any laptop with the ITE 8291 keyboard controller (USB ID: 048d:600b)

## 🔌 Adding Support for Your Laptop

Want to add support for your laptop? Here's how you can help!

### Option 1: Submit Your Hardware Info (Recommended)

[Open an issue](https://github.com/aineasg/tongfang-rgb/issues) with the title "Support Request: [Your Laptop Model]" and include:

```bash
# Run these commands and paste the output:

# 1. Laptop model information
sudo dmidecode -t system | grep -E "Manufacturer|Product Name|Version"

# 2. USB device check
lsusb | grep -i "ite\|048d"

# 3. Check for LED sysfs interface
ls -la /sys/class/leds/ | grep -i kbd

# 4. Count available LED zones
ls /sys/class/leds/rgb:kbd_backlight* 2>/dev/null | wc -l

# 5. Check if zones are writable (run as root)
sudo ls -la /sys/class/leds/rgb:kbd_backlight/multi_intensity 2>/dev/null

# 6. Test writing a color (optional, run as root)
echo "50 0 0" | sudo tee /sys/class/leds/rgb:kbd_backlight/multi_intensity 2>/dev/null && echo "Write successful!" || echo "Write failed"

# 7. Kernel version
uname -r

# 8. Distro
cat /etc/os-release | grep -E "^NAME=|^VERSION="
```

If your laptop has a different ITE controller or uses a different sysfs path, also include:
```bash
# List all LED devices
ls -la /sys/class/leds/

# Check for any RGB keyboard devices
find /sys/class/leds/ -name "*kbd*" -o -name "*keyboard*" -o -name "*rgb*"
```

### Option 2: Submit an EC Dump (Advanced)

If you want to help reverse-engineer a new controller:

```bash
# Install ec-dump tool (if available) or use:
sudo modprobe ec_sys
sudo cat /sys/kernel/debug/ec/ec0/io 2>/dev/null | xxd > ec-dump.txt

# Or use the kernel's embedded controller interface
sudo hexdump -C /sys/kernel/debug/ec/ec0/io > ec-dump-verbose.txt 2>/dev/null
```

Attach the dump files to your issue.

### Option 3: Add Support Yourself

If your laptop uses a similar sysfs interface but with different zone mappings:

1. **Fork the repository**

2. **Identify your zone mapping**:
   ```bash
   # Test each zone to find which key it controls
   for i in $(ls /sys/class/leds/ | grep kbd_backlight | sed 's/rgb:kbd_backlight//' | tr -d '_'); do
       echo "Testing zone: $i"
       echo "50 0 0" > /sys/class/leds/rgb:kbd_backlight${i}_$i/multi_intensity 2>/dev/null || \
       echo "50 0 0" > /sys/class/leds/rgb:kbd_backlight_$i/multi_intensity 2>/dev/null
       sleep 0.5
   done
   ```

3. **Edit `kbd-rgb.py`**:
   - Update `KEY_MAP` dictionary with your zone numbers
   - Update `TOTAL_ZONES` if you have a different number
   - Update `SECTORS` and `ROWS` if needed

4. **Test thoroughly**:
   ```bash
   sudo ./kbd-rgb.py all red
   sudo ./kbd-rgb.py sector wasd blue
   ```

5. **Submit a Pull Request** with:
   - Your laptop model name
   - The changes you made
   - Confirmation that it works

### What I Need to Add Support

| Information | Why It's Needed |
|-------------|-----------------|
| Laptop model | To list compatible devices |
| `lsusb` output | To identify the controller chip |
| Zone count | To set `TOTAL_ZONES` correctly |
| Zone mapping | To map keys to LED zones |
| Sysfs path | If different from `rgb:kbd_backlight` |
| Color range | If different from 0-50 |

I'll review submissions and merge valid support additions to the main branch!

## 📝 License

MIT License - Feel free to use, modify, and distribute.

## 🙏 Credits

- Author: [Aineasg](https://github.com/aineasg)
- Based on the ITE 8291 RGB controller documentation
- Inspired by various keyboard RGB projects in the Linux community

## 🐛 Reporting Issues

If you encounter any issues, please [open an issue](https://github.com/aineasg/tongfang-rgb/issues) with:

1. Your laptop model
2. Linux distribution
3. Output of:
   ```bash
   ls /sys/class/leds/rgb:kbd_backlight* 2>/dev/null | wc -l
   lsusb | grep 048d
   ```

## 🔄 Changelog

### v1.0.0
- Initial release
- CLI with full RGB control
- GTK4 GUI with visual keyboard
- 9 animation effects
- Background/daemon mode
- Multi-distribution support (Arch, Debian, Fedora, openSUSE)
