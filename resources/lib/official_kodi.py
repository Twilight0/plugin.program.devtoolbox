# -*- coding: utf-8 -*-
"""
Official Kodi Addon & Dependency Installer for Dev Toolbox
Queries https://mirrors.kodi.tv/addons/ against active Kodi version name
and provides manual installation of dependencies (script.module.*) and addons.
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import zipfile

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

from .toggles import execute_jsonrpc

MIRRORS_BASE_URL = "https://mirrors.kodi.tv/addons/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Kodi/DevToolbox"

KODI_CODENAMES = {
    15: "isengard",
    16: "jarvis",
    17: "krypton",
    18: "leia",
    19: "matrix",
    20: "nexus",
    21: "omega",
    22: "piers",
}


def get_kodi_codename(force_refresh=False):
    """
    Query https://mirrors.kodi.tv/addons/ to discover available codenames
    and match against the active Kodi version name.
    """
    available_dirs = []
    try:
        req = urllib.request.Request(MIRRORS_BASE_URL, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        matches = re.findall(r'href=[\"\']([a-zA-Z0-9_\-]+)/[\"\']', html)
        available_dirs = [m for m in matches if m not in ("..", "fancyindex", "addons")]
    except Exception as e:
        xbmc.log(f"[DevToolbox] Error querying mirrors directory: {e}", xbmc.LOGWARNING)

    # Detect current Kodi version
    build_str = xbmc.getInfoLabel("System.BuildVersion")
    build_lower = build_str.lower()

    # Check direct word match in build string
    for codename in available_dirs:
        if codename in build_lower:
            return codename, available_dirs

    # Extract major version number (e.g., '21' from '21.3 (21.3.0)...')
    major_match = re.search(r"(\d+)\.", build_str)
    if major_match:
        major_num = int(major_match.group(1))
        expected_name = KODI_CODENAMES.get(major_num)
        if expected_name and expected_name in available_dirs:
            return expected_name, available_dirs
        elif expected_name:
            return expected_name, available_dirs

    # Fallback default
    if "omega" in available_dirs:
        return "omega", available_dirs
    return "omega", (available_dirs or ["omega", "nexus", "matrix"])


def get_cached_addons_list(codename, force_refresh=False):
    """
    Fetch and cache the list of addon directories from the Kodi mirror for the given codename.
    """
    temp_dir = xbmcvfs.translatePath("special://temp/")
    cache_file = os.path.join(temp_dir, f"devtoolbox_mirror_{codename}.json")

    # Cache valid for 12 hours
    if not force_refresh and os.path.isfile(cache_file):
        try:
            mtime = os.path.getmtime(cache_file)
            if time.time() - mtime < 43200:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass

    # Fetch fresh list from mirror
    target_url = f"{MIRRORS_BASE_URL}{codename}/"
    addons = []
    try:
        req = urllib.request.Request(target_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        matches = re.findall(r'href=[\"\']([a-zA-Z0-9_\-\.\+]+)/[\"\']', html)
        addons = [m for m in matches if m not in ("..", "fancyindex", "resources")]
        addons = sorted(list(set(addons)))

        # Save cache
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(addons, f)
        except Exception:
            pass
    except Exception as e:
        xbmc.log(f"[DevToolbox] Error fetching mirror addons for {codename}: {e}", xbmc.LOGERROR)
        if os.path.isfile(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

    return addons


def get_addon_zip_versions(codename, addon_id):
    """
    Fetch available zip files from https://mirrors.kodi.tv/addons/{codename}/{addon_id}/
    """
    addon_url = f"{MIRRORS_BASE_URL}{codename}/{addon_id}/"
    zips = []
    try:
        req = urllib.request.Request(addon_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        matches = re.findall(r'href=[\"\']([^\"\']+\.zip)[\"\']', html)
        for m in matches:
            full_url = urllib.parse.urljoin(addon_url, m)
            zips.append((m, full_url))

        # Sort reverse so newest version is typically first
        zips.sort(key=lambda x: x[0], reverse=True)
    except Exception as e:
        xbmc.log(f"[DevToolbox] Error fetching zip versions for {addon_id}: {e}", xbmc.LOGERROR)

    return zips


def is_addon_installed(addon_id):
    """Check if an addon is installed locally."""
    installed_dir = xbmcvfs.translatePath(f"special://home/addons/{addon_id}")
    return os.path.isdir(installed_dir)


def install_addon_zip(codename, addon_id, zip_filename=None, zip_url=None):
    """
    Download zip from Kodi mirror, extract to addons directory, update and enable.
    """
    if not zip_url:
        versions = get_addon_zip_versions(codename, addon_id)
        if not versions:
            xbmcgui.Dialog().notification("Kodi Mirror", f"No zip packages found for {addon_id}", xbmcgui.NOTIFICATION_ERROR, 3000)
            return False

        if len(versions) == 1:
            zip_filename, zip_url = versions[0]
        else:
            # Let user select version
            options = [v[0] for v in versions]
            dialog = xbmcgui.Dialog()
            sel = dialog.select(f"Select Version for {addon_id}:", options)
            if sel < 0:
                return False
            zip_filename, zip_url = versions[sel]

    # Confirm installation
    confirm = xbmcgui.Dialog().yesno(
        "Official Kodi Installer",
        f"Install [COLOR FF00D4FF]{addon_id}[/COLOR] from official Kodi mirror?\n\nPackage: {zip_filename}\nCodename: {codename}",
        yeslabel="Install",
        nolabel="Cancel"
    )
    if not confirm:
        return False

    dp = xbmcgui.DialogProgress()
    dp.create("Official Kodi Installer", f"Downloading {zip_filename}...")

    temp_dir = xbmcvfs.translatePath("special://temp/")
    local_zip = os.path.join(temp_dir, zip_filename)

    try:
        req = urllib.request.Request(zip_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=20) as resp:
            total_size = int(resp.headers.get("content-length", 0))
            downloaded = 0
            chunk_size = 1024 * 32

            with open(local_zip, "wb") as f:
                while True:
                    if dp.iscanceled():
                        dp.close()
                        return False
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        pct = int((downloaded / total_size) * 100)
                        dp.update(pct, f"Downloading {zip_filename}...\n{downloaded // 1024} KB / {total_size // 1024} KB")
                    else:
                        dp.update(50, f"Downloading {zip_filename}...\n{downloaded // 1024} KB")

        dp.update(85, f"Extracting {zip_filename} to addons directory...")
        addons_dest = xbmcvfs.translatePath("special://home/addons/")

        with zipfile.ZipFile(local_zip, "r") as zf:
            zf.extractall(addons_dest)

        dp.update(95, "Updating local Kodi addons registry and enabling...")

        # Update local addons and enable
        xbmc.executebuiltin("UpdateLocalAddons")
        time.sleep(0.3)
        execute_jsonrpc("Addons.SetAddonEnabled", {"addonid": addon_id, "enabled": True})

        dp.close()
        xbmcgui.Dialog().notification(
            "Official Kodi Installer",
            f"Successfully installed & enabled: {addon_id}",
            xbmcgui.NOTIFICATION_INFO,
            3500,
            sound=False
        )
        xbmc.executebuiltin("Container.Refresh")
        return True

    except Exception as e:
        dp.close()
        xbmc.log(f"[DevToolbox] Error downloading/installing {addon_id}: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification("Install Error", str(e), xbmcgui.NOTIFICATION_ERROR, 3500)
        return False
    finally:
        if os.path.isfile(local_zip):
            try:
                os.remove(local_zip)
            except Exception:
                pass


def direct_install_prompt():
    """Prompt user for an addon/module ID and install it from the mirror."""
    codename, _ = get_kodi_codename()
    dialog = xbmcgui.Dialog()
    query = dialog.input(f"Enter Addon or Module ID (Kodi {codename}):", type=xbmcgui.INPUT_ALPHANUM)
    if not query:
        return

    addon_id = query.strip()
    install_addon_zip(codename, addon_id)


def render_official_kodi_root(handle, base_url):
    """Render the top-level directory menu for the Official Kodi Installer."""
    codename, available = get_kodi_codename()
    all_addons = get_cached_addons_list(codename)
    modules = [a for a in all_addons if a.startswith("script.module.")]

    from .theme_manager import get_theme_art
    icon_path, fanart_path = get_theme_art()

    xbmcplugin.setContent(handle, "files")

    items = [
        (
            f"[COLOR FFFFA800]🔍 Search Official Kodi Repository...[/COLOR]",
            f"Search across {len(all_addons)} official addons and python modules for Kodi {codename.capitalize()}",
            f"{base_url}?action=official_kodi_search&codename={codename}",
            True
        ),
        (
            f"[COLOR FF00D4FF]📦 Python Modules & Dependencies ({len(modules)})[/COLOR]",
            f"Browse and install script.module.* dependencies hidden by the native Kodi Addon Manager",
            f"{base_url}?action=official_kodi_browse&type=modules&codename={codename}",
            True
        ),
        (
            f"[COLOR FF55FF55]📂 All Official Kodi Addons ({len(all_addons)})[/COLOR]",
            f"Browse all official addons available in the {codename.capitalize()} repository mirror",
            f"{base_url}?action=official_kodi_browse&type=all&codename={codename}",
            True
        ),
        (
            f"[COLOR FF8A9BA8]⌨️ Install by Addon ID Directly...[/COLOR]",
            f"Manually input an addon or dependency ID (e.g., script.module.requests)",
            f"{base_url}?action=official_kodi_direct&codename={codename}",
            False
        ),
        (
            f"[COLOR FF8A9BA8]🔄 Refresh Official Kodi Mirror Index[/COLOR]",
            f"Re-fetch the directory index from {MIRRORS_BASE_URL}{codename}/",
            f"{base_url}?action=official_kodi_refresh&codename={codename}",
            False
        ),
    ]

    for title, desc, url, is_folder in items:
        item = xbmcgui.ListItem(label=title)
        item.setArt({"icon": icon_path, "fanart": fanart_path, "thumb": icon_path})
        item.setInfo("video", {"plot": desc})
        xbmcplugin.addDirectoryItem(handle, url, item, isFolder=is_folder)

    xbmcplugin.endOfDirectory(handle, succeeded=True)


def render_official_kodi_list(handle, base_url, codename, filter_type="modules", query=None):
    """Render the list of addons/dependencies."""
    all_addons = get_cached_addons_list(codename)

    if query:
        query_lower = query.lower()
        matched = [a for a in all_addons if query_lower in a.lower()]
    elif filter_type == "modules":
        matched = [a for a in all_addons if a.startswith("script.module.")]
    else:
        matched = all_addons

    from .theme_manager import get_theme_art
    icon_path, fanart_path = get_theme_art()

    xbmcplugin.setContent(handle, "files")

    for addon_id in matched:
        installed = is_addon_installed(addon_id)
        status_tag = " [COLOR FF55FF55]✓ Installed[/COLOR]" if installed else " [COLOR FF8A9BA8](Available)[/COLOR]"
        title = f"[COLOR FFFFFFFF]{addon_id}[/COLOR]{status_tag}"

        desc = f"Click to download and install {addon_id} from official mirrors.kodi.tv/addons/{codename}/"
        url = f"{base_url}?action=official_kodi_install&addonid={addon_id}&codename={codename}"

        item = xbmcgui.ListItem(label=title)
        item.setArt({"icon": icon_path, "fanart": fanart_path, "thumb": icon_path})
        item.setInfo("video", {"plot": desc})
        xbmcplugin.addDirectoryItem(handle, url, item, isFolder=False)

    xbmcplugin.endOfDirectory(handle, succeeded=True)


def handle_official_kodi_search(handle, base_url, codename):
    """Prompt user for a search query and display results."""
    dialog = xbmcgui.Dialog()
    query = dialog.input(f"Search Official Kodi {codename.capitalize()} Addons:", type=xbmcgui.INPUT_ALPHANUM)
    if not query:
        return
    render_official_kodi_list(handle, base_url, codename, query=query.strip())
