# Contributing to Tongfang RGB Controller

Thank you for your interest in contributing!

## 🐛 Bug Reports

If you find a bug, please [open an issue](https://github.com/aineasg/tongfang-rgb/issues) with:

1. **Your system info:**
   - Laptop model
   - Linux distribution
   - Python version (`python3 --version`)

2. **Hardware detection:**
   ```bash
   ls /sys/class/leds/rgb:kbd_backlight* | wc -l
   lsusb | grep 048d
   ```

3. **Error message:** The full error output

4. **Steps to reproduce:** What you did that caused the error

## 💡 Feature Requests

[Open an issue](https://github.com/aineasg/tongfang-rgb/issues) with:
- Description of the feature
- Use case (why would this be useful?)
- Possible implementation ideas (optional)

## 🔧 Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly on your system
5. Commit with clear messages (`git commit -m "Add amazing feature"`)
6. Push to your fork (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Style

- Python 3 compatible
- Follow PEP 8 guidelines
- Add comments for complex logic

### Testing

Before submitting, please test:
- [ ] CLI commands work (`kbd-rgb colors`, `kbd-rgb all red`, etc.)
- [ ] GUI launches without errors
- [ ] Colors actually change on your keyboard
- [ ] Animations work properly
- [ ] Background mode works

## 🎨 Adding Support for New Laptops

If you have a laptop that works with this tool but isn't listed, please share:

```bash
sudo dmidecode -t system | grep -E "Manufacturer|Product Name"
lsusb | grep 048d
ls /sys/class/leds/rgb:kbd_backlight* | wc -l
```

## 📝 License

By contributing, you agree that your contributions will be licensed under the MIT License.
