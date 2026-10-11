# Dev ToolBox — Kodi Backup & Restore User Guide

## 1. Overview
The **Backup & Restore Engine** creates clean, single-archive `.zip` packages of your Kodi setup and restores them reliably across any platform (Android, Linux, Windows, macOS, CoreELEC, and LibreELEC).

---

## 2. Target Directories
Backups exclusively target the two fundamental directories:
- `special://home/addons/` — All user installed addons, scripts, and skins.
- `special://masterprofile/` (`userdata`) — Database configurations, keymaps, sources, passwords, and addon data.

All other root folders (such as temporary caches and platform binaries) are completely redundant and excluded to minimize archive size.

---

## 3. Automatic Sanitization & Cleaning
Every archive is dynamically sanitized during compression to discard runtime garbage and private development metadata:
- Excluded directories: `__pycache__`, `.git`, `.github`, `.idea`, `.vscode`, `packages` (cached addon zips), `Thumbnails` (cached textures), and `temp`.
- Excluded files: `.pyc`, `.pyo`, `kodi.log`, `kodi.old.log`, `.bak`, `.tmp`, and OS cache files (`.DS_Store`, `Thumbs.db`).

---

## 4. Databases (`Database/*.db`)
Before backing up, you are prompted whether to bundle database files:
- Includes: `AddonsXX.db`, `TexturesXX.db`, `MyVideosXXX.db`, `MyMusicXX.db`, `ViewModes.db`.
- **Default:** YES.
- **Note:** Active Kodi database files are read safely from disk.

---

## 5. The Manifest (`devtoolbox_manifest.json`)
Every backup produced by Dev ToolBox embeds a metadata manifest at the archive root:
- Originating Kodi version (e.g., Kodi 21 "Omega", major integer 21).
- Creation timestamp and platform build string.
- Database inclusion status.
- Total indexed file count.

### Version Mismatch Safety Guard
Databases and Python API bindings differ across major Kodi releases. When restoring an archive with a manifest:
- If the archive was created on a different major Kodi release (e.g. Kodi 20 vs 21), a high-visibility warning is displayed.
- The restore is aborted unless you explicitly choose to override.

### Archives Without a Manifest
If you select a third-party archive or an older zip created without Dev ToolBox:
- Dev ToolBox detects the absence of `devtoolbox_manifest.json`.
- A warning prompts you that the archive origin and Kodi version cannot be verified before proceeding.
- Root path normalization automatically detects and strips any enclosing parent directories (e.g. `backup/addons/` -> `addons/`).

---

## 6. Restore Strategies
You can choose between two restore modes:
1. **Full Replace (Clean Wipe):**
   - Deletes existing addons and userdata before extraction to replicate the exact state of the backup.
   - **Self-Preservation:** Dev ToolBox protects its own directory (`plugin.program.devtoolbox`) from deletion and overwrites, ensuring operational stability and preventing mid-restore crashes.
2. **Merge / Update (Non-destructive):**
   - Adds missing files and updates matching files without deleting other installed addons or settings.

---

## 7. Post-Restore Process Termination (Force Close)
Because Kodi holds live in-memory locks on active SQLite databases (`Addons*.db`, `Textures*.db`, `MyVideos*.db`) while running:
- A graceful exit or restart (`RestartApp` / `Quit`) executes Kodi shutdown hooks that flush dirty in-memory database pages over the freshly extracted files on disk, corrupting or reverting your restored state!
- **Force Close (Default):** Dev ToolBox immediately terminates the Kodi process (`SIGKILL` on Linux/Android/CoreELEC/macOS, `taskkill /F` and `os._exit(0)` on Windows). This bypasses in-memory flushing and guarantees all restored databases remain 100% intact.
- Once closed, simply re-launch Kodi normally.
- This behavior can be toggled in Dev ToolBox Addon Settings under **Restore Options**.
