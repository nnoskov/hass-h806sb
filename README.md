# <img src="https://github.com/nnoskov/hass-h806sb/blob/8354b70590e1c51bc88f9ddc57a96e29cae6d610/custom_components/h806sb/icon.svg" width="48" height="48" alt="H806SB Logo"> Home Assistant H806SB LED Controller Integration

[![GitHub release](https://img.shields.io/github/release/nnoskov/hass-h806sb.svg)](https://github.com/nnoskov/hass-h806sb/releases)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/nnoskov/hass-h806sb)
![GitHub last commit](https://img.shields.io/github/last-commit/nnoskov/hass-h806sb)
[![Buy me a coffee](https://img.shields.io/badge/Buy%20me%20a%20coffee-%E2%98%95-yellow)](https://buymeacoffee.com/nnoskov)

Control your H806SB LED strip controllers directly from Home Assistant via WiFi. This custom integration provides seamless control of your LED lighting with automatic device discovery and intuitive controls.

## ✨ Features

- 🔍 **Automatic Discovery** - Finds devices on your network automatically
- ⚡ **Power Control** - Turn lights on/off with instant response
- 💡 **Brightness Adjustment** - Smooth dimming from 0-100%
- 🌐 **WiFi Connectivity** - Control your lights over local network
- 🧩 **Native Home Assistant Integration** - Appears as standard light entities

## 📦 Installation
### Via HACS (recommended)

1. Ensure you have [HACS](https://hacs.xyz) installed in your Home Assistant
2. Go to **HACS** → **Integrations**
3. Click the 3-dot menu (⋮) in top right corner → **Custom repositories**
4. Add repository URL: `https://github.com/nnoskov/hass-h806sb`
5. Select category: **Integration**
6. Click **ADD**
7. Search for "H806SB" in HACS and install it
8. Restart Home Assistant
9. Go to **Settings** → **Devices & Services** → **Add Integration**
10. Search for "H806SB" and configure it

### Manual installation

1. Download the latest release from [Releases page](https://github.com/nnoskov/hass-h806sb/releases)
2. Extract the `h806sb` folder from the ZIP archive
3. Copy the `h806sb` folder to your Home Assistant `config/custom_components` directory
4. Restart Home Assistant
5. Go to **Settings** → **Devices & Services** → **Add Integration**
6. Search for "H806SB" and configure it

### Verification

After installation, check:
- The `h806sb` folder exists in `config/custom_components`
- No errors in Home Assistant logs
- The integration appears in available integrations