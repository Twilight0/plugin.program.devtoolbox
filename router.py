# -*- coding: utf-8 -*-
"""
Dev Toolbox - Entry Router & Plugin Dispatcher
"""
import sys
import urllib.parse
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

from resources.lib.editor import browse_and_open_editor
from resources.lib.toggles import toggle_kodi_debug_logging, toggle_skin_debugging, reload_skin, restart_kodi
from resources.lib.addons_manager import (
    list_addons_directory,
    open_addon_settings,
    show_addon_info,
    toggle_addon_state,
    manage_addon_dialog,
    open_addon_in_editor,
)
from resources.lib.log_tools import view_kodi_log, upload_kodi_log
from resources.lib.windows.keymap import KeymapWindow
from resources.lib.theme_manager import (
    get_theme_art,
    change_theme_dialog,
    sync_theme_if_needed,
    apply_theme
)


ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo("id")
ADDON_PATH = ADDON.getAddonInfo("path")


def is_menu_item_enabled(setting_id):
    """Check if a main menu item is enabled in settings (default True)."""
    val = ADDON.getSetting(setting_id)
    if val == "":
        return True
    return val.lower() == "true"


def build_menu(handle, base_url):
    """Render the Dev Toolbox root directory menu."""
    xbmcplugin.setContent(handle, "files")

    tools = [
        (
            "menu_editor",
            "[COLOR FF00D4FF]In-GUI Code & Text Editor[/COLOR]",
            "Edit scripts, XMLs, and run test Python files with syntax highlighting & completions",
            f"{base_url}?action=editor",
            False
        ),
        (
            "menu_toggle_debug",
            "[COLOR FFFFA800]Toggle Kodi Debug Logging[/COLOR]",
            "Toggle on-screen debug info overlay and verbose logging",
            f"{base_url}?action=toggle_debug",
            False
        ),
        (
            "menu_toggle_skin_debug",
            "[COLOR FFFFA800]Toggle Skin Debugging[/COLOR]",
            "Toggle skin debug coordinates and focused control IDs",
            f"{base_url}?action=toggle_skin_debug",
            False
        ),
        (
            "menu_reload_skin",
            "[COLOR FFFFA800]Reload Skin Now[/COLOR]",
            "Reload current Kodi skin cache immediately",
            f"{base_url}?action=reload_skin",
            False
        ),
        (
            "menu_addons_manager",
            "[COLOR FF55FF55]Addon Manager & Inspector[/COLOR]",
            "List installed addons, check enabled/disabled states, launch settings or info",
            f"{base_url}?action=addons_list",
            True
        ),
        (
            "menu_log_view",
            "[COLOR FF00D4FF]Kodi Log Viewer[/COLOR]",
            "View full latest kodi.log entries",
            f"{base_url}?action=log_view",
            False
        ),
        (
            "menu_log_view_errors",
            "[COLOR FFFF5555]Kodi Log Viewer (Errors Only)[/COLOR]",
            "Filter kodi.log strictly for ERROR, WARNING, and EXCEPTIONS",
            f"{base_url}?action=log_view_errors",
            False
        ),
        (
            "menu_log_upload",
            "[COLOR FF98C379]Upload Log & Generate QR Code[/COLOR]",
            "Upload kodi.log to hastebin/paste and display QR code for mobile viewing",
            f"{base_url}?action=log_upload",
            False
        ),
        (
            "menu_keymap_editor",
            "[COLOR FFC678DD]Visual Keymap Editor (WindowXML)[/COLOR]",
            "Edit key mappings, actions, and hotkeys using custom XML interface",
            f"{base_url}?action=keymap_editor",
            False
        ),
        (
            "menu_change_theme",
            "[COLOR FF00D4FF]Switch Artwork Theme[/COLOR]",
            "Select and preview visual themes (changes icon and fanart paths to clear cache)",
            f"{base_url}?action=change_theme",
            False
        ),
        (
            None,
            "[COLOR FF8A9BA8]Dev Toolbox Settings[/COLOR]",
            "Configure addon options, themes, and menu item visibility",
            f"{base_url}?action=addon_settings&addonid={ADDON_ID}",
            False
        ),
        (
            "menu_restart_kodi",
            "[COLOR FF8A9BA8]Restart Kodi Application[/COLOR]",
            "Safely restart Kodi process",
            f"{base_url}?action=restart_kodi",
            False
        ),
    ]

    icon_path, fanart_path = get_theme_art()
    try:
        xbmcplugin.setPluginFanart(handle, fanart_path)
    except Exception:
        pass

    for setting_id, title, desc, url, is_folder in tools:
        if setting_id is not None and not is_menu_item_enabled(setting_id):
            continue
        item = xbmcgui.ListItem(label=title)
        item.setArt({
            "icon": icon_path,
            "fanart": fanart_path,
            "thumb": icon_path
        })
        xbmcplugin.addDirectoryItem(handle, url, item, isFolder=is_folder)

    xbmcplugin.endOfDirectory(handle, succeeded=True)


def open_keymap_editor():
    """Launch the custom WindowXML keymap editor window."""
    window = KeymapWindow(
        "script-devtoolbox-keymap.xml",
        ADDON_PATH,
        "Default",
        "720p"
    )
    window.doModal()
    del window


def run():
    base_url = sys.argv[0]
    handle = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] != "" else -1
    params_str = sys.argv[2][1:] if len(sys.argv) > 2 and sys.argv[2] else ""
    params = dict(urllib.parse.parse_qsl(params_str))

    # Synchronize addon.xml assets with current theme setting if changed externally
    try:
        sync_theme_if_needed()
    except Exception:
        pass

    action = params.get("action")

    if not action:
        if handle >= 0:
            build_menu(handle, base_url)
        else:
            browse_and_open_editor()
        return

    if action == "editor":
        filepath = params.get("filepath")
        from resources.lib.editor import open_rich_editor
        open_rich_editor(filepath=filepath)
    elif action == "toggle_debug":
        toggle_kodi_debug_logging()
    elif action == "toggle_skin_debug":
        toggle_skin_debugging()
    elif action == "reload_skin":
        reload_skin()
    elif action == "restart_kodi":
        restart_kodi()
    elif action == "addons_list":
        list_addons_directory(handle, base_url)
    elif action == "addon_settings":
        addon_id = params.get("addonid")
        if addon_id:
            open_addon_settings(addon_id)
    elif action == "addon_info":
        addon_id = params.get("addonid")
        if addon_id:
            show_addon_info(addon_id)
    elif action == "addon_toggle":
        addon_id = params.get("addonid")
        state_bool = params.get("state", "True").lower() == "true"
        if addon_id:
            toggle_addon_state(addon_id, state_bool)
    elif action == "addon_manage":
        addon_id = params.get("addonid")
        name = params.get("name", addon_id)
        if addon_id:
            manage_addon_dialog(addon_id, name)
    elif action == "addon_edit_xml":
        addon_id = params.get("addonid")
        if addon_id:
            open_addon_in_editor(addon_id, mode="xml")
    elif action == "log_view":
        view_kodi_log(filter_errors=False)
    elif action == "log_view_errors":
        view_kodi_log(filter_errors=True)
    elif action == "log_upload":
        upload_kodi_log()
    elif action == "keymap_editor":
        open_keymap_editor()
    elif action == "change_theme":
        theme_id = params.get("theme_id")
        if theme_id:
            apply_theme(theme_id)
        else:
            change_theme_dialog()


if __name__ == "__main__":
    run()
