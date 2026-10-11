# -*- coding: utf-8 -*-
"""
Kodi Installation Backup & Restore Engine
Creates and restores single-file sanitized archives (.zip) of addons and userdata.
Platform-independent, uses standard Kodi dialogs.
"""
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import zipfile

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

MANIFEST_FILENAME = "devtoolbox_manifest.json"


def force_kill_kodi():
    """
    Forcefully terminates the Kodi process immediately.
    Bypasses standard Kodi application shutdown hooks and in-memory database flushes
    so that freshly restored SQLite databases and settings on disk are preserved intact.
    """
    pid = os.getpid()
    xbmc.log(f"[DevToolbox] Force killing Kodi process (PID: {pid}) to preserve restored files...", xbmc.LOGINFO)

    # 1. Platform-specific hard kill
    if sys.platform.startswith("win"):
        try:
            subprocess.Popen(f"taskkill /F /PID {pid}", shell=True)
        except Exception as e:
            xbmc.log(f"[DevToolbox] Warning: taskkill failed: {e}", xbmc.LOGWARNING)
        os._exit(0)
    else:
        # Linux, Android, macOS, CoreELEC, LibreELEC
        try:
            os.kill(pid, signal.SIGKILL)
        except Exception:
            try:
                os.kill(pid, signal.SIGTERM)
            except Exception:
                pass
        os._exit(0)

# Exclusion rules for sanitizing the archive
EXCLUDED_DIR_NAMES = {
    "__pycache__",
    ".git",
    ".github",
    ".idea",
    ".vscode",
    "packages",      # Kodi's downloaded zip archive cache
    "Thumbnails",    # Dynamically generated texture thumbnails
    "temp",
    "cdart",
}

EXCLUDED_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".log",
    ".old",
    ".bak",
    ".tmp",
    ".DS_Store",
    "Thumbs.db",
}

EXCLUDED_FILES = {
    "kodi.log",
    "kodi.old.log",
    "spmc.log",
    "spmc.old.log",
}


def get_current_kodi_info():
    """Extract current Kodi build version and major integer."""
    build_str = xbmc.getInfoLabel("System.BuildVersion") or ""
    major = 0
    m = re.search(r"(\d+)\.", build_str)
    if m:
        try:
            major = int(m.group(1))
        except ValueError:
            pass

    return {
        "build_version": build_str,
        "major_version": major,
        "platform": "unknown"
    }


def should_exclude(dir_name=None, file_name=None, rel_path=None, include_databases=True):
    """Determine whether a file or directory should be excluded from the backup."""
    if dir_name and dir_name in EXCLUDED_DIR_NAMES:
        return True

    if rel_path:
        norm = rel_path.replace("\\", "/").strip("/")
        parts = norm.split("/")
        for p in parts:
            if p in EXCLUDED_DIR_NAMES:
                return True

        # Database exclusion check
        if not include_databases:
            if "Database" in parts or any(p.endswith(".db") for p in parts):
                return True

    if file_name:
        if file_name in EXCLUDED_FILES:
            return True
        ext = os.path.splitext(file_name)[1].lower()
        if ext in EXCLUDED_EXTENSIONS:
            return True

    return False


def collect_backup_files(addons_path, userdata_path, include_databases=True):
    """Walk addons and userdata trees, returning list of (absolute_path, archive_arcname)."""
    file_list = []

    # 1. Addons directory
    if os.path.isdir(addons_path):
        for root, dirs, files in os.walk(addons_path):
            dirs[:] = [d for d in dirs if not should_exclude(dir_name=d)]
            for f in files:
                abs_f = os.path.join(root, f)
                rel_f = os.path.relpath(abs_f, addons_path)
                arc_name = f"addons/{rel_f}".replace("\\", "/")
                if not should_exclude(file_name=f, rel_path=arc_name, include_databases=include_databases):
                    file_list.append((abs_f, arc_name))

    # 2. Userdata directory
    if os.path.isdir(userdata_path):
        for root, dirs, files in os.walk(userdata_path):
            dirs[:] = [d for d in dirs if not should_exclude(dir_name=d)]
            for f in files:
                abs_f = os.path.join(root, f)
                rel_f = os.path.relpath(abs_f, userdata_path)
                arc_name = f"userdata/{rel_f}".replace("\\", "/")
                if not should_exclude(file_name=f, rel_path=arc_name, include_databases=include_databases):
                    file_list.append((abs_f, arc_name))

    return file_list


def create_backup():
    """Interactive backup routine using standard Kodi dialogs."""
    dialog = xbmcgui.Dialog()

    # 1. Ask whether to include databases
    include_dbs = dialog.yesno(
        "Dev Toolbox Backup",
        "Do you want to include Kodi databases (Addons, Textures, Videos, Music)?\n\n[COLOR FF00D4FF]Note:[/COLOR] Databases contain library scrape data and addon enabled states.",
        yeslabel="Include Databases",
        nolabel="Exclude Databases"
    )

    # 2. Select destination folder
    dest_dir = dialog.browse(
        3,  # BROWSE_TYPE_DIRECTORY
        "Select Backup Destination Directory",
        "files"
    )
    if not dest_dir:
        return

    dest_dir = xbmcvfs.translatePath(dest_dir)
    if not os.path.isdir(dest_dir):
        dialog.ok("Backup Error", f"Selected destination directory does not exist:\n{dest_dir}")
        return

    # Generate filename
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    kodi_info = get_current_kodi_info()
    archive_name = f"kodi_backup_{kodi_info['major_version']}_{timestamp}.zip"
    archive_path = os.path.join(dest_dir, archive_name)

    addons_path = xbmcvfs.translatePath("special://home/addons")
    userdata_path = xbmcvfs.translatePath("special://masterprofile/")

    # Progress dialog
    dp = xbmcgui.DialogProgress()
    dp.create("Kodi Backup", "Scanning addons and userdata files...")

    files_to_pack = collect_backup_files(addons_path, userdata_path, include_databases=include_dbs)
    total_files = len(files_to_pack)

    if total_files == 0:
        dp.close()
        dialog.ok("Backup Error", "No files found to backup.")
        return

    manifest_data = {
        "backup_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "kodi_build": kodi_info["build_version"],
        "kodi_major": kodi_info["major_version"],
        "includes_databases": include_dbs,
        "total_files": total_files
    }

    try:
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
            # Write manifest
            zf.writestr(MANIFEST_FILENAME, json.dumps(manifest_data, indent=2))

            for idx, (abs_path, arc_name) in enumerate(files_to_pack):
                if dp.iscanceled():
                    dp.close()
                    if os.path.exists(archive_path):
                        try:
                            os.remove(archive_path)
                        except Exception:
                            pass
                    dialog.notification("Kodi Backup", "Backup cancelled by user", xbmcgui.NOTIFICATION_WARNING, 3000)
                    return

                pct = int(((idx + 1) / float(total_files)) * 100)
                file_display = os.path.basename(abs_path)
                dp.update(pct, f"Compressing ({idx + 1}/{total_files}):\n{file_display}")

                try:
                    zf.write(abs_path, arc_name)
                except Exception as write_err:
                    xbmc.log(f"[DevToolbox] Warning: Could not pack {abs_path}: {write_err}", xbmc.LOGWARNING)

        dp.close()

        size_mb = os.path.getsize(archive_path) / (1024 * 1024.0)
        dialog.ok(
            "Backup Completed",
            f"Backup created successfully!\n\nArchive: [COLOR FF00D4FF]{archive_name}[/COLOR]\nSize: {size_mb:.2f} MB\nFiles: {total_files}\nPath: {dest_dir}"
        )
    except Exception as e:
        dp.close()
        xbmc.log(f"[DevToolbox] Backup creation failed: {e}", xbmc.LOGERROR)
        dialog.ok("Backup Error", f"Failed to create backup archive:\n{e}")


def restore_backup():
    """Interactive restore routine using standard Kodi dialogs."""
    dialog = xbmcgui.Dialog()

    # 1. Select backup zip file
    zip_path = dialog.browse(
        1,  # BROWSE_TYPE_FILE
        "Select Backup Archive (.zip)",
        "files",
        mask=".zip"
    )
    if not zip_path:
        return

    zip_path = xbmcvfs.translatePath(zip_path)
    if not os.path.isfile(zip_path) or not zip_path.lower().endswith(".zip"):
        dialog.ok("Restore Error", f"Invalid backup file selected:\n{zip_path}")
        return

    # 2. Read and validate manifest & detect path layout
    manifest = {}
    prefix = ""
    has_manifest = False

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            all_names = [n.replace("\\", "/") for n in zf.namelist()]
            if MANIFEST_FILENAME in all_names:
                has_manifest = True
                try:
                    raw = zf.read(MANIFEST_FILENAME).decode("utf-8")
                    manifest = json.loads(raw)
                except Exception as m_err:
                    xbmc.log(f"[DevToolbox] Warning parsing manifest: {m_err}", xbmc.LOGWARNING)

            # Determine path prefix (handle archives wrapped in top-level directories)
            # Check direct top-level
            has_direct_addons = any(n.startswith("addons/") for n in all_names)
            has_direct_userdata = any(n.startswith("userdata/") for n in all_names)

            if not has_direct_addons and not has_direct_userdata:
                # Try finding nested prefix like "<root_dir>/addons/" or "<root_dir>/userdata/"
                for name in all_names:
                    parts = name.split("/")
                    if len(parts) > 1 and parts[1] in ("addons", "userdata"):
                        prefix = parts[0] + "/"
                        break

    except Exception as e:
        dialog.ok("Restore Error", f"Unable to read archive metadata:\n{e}")
        return

    current_kodi = get_current_kodi_info()
    backup_major = manifest.get("kodi_major")

    # 3. Check for Manifest and Kodi version mismatch
    if has_manifest and backup_major:
        if backup_major != current_kodi["major_version"]:
            mismatch_msg = (
                f"KODI VERSION MISMATCH WARNING!\n\n"
                f"Backup was created on: [COLOR FFFF5555]Kodi {backup_major}[/COLOR]\n"
                f"Current Kodi version is: [COLOR FF00D4FF]Kodi {current_kodi['major_version']}[/COLOR] ({current_kodi['build_version'][:15]})\n\n"
                f"Databases and addon APIs differ across major Kodi releases. Restoring may break your library or cause crashes.\n\n"
                f"Do you want to override and continue anyway?"
            )
            override = dialog.yesno(
                "Version Mismatch Warning",
                mismatch_msg,
                yeslabel="Override & Continue",
                nolabel="Cancel Restore"
            )
            if not override:
                return
    else:
        # Warning for archives without Dev ToolBox manifest
        manifestless_msg = (
            f"ARCHIVE WITHOUT MANIFEST DETECTED!\n\n"
            f"This backup does not contain a Dev ToolBox manifest.\n"
            f"The originating Kodi version cannot be verified.\n\n"
            f"Restoring databases or incompatible addons from an unknown Kodi version may cause instability.\n\n"
            f"Do you want to continue with the restore?"
        )
        cont = dialog.yesno(
            "Unknown Archive Origin",
            manifestless_msg,
            yeslabel="Proceed Anyway",
            nolabel="Cancel Restore"
        )
        if not cont:
            return

    # 4. Choose Restore Mode (Full Replace vs Merge)
    options = [
        "Full Replace (Clean Wipe & Restore) - Deletes existing addons/userdata and restores exact backup",
        "Merge / Update (Add Missing & Overwrite) - Preserves other existing files, updating matching ones"
    ]
    mode_sel = dialog.select("Select Restore Mode:", options)
    if mode_sel < 0:
        return

    is_full_replace = (mode_sel == 0)

    # 5. Final Confirmation
    confirm_msg = (
        f"[COLOR FFFF5555]WARNING: YOU ARE ABOUT TO RESTORE KODI DATA![/COLOR]\n\n"
        f"Archive: {os.path.basename(zip_path)}\n"
        f"Mode: {'FULL REPLACE' if is_full_replace else 'MERGE / UPDATE'}\n\n"
        f"Note: Dev ToolBox will preserve itself during restore to ensure operational stability.\n\n"
        f"Are you sure you want to proceed?"
    )
    if not dialog.yesno("Confirm Restore", confirm_msg, yeslabel="Yes, Restore Now", nolabel="Cancel"):
        return

    addons_dest = xbmcvfs.translatePath("special://home/addons")
    userdata_dest = xbmcvfs.translatePath("special://masterprofile/")

    current_addon_id = "plugin.program.devtoolbox"

    dp = xbmcgui.DialogProgress()
    dp.create("Restoring Kodi", "Preparing target directories...")

    try:
        # Full replace wiping step (preserves plugin.program.devtoolbox to avoid execution crash)
        if is_full_replace:
            dp.update(10, "Cleaning existing addons directory...")
            if os.path.isdir(addons_dest):
                for item in os.listdir(addons_dest):
                    if item == current_addon_id:
                        continue  # Keep self alive
                    p = os.path.join(addons_dest, item)
                    try:
                        if os.path.isdir(p):
                            shutil.rmtree(p, ignore_errors=True)
                        else:
                            os.remove(p)
                    except Exception:
                        pass

            dp.update(20, "Cleaning existing userdata directory...")
            if os.path.isdir(userdata_dest):
                for item in os.listdir(userdata_dest):
                    p = os.path.join(userdata_dest, item)
                    try:
                        if os.path.isdir(p):
                            shutil.rmtree(p, ignore_errors=True)
                        else:
                            os.remove(p)
                    except Exception:
                        pass

        # Extraction step
        with zipfile.ZipFile(zip_path, "r") as zf:
            members = [
                m for m in zf.infolist()
                if not m.filename.endswith("/")
                and not os.path.basename(m.filename.replace("\\", "/")) == MANIFEST_FILENAME
            ]
            total_members = len(members)

            for idx, member in enumerate(members):
                if dp.iscanceled():
                    dp.close()
                    dialog.notification("Kodi Restore", "Restore cancelled midway", xbmcgui.NOTIFICATION_WARNING, 3000)
                    return

                arc_name = member.filename.replace("\\", "/")

                # Strip detected top-level prefix if any
                if prefix and arc_name.startswith(prefix):
                    normalized_name = arc_name[len(prefix):]
                else:
                    normalized_name = arc_name

                pct = 20 + int(((idx + 1) / float(total_members)) * 75)
                dp.update(pct, f"Extracting ({idx + 1}/{total_members}):\n{os.path.basename(normalized_name)}")

                if normalized_name.startswith("addons/"):
                    sub_path = normalized_name[len("addons/"):]
                    # Protect self: skip overwriting the actively running Dev ToolBox to prevent file lock crashes or mid-flight downgrades
                    addon_root_item = sub_path.split("/")[0] if "/" in sub_path else sub_path
                    if addon_root_item == current_addon_id:
                        continue
                    target_file = os.path.join(addons_dest, sub_path)
                elif normalized_name.startswith("userdata/"):
                    sub_path = normalized_name[len("userdata/"):]
                    target_file = os.path.join(userdata_dest, sub_path)
                else:
                    continue

                target_dir = os.path.dirname(target_file)
                if not os.path.isdir(target_dir):
                    os.makedirs(target_dir, exist_ok=True)

                try:
                    with zf.open(member) as source, open(target_file, "wb") as target:
                        shutil.copyfileobj(source, target)
                except Exception as ext_err:
                    xbmc.log(f"[DevToolbox] Warning: Failed to extract {arc_name}: {ext_err}", xbmc.LOGWARNING)

        dp.update(98, "Updating local addon registry...")
        xbmc.executebuiltin("UpdateLocalAddons")
        time.sleep(0.3)

        dp.close()

        # Prompt for immediate termination/restart
        addon = xbmcaddon.Addon("plugin.program.devtoolbox")
        force_close_enabled = addon.getSettingBool("restore_force_close") if hasattr(addon, "getSettingBool") else (addon.getSetting("restore_force_close").lower() == "true")

        if force_close_enabled:
            restart_msg = (
                "[COLOR FF55FF55]Restore completed successfully![/COLOR]\n\n"
                "To ensure freshly restored SQLite databases and settings are NOT overwritten "
                "by Kodi's in-memory shutdown hooks, Kodi must be closed immediately.\n\n"
                "Force close Kodi now?"
            )
            do_kill = dialog.yesno(
                "Restore Completed",
                restart_msg,
                yeslabel="Force Close Now",
                nolabel="Close Later"
            )
            if do_kill:
                force_kill_kodi()
            else:
                xbmc.executebuiltin("Container.Refresh")
        else:
            do_restart = dialog.yesno(
                "Restore Completed",
                "Restore completed successfully!\n\nKodi MUST be restarted immediately so databases, skin settings, and restored addons reload properly.\n\nRestart Kodi now?",
                yeslabel="Restart Now",
                nolabel="Restart Later"
            )
            if do_restart:
                xbmc.executebuiltin("RestartApp")
            else:
                xbmc.executebuiltin("Container.Refresh")

    except Exception as e:
        dp.close()
        xbmc.log(f"[DevToolbox] Restore operation failed: {e}", xbmc.LOGERROR)
        dialog.ok("Restore Error", f"Failed to restore backup:\n{e}")


def show_backup_restore_menu():
    """Main entry point dialog displaying Backup, Restore, or Guide options."""
    dialog = xbmcgui.Dialog()
    options = [
        "Create Backup Archive... (Clean ZIP of Addons & Userdata)",
        "Restore from Backup Archive... (Full Replace or Merge Mode)",
        "Backup & Restore Guide (Strategy & Manifest Reference)"
    ]
    sel = dialog.select("Kodi Backup & Restore", options)
    if sel == 0:
        create_backup()
    elif sel == 1:
        restore_backup()
    elif sel == 2:
        from .windows.backup_guide import show_backup_guide
        show_backup_guide()
