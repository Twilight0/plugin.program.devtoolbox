# -*- coding: utf-8 -*-
"""
Dev Toolbox - Addon Manager & Inspector
Lists installed addons with enabled/disabled states and provides direct actions (Settings, Info, Enable/Disable)
"""

import os
import urllib.parse
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs
from .toggles import execute_jsonrpc


def get_all_addons():
    """Retrieve all addons with state and metadata from JSONRPC."""
    res = execute_jsonrpc("Addons.GetAddons", {
        "properties": ["name", "version", "summary", "description", "path", "author", "thumbnail", "fanart", "enabled"]
    })
    return res.get("addons", [])


def list_addons_directory(handle, base_url):
    """List addons as directory items with custom context menu actions."""
    addons = get_all_addons()
    # Sort addons alphabetically by name
    addons.sort(key=lambda x: (x.get("name") or x.get("addonid", "")).lower())

    for addon in addons:
        addon_id = addon.get("addonid", "")
        name = addon.get("name") or addon_id
        version = addon.get("version", "1.0.0")
        is_enabled = addon.get("enabled", True)
        icon = addon.get("thumbnail", "")
        fanart = addon.get("fanart", "")

        state_label = "[COLOR FF55FF55][ENABLED][/COLOR]" if is_enabled else "[COLOR FFFF5555][DISABLED][/COLOR]"
        title = f"{state_label} {name} [COLOR FF8A9BA8]v{version}[/COLOR]"

        item = xbmcgui.ListItem(label=title)
        art = {}
        if icon:
            art["icon"] = icon
            art["thumb"] = icon
        if fanart:
            art["fanart"] = fanart
        if art:
            item.setArt(art)

        # Add context menu items for direct operations
        context_items = [
            ("Open Settings", f"RunPlugin({base_url}?action=addon_settings&addonid={addon_id})"),
            ("Show Addon Info", f"RunPlugin({base_url}?action=addon_info&addonid={addon_id})"),
            ("Toggle Enable/Disable", f"RunPlugin({base_url}?action=addon_toggle&addonid={addon_id}&state={str(is_enabled)})"),
            ("Edit addon.xml", f"RunPlugin({base_url}?action=addon_edit_xml&addonid={addon_id})"),
        ]
        item.addContextMenuItems(context_items, replaceItems=False)

        # Main click action: opens dialog with choices
        url = f"{base_url}?action=addon_manage&addonid={addon_id}&name={name}"
        xbmcplugin.addDirectoryItem(handle, url, item, isFolder=False)

    xbmcplugin.endOfDirectory(handle, succeeded=True)


def open_addon_settings(addon_id):
    xbmc.executebuiltin(f"Addon.OpenSettings({addon_id})")


def resolve_addon_file(addon_id, filename="addon.xml"):
    """Robustly resolve file path for an addon across user and system addon directories."""
    candidates = [
        os.path.join(xbmcvfs.translatePath(f"special://home/addons/{addon_id}/"), filename),
        os.path.join(xbmcvfs.translatePath(f"special://xbmc/addons/{addon_id}/"), filename),
        os.path.join(f"/usr/share/kodi/addons/{addon_id}/", filename),
        os.path.join(f"/usr/lib/kodi/addons/{addon_id}/", filename),
    ]
    # Check if JSON-RPC provides an exact addon path
    res = execute_jsonrpc("Addons.GetAddonDetails", {"addonid": addon_id, "properties": ["path"]})
    reported_path = res.get("addon", {}).get("path")
    if reported_path:
        cand = os.path.join(xbmcvfs.translatePath(reported_path), filename)
        candidates.insert(0, cand)

    for c in candidates:
        if os.path.isfile(c):
            return c

    # Fallback default
    return candidates[0]


def show_addon_info(addon_id):
    """Safe Addon Information viewer that does not trigger native Kodi C++ segfault."""
    res = execute_jsonrpc("Addons.GetAddonDetails", {
        "addonid": addon_id,
        "properties": ["name", "version", "summary", "description", "path", "author", "thumbnail", "fanart", "dependencies", "broken", "rating", "extrainfo", "enabled"]
    })
    details = res.get("addon", {})
    if not details:
        details = {"name": addon_id, "addonid": addon_id}

    from .windows.addon_info import AddonInfoWindow
    addon_path = xbmcaddon.Addon().getAddonInfo("path")
    win = AddonInfoWindow(
        "script-devtoolbox-addoninfo.xml",
        addon_path,
        "Default",
        "720p",
        addon_id=addon_id,
        details=details
    )
    win.doModal()
    action_req = getattr(win, "action_requested", None)
    del win

    if action_req == "edit_xml":
        import xbmc
        xbmc.sleep(100)
        open_addon_in_editor(addon_id, mode="xml")


def toggle_addon_state(addon_id, current_state_bool):
    new_state = not current_state_bool
    execute_jsonrpc("Addons.SetAddonEnabled", {"addonid": addon_id, "enabled": new_state})
    status_str = "ENABLED" if new_state else "DISABLED"
    xbmcgui.Dialog().notification("Addon Manager", f"{addon_id}: {status_str}", xbmcgui.NOTIFICATION_INFO, 2000, sound=False)
    xbmc.executebuiltin("Container.Refresh")


def open_addon_in_editor(addon_id, mode="xml"):
    target_file = None
    if mode == "xml":
        target_file = resolve_addon_file(addon_id, "addon.xml")
    else:
        for cand_name in ["router.py", "default.py", "main.py", "service.py"]:
            f = resolve_addon_file(addon_id, cand_name)
            if os.path.isfile(f):
                target_file = f
                break
        if not target_file:
            target_file = resolve_addon_file(addon_id, "default.py")

    quoted = urllib.parse.quote_plus(target_file)
    xbmc.executebuiltin(f"RunPlugin(plugin://plugin.program.devtoolbox/?action=editor&filepath={quoted})")


def manage_addon_dialog(addon_id, addon_name):
    dialog = xbmcgui.Dialog()
    options = [
        "Open Addon Settings",
        "View Addon Info",
        "Toggle Enable / Disable",
        "Open in Dev Text Editor (addon.xml)",
        "Open in Dev Text Editor (entry script)"
    ]
    idx = dialog.select(f"Manage: {addon_name} ({addon_id})", options)
    if idx == 0:
        open_addon_settings(addon_id)
    elif idx == 1:
        show_addon_info(addon_id)
    elif idx == 2:
        res = execute_jsonrpc("Addons.GetAddonDetails", {"addonid": addon_id, "properties": ["enabled"]})
        curr = res.get("addon", {}).get("enabled", True)
        toggle_addon_state(addon_id, curr)
    elif idx == 3:
        open_addon_in_editor(addon_id, mode="xml")
    elif idx == 4:
        open_addon_in_editor(addon_id, mode="entry")
