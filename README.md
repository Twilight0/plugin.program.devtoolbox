# 🧰 Dev Toolbox (Kodi Development Suite)

[![Kodi](https://img.shields.io/badge/Kodi-v19%20%7C%20v20%20%7C%20v21%2B-blue.svg)](https://kodi.tv/)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-green.svg)](LICENSE)
[![Python: 3.x](https://img.shields.io/badge/Python-3.x-yellow.svg)](https://www.python.org/)

**Dev Toolbox** (`plugin.program.devtoolbox`) is a comprehensive, modular development and diagnostics suite designed specifically for Kodi addon authors, skinners, and power users.

Instead of relying on restricted standard dialogs or SSH terminal workarounds, **Dev Toolbox** provides native, full-screen **`xbmcgui.WindowXML`** interfaces for in-GUI code editing, keymap mapping, safe addon inspection, and real-time log uploading with QR code pairing.

---

## 🏛️ Architecture Overview

```text
plugin.program.devtoolbox/
├── 💻 In-GUI Code & Text Editor      ──> Custom WindowXML with syntax styling & live runner
├── ⌨️  Visual Keymap Editor           ──> Custom WindowXML hotkey mapper across all scopes
├── 🔍 Safe Addon Inspector           ──> Crash-proof custom WindowXML addon metadata viewer
├── 📦 Official Kodi Installer        ──> Direct dependency (script.module.*) downloader from mirrors.kodi.tv
├── 📜 Kodi Log Tools & QR Uploader   ──> Live log viewer & WindowXML QR code mobile pairing
├── ⚡ Live Debug & Skin Toggles      ──> Instant debug overlay, skin reload & dirty regions
├── 🎨 Artwork Theme Engine           ──> Dynamic texture cache path isolation & asset syncing
└── 🌐 Global Context Menu Item       ──> 1-click launcher accessible from anywhere in Kodi
```

---

## ✨ Features & Capabilities

### 💻 1. In-GUI Code & Text Editor (`script-devtoolbox-editor.xml`)

A complete in-GUI code editing workspace running directly on your TV, desktop, or mobile device:

- ✍️ **Flexible Editing Modes**: Edit files line-by-line or paste/replace full buffer content.

- 🌈 **Syntax Styling**: Colorized keyword highlighting for Python scripts, XML layouts, and JSON structures.

- ▶️ **In-GUI Script Execution**: Test and run any Python file directly from the editor with live capture of `stdout`, `stderr`, and exit return codes.

- 💡 **Kodi API Snippets & Autocompletions**: Instant insertion of common Kodi idioms (`xbmcgui.Dialog`, JSON-RPC commands, list items, settings access, file operations).

- 🔎 **Find & Replace**: Search and replace across lines with match counter and navigation.

- 📁 **Virtual Path Support**: Direct resolution of `special://home`, `special://userdata`, and installed addon directories.

<br>

### ⌨️ 2. Visual Keymap Editor (`script-devtoolbox-keymap.xml`)

A visual mapping interface to customize controller, keyboard, and remote bindings on the fly:

- 🎯 **Full Scope Support**: Modify keymaps across scopes (`global`, `Home`, `VirtualKeyboard`, `VideoMenu`, `FullscreenVideo`, `MyFiles`, etc.).

- 🎮 **Interactive Action Picker**: Select from curated Kodi built-in actions, navigation commands, or define custom built-in strings.

- 🛡️ **Non-Destructive User Overrides**: Saves mappings cleanly into user keymaps (`special://userdata/keymaps/gen.xml`) without altering system defaults.

<br>

### 🔍 3. Safe Addon Inspector & Manager (`script-devtoolbox-addoninfo.xml`)

Kodi's native C++ `DialogAddonInfo` can crash when inspecting non-standard or virtual items. Dev Toolbox provides a safe, crash-proof replacement:

- 📊 **Detailed Metadata**: Displays addon ID, version, author, install path, enabled status, summary, and description.

- 🖼️ **Live Fanart & Icon Previews**: Renders high-resolution fanart backdrops and icons.

- 📜 **Autoscrolling Dependencies**: Neatly displays each required dependency on its own bulleted line with auto-scrolling for long lists.

- 🚀 **Decoupled Editor Launch**: Open `addon.xml` or entry scripts directly in the Dev Text Editor, decoupled via asynchronous invocation to eliminate modal window collisions.

<br>

### 📦 4. Official Kodi Dependency & Addon Installer

Kodi's built-in Add-on Manager hides module dependencies (`script.module.*`) from the user interface. Dev Toolbox connects directly to the official mirror:

- 🌐 **Dynamic Version Codename Querying**: Automatically queries [`https://mirrors.kodi.tv/addons/`](https://mirrors.kodi.tv/addons/) to discover valid mirror branch directories (`omega`, `nexus`, `matrix`, `piers`, etc.) and matches your active Kodi version.

- 📥 **Direct Dependency Installation**: Browse and install any `script.module.*` dependency package directly without requiring third-party repository workarounds.

- 🔍 **Instant Search & Direct ID Input**: Filter across thousands of official repository addons or enter an exact ID (e.g. `script.module.requests`) to fetch and install the latest available ZIP archive with real-time download progress.

- ⚡ **Auto-Enable & Registration**: Automatically extracts packages into `special://home/addons/`, triggers `UpdateLocalAddons`, and enables the module immediately.

<br>

### 📜 5. Log Viewer & QR Code Uploader (`script-devtoolbox-qr.xml`)

Inspect Kodi logs without navigating remote file systems:

- 📋 **Dual Log Modes**: Read full `kodi.log` or filter strictly for `ERROR`, `WARNING`, and `EXCEPTION` events.

- ☁️ **Cloud Pastebin Uploader**: Uploads logs anonymously to secure paste services (`paste.kodi.tv` / `hastebin`).

- 📱 **QR Code Mobile Pairing**: Generates a scannable QR code on-screen via `script-devtoolbox-qr.xml` for instant review on mobile phones or tablets.

<br>

### ⚡ 6. Developer & Skin Debug Toggles

Quick access to critical Kodi developer switches:

- 🐞 **Debug Logging**: One-touch toggle for verbose logging and the on-screen CPU/FPS overlay.

- 📐 **Skin Debugging**: Toggle coordinates, focused control IDs, and dirty regions silently without audio disruptions.

- 🔄 **Instant Skin Reload**: Reload skin cache immediately (`ReloadSkin`) to see UI changes instantly.

- 🔁 **Kodi Restart**: Safely restart the Kodi application directly from the menu.

<br>

### 🎨 7. Dynamic Theme Engine & Texture Cache Isolation

Kodi's internal texture cache (`Textures13.db`) caches images based on file path. Dev Toolbox eliminates stale cache issues by isolating artwork across distinct paths in [`resources/media/`](resources/media/):

| Theme | Icon Path | Fanart Path |
| :--- | :--- | :--- |
| **Theme 0 (Default)** | `resources/media/icon_default.png` | `resources/media/fanart_default.jpg` |
| **Theme 1 (Cyber HUD)** | `resources/media/icon_cyber.png` | `resources/media/fanart_cyber.jpg` |
| **Theme 2 (Modern Glass)** | `resources/media/icon_modern.png` | `resources/media/fanart_modern.jpg` |

- 🔄 **Automatic `addon.xml` Synchronization**: Switching themes updates `<assets>` in `addon.xml` dynamically.
- 🔔 **Silent Restart Reminder**: Displays a silent on-screen notification reminding you to restart Kodi so system-level skin widgets reload the new assets.

<br>

### ⚙️ 8. Customization & Global Access

- 🌐 **Global Context Menu**: Right-click or press `C` / long-press anywhere inside Kodi to open **Dev Toolbox** immediately.

- 🎛️ **Configurable Main Menu**: Toggle individual menu items on or off via Add-on Settings under **Main Menu Items**.

- 🧹 **Clean Execution Model**: Enforces `<reuselanguageinvoker>false</reuselanguageinvoker>` for complete thread isolation and zero memory accumulation across runs.

---

## 🖥️ WindowXML Performance & Design

Unlike standard `xbmcgui.Dialog` implementations which block execution and stack on top of underlying media windows, all Dev Toolbox interfaces are designed as full-fledged `xbmcgui.WindowXML` instances:

1. 🪟 **Full-Screen Render Integrity**: Each window controls its own z-order, backdrop textures, and focus loops without overlaying or bleeding into active Kodi directories.

2. 🔀 **Decoupled Built-in Dispatch**: Editor and diagnostic actions are dispatched via `xbmc.executebuiltin("RunPlugin(...)")` ensuring modal dialogs finish cleanup before child windows initialize.

3. 📺 **Responsive 720p/1080p Scaling**: Skin files use Kodi's native resolution scaling, rendering sharply on 720p, 1080p, and 4K displays.

---

## 📥 Installation

1. Clone or extract into your Kodi `addons` directory:
   ```bash
   git clone https://github.com/Twilight0/plugin.program.devtoolbox.git ~/.kodi/addons/plugin.program.devtoolbox
   ```

2. Restart Kodi or navigate to **Settings -> Add-ons -> Check for updates**.

3. Launch **Dev Toolbox** from the **Programs** menu or via the global context menu.

---

## 📄 License

This project is licensed under the terms of the **GNU General Public License v3.0** (GPL-3.0). See [LICENSE](LICENSE) for details.
