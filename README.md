# Tongfang/AiStone System Controller

A fast, feature-rich RGB keyboard lighting and fan controller for Tongfang/AiStone laptops with ITE 8291 keyboard controller. Includes both a powerful CLI tool and a modern GTK4 GUI application that controls **both RGB lighting and fans in a single window**.

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

> **Note:** Animations run in a dedicated background thread — the GUI stays fully responsive while effects are active.

### 🌡️ Fan Control (GUI)
- **Live RPM readout** for both CPU and GPU fans with animated fan visualization
- **Temperature monitoring** — real-time CPU temperature display
- **Fan modes** — switch between Auto (intelligent) and Boost with one click
- **EC-based control** via `acpi_call` — safe reads and writes with validation
- Requires `acpi_call` and `ec_sys` kernel modules (see Requirements)

### 🖥️ Combined GUI
Everything in **one panel** — RGB keyboard controls on top, fan monitoring and control below. No need to juggle separate tools.

### 🔄 Background Mode (CLI)
- Run animations in the background (daemon mode)
- Continue using your terminal or close it — animation keeps running
- Easy start/stop controls

## 📋 Requirements

### Hardware
- **Tongfang/AiStone laptop** with ITE 8291 keyboard controller
- Compatible models: X6RP57TW, GK5CN5Z, GK5CP6Z, and other Tongfang chassis
- **USB ID**: `048d:600b`
- **LED zones**: 126 (numbered 0–125)

### Software
- Linux kernel with LED sysfs support
- Python 3.8 or higher
- Root/sudo access (required for hardware control)

#### Additional requirements for fan control
- `acpi_call` kernel module — for writing fan modes via ACPI
- `ec_sys` kernel module — for reading fan RPM, temperature, and duty cycle

```bash
# Load the modules (temporary, until next reboot)
sudo modprobe acpi_call
sudo modprobe ec_sys write_support=1

# To load them automatically on boot (Arch/CachyOS)
echo "acpi_call" | sudo tee /etc/modules-load.d/fan-control.conf
echo "ec_sys" | sudo tee -a /etc/modules-load.d/fan-control.conf
```

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
2. Install the combined GUI to `/usr/local/bin/kbd-rgb-gui`
3. Install required dependencies for your distribution
4. Create sudoers rules for passwordless execution
5. Add shell aliases for easy access
6. Create a desktop entry for the GUI

## 🚀 Usage

### GUI Application

```bash
# Launch the combined RGB + Fan controller GUI
sudo kbd-rgb-gui
```

Or find **"Keyboard RGB Controller"** in your application menu.

**GUI Features:**
- Click on the virtual keyboard to select keys
- Use the color picker or preset colors
- Apply colors to selected keys, sectors, or all keys
- Start/stop animations — GUI stays responsive during animations
- Monitor CPU/GPU fan RPM and CPU temperature in real time
- Switch fan modes (Auto / Boost) directly from the GUI

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
├── kbd-rgb-gui.py      # Combined GTK4 GUI (RGB + Fan control)
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
- Each zone has a `multi_intensity` file accepting "R G B" values (0–50)
- No kernel modules required for RGB — works with standard Linux LED class
- Fan control uses ACPI method `\_SB.AMW0.WMBC` via `acpi_call`
- Fan status is read directly from the EC register map via `/sys/kernel/debug/ec/ec0/io`

### Color Range
- **Important**: The ITE 8291 uses a **0–50** color range, NOT 0–255!
- This is a hardware limitation of the controller
- The software handles conversion automatically

### Zone Mapping
- Zone 0: Left Ctrl key
- Zones 1–125: Other keys (see `KEY_MAP` in source)
- Total: 126 controllable zones
- Some physical keys (e.g. Tab) span two separate LED zones — both are written automatically

### Fan Control Safety
- All EC writes are validated before being sent
- PWM values are capped at the safe maximum (200)
- Fan mode byte is checked against the known-valid set before writing
- The GUI gracefully degrades if `acpi_call` or `ec_sys` is unavailable — RGB controls still work fully

## 🔧 Troubleshooting

### "No LED zones detected"
```bash
ls /sys/class/leds/ | grep kbd_backlight
lsusb | grep 048d:600b
```

### GUI doesn't start
```bash
python3 -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk; print('OK')"
```
Install missing dependencies (see Installation section).

### Colors don't change
- Ensure you're running with `sudo` or the sudoers rule is active
- Check: `cat /etc/sudoers.d/kbd-rgb`

### Fan control section shows a warning
The GUI will show an orange warning if the fan control modules aren't loaded. RGB lighting still works normally. Load the modules to enable fan control:
```bash
sudo modprobe acpi_call
sudo modprobe ec_sys write_support=1
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
Any laptop with the ITE 8291 keyboard controller (USB ID: 048d:600b). Fan control requires compatible ACPI methods — tested on X6RP57TW.

## 🔌 Adding Support for Your Laptop

Want to add support for your laptop? Here's how you can help!

### Option 1: Submit Your Hardware Info (Recommended)

[Open an issue](https://github.com/aineasg/tongfang-rgb/issues) with the title "Support Request: [Your Laptop Model]" and include:

```bash
# 1. Laptop model
sudo dmidecode -t system | grep -E "Manufacturer|Product Name|Version"

# 2. USB device check
lsusb | grep -i "ite\|048d"

# 3. LED sysfs interface
ls -la /sys/class/leds/ | grep -i kbd

# 4. Zone count
ls /sys/class/leds/rgb:kbd_backlight* 2>/dev/null | wc -l

# 5. Writability check (run as root)
sudo ls -la /sys/class/leds/rgb:kbd_backlight/multi_intensity 2>/dev/null

# 6. Test write (run as root)
echo "50 0 0" | sudo tee /sys/class/leds/rgb:kbd_backlight/multi_intensity 2>/dev/null

# 7. Kernel version
uname -r

# 8. Distro
cat /etc/os-release | grep -E "^NAME=|^VERSION="
```

### Option 2: Submit an EC Dump (for fan control support)

```bash
sudo modprobe ec_sys
sudo cat /sys/kernel/debug/ec/ec0/io 2>/dev/null | xxd > ec-dump.txt
```

Attach the dump to your issue.

### Option 3: Add Support Yourself

1. Fork the repository
2. Identify your zone mapping by iterating zones and noting which key lights up
3. Update `KEY_MAP`, `TOTAL_ZONES`, `SECTORS` in the source
4. Test and submit a Pull Request with your laptop model and confirmation it works

## 📝 License

MIT License - Feel free to use, modify, and distribute.

## 🙏 Credits

- Author: [Aineasg](https://github.com/aineasg)
- Based on the ITE 8291 RGB controller documentation
- Inspired by various keyboard RGB projects in the Linux community

## 🐛 Reporting Issues

[Open an issue](https://github.com/aineasg/tongfang-rgb/issues) with:
1. Your laptop model
2. Linux distribution
3. Output of:
   ```bash
   ls /sys/class/leds/rgb:kbd_backlight* 2>/dev/null | wc -l
   lsusb | grep 048d
   ```

## 🔄 Changelog

### v2.0.0
- **Combined GUI** — RGB keyboard control and fan control now in a single window
- **Fan monitoring** — live CPU/GPU RPM, CPU temperature, and fan mode display
- **Fan mode control** — switch between Auto and Boost directly from the GUI
- **Animated fan visualization** — fan blades spin in sync with actual RPM
- **Non-blocking animations** — animation engine moved to a background thread; GUI is fully responsive during effects
- **Key mapping fixes** — Tab key now correctly writes both LED zones (42 and 63)
- EC fan control uses safe ACPI method with validated writes and PWM capping

### v1.0.0
- Initial release
- CLI with full RGB control
- GTK4 GUI with visual keyboard
- 9 animation effects
- Background/daemon mode
- Multi-distribution support (Arch, Debian, Fedora, openSUSE)
