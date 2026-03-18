# Quick Start Guide

## ⚡ Fast Install

```bash
git clone https://github.com/aineasg/tongfang-rgb.git && cd tongfang-rgb && sudo ./setup.sh
```

Then reload your shell:
```bash
source ~/.bashrc   # or ~/.zshrc or ~/.config/fish/config.fish
```

## 📦 Dependencies by Distribution

| Distribution | Install Command |
|-------------|-----------------|
| **Arch / CachyOS / Manjaro** | `sudo pacman -S python python-gobject gtk4` |
| **Debian / Ubuntu / Mint / Pop!_OS** | `sudo apt install python3 python3-gi gir1.2-gtk-4.0` |
| **Fedora / RHEL / CentOS** | `sudo dnf install python3 python3-gobject gtk4` |
| **openSUSE** | `sudo zypper install python3 python3-gobject gtk4` |

## 🎯 Try It Out

```bash
# CLI - Set all keys to violet
kbd-rgb all violet

# CLI - Run rainbow animation in background
kbd-rgb animate rainbow -d

# GUI - Launch the visual interface
sudo kbd-rgb-gui
```

## 🔧 Quick Troubleshooting

### No LED zones detected?
```bash
ls /sys/class/leds/ | grep kbd_backlight
lsusb | grep 048d:600b
```

### GUI won't start?
```bash
python3 -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk; print('OK')"
```

### Need to stop an animation?
```bash
kbd-rgb stop
```

## 📚 More Info

- Full documentation: [README.md](README.md)
- Report issues: [GitHub Issues](https://github.com/aineasg/tongfang-rgb/issues)
