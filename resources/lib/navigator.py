# -*- coding: utf-8 -*-
"""
Dev Toolbox - Main Menu & Navigation Root
Builds the root tool directory and registers top-level navigation routes on urldispatcher.
"""
import sys
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
from urldispatcher import urldispatcher

from .editor import browse_and_open_editor, open_rich_editor
from .toggles import (
    toggle_kodi_debug_logging,
    toggle_skin_debugging,
    reload_skin,
    restart_kodi,
    quit_kodi,
)
from .addons_manager import (
    list_addons_directory,
    open_addon_settings,
    show_addon_info,
    toggle_addon_state,
    manage_addon_dialog,
    open_addon_in_editor,
)
from .log_tools import view_kodi_log, upload_kodi_log
from .windows.keymap import KeymapWindow
from .theme_manager import (
    get_theme_art,
    change_theme_dialog,
    apply_theme,
)
from .official_kodi import (
    render_official_kodi_root,
    render_official_kodi_list,
    handle_official_kodi_search,
    direct_install_prompt,
    install_addon_zip,
    get_kodi_codename,
    get_cached_addons_list,
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
            "menu_official_kodi",
            "[COLOR FF00D4FF]Official Kodi Dependency / Addon Installer[/COLOR]",
            "Search and install dependencies (script.module.*) and addons directly from mirrors.kodi.tv",
            f"{base_url}?action=official_kodi",
            True
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
            "[COLOR FF8A9BA8]Restart Kodi[/COLOR]",
            "Safely restart Kodi process",
            f"{base_url}?action=restart_kodi",
            False
        ),
        (
            "menu_quit_kodi",
            "[COLOR FFFF5555]Quit Kodi[/COLOR]",
            "Safely close and quit Kodi application",
            f"{base_url}?action=quit_kodi",
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


# --- Route Registrations with urldispatcher ---

@urldispatcher.register("root")
def route_root():
    handle = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] != "" else -1
    base_url = sys.argv[0]
    if handle >= 0:
        build_menu(handle, base_url)
    else:
        browse_and_open_editor()


@urldispatcher.register("editor", kwargs=["filepath"])
def route_editor(filepath=None):
    open_rich_editor(filepath=filepath)


@urldispatcher.register("toggle_debug")
def route_toggle_debug():
    toggle_kodi_debug_logging()


@urldispatcher.register("toggle_skin_debug")
def route_toggle_skin_debug():
    toggle_skin_debugging()


@urldispatcher.register("reload_skin")
def route_reload_skin():
    reload_skin()


@urldispatcher.register("restart_kodi")
def route_restart_kodi():
    restart_kodi()


@urldispatcher.register("quit_kodi")
def route_quit_kodi():
    quit_kodi()


@urldispatcher.register("addons_list")
def route_addons_list():
    handle = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] != "" else -1
    base_url = sys.argv[0]
    list_addons_directory(handle, base_url)


@urldispatcher.register("addon_settings", kwargs=["addonid"])
def route_addon_settings(addonid=None):
    if addonid:
        open_addon_settings(addonid)


@urldispatcher.register("addon_info", kwargs=["addonid"])
def route_addon_info(addonid=None):
    if addonid:
        show_addon_info(addonid)


@urldispatcher.register("addon_toggle", kwargs=["addonid", "state"])
def route_addon_toggle(addonid=None, state=True):
    if addonid:
        state_bool = str(state).lower() == "true" if not isinstance(state, bool) else state
        toggle_addon_state(addonid, state_bool)


@urldispatcher.register("addon_manage", kwargs=["addonid", "name"])
def route_addon_manage(addonid=None, name=None):
    if addonid:
        manage_addon_dialog(addonid, name or addonid)


@urldispatcher.register("addon_edit_xml", kwargs=["addonid"])
def route_addon_edit_xml(addonid=None):
    if addonid:
        open_addon_in_editor(addonid, mode="xml")


@urldispatcher.register("log_view")
def route_log_view():
    view_kodi_log(filter_errors=False)


@urldispatcher.register("log_view_errors")
def route_log_view_errors():
    view_kodi_log(filter_errors=True)


@urldispatcher.register("log_upload")
def route_log_upload():
    upload_kodi_log()


@urldispatcher.register("keymap_editor")
def route_keymap_editor():
    window = KeymapWindow(
        "script-devtoolbox-keymap.xml",
        ADDON_PATH,
        "Default",
        "720p"
    )
    window.doModal()
    del window


@urldispatcher.register("change_theme", kwargs=["theme_id"])
def route_change_theme(theme_id=None):
    if theme_id:
        apply_theme(theme_id)
    else:
        change_theme_dialog()


@urldispatcher.register("official_kodi")
def route_official_kodi():
    handle = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] != "" else -1
    base_url = sys.argv[0]
    render_official_kodi_root(handle, base_url)


@urldispatcher.register("official_kodi_browse", kwargs=["codename", "type"])
def route_official_kodi_browse(codename=None, type="modules"):
    handle = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] != "" else -1
    base_url = sys.argv[0]
    cn = codename or get_kodi_codename()[0]
    render_official_kodi_list(handle, base_url, cn, filter_type=type or "modules")


@urldispatcher.register("official_kodi_search", kwargs=["codename"])
def route_official_kodi_search(codename=None):
    handle = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] != "" else -1
    base_url = sys.argv[0]
    cn = codename or get_kodi_codename()[0]
    handle_official_kodi_search(handle, base_url, cn)


@urldispatcher.register("official_kodi_direct")
def route_official_kodi_direct():
    direct_install_prompt()


@urldispatcher.register("official_kodi_install", kwargs=["addonid", "codename"])
def route_official_kodi_install(addonid=None, codename=None):
    if addonid:
        cn = codename or get_kodi_codename()[0]
        install_addon_zip(cn, addonid)


@urldispatcher.register("official_kodi_refresh", kwargs=["codename"])
def route_official_kodi_refresh(codename=None):
    cn = codename or get_kodi_codename()[0]
    get_cached_addons_list(cn, force_refresh=True)
    xbmcgui.Dialog().notification("Kodi Mirror", f"Refreshed {cn} index", xbmcgui.NOTIFICATION_INFO, 2000, sound=False)
    xbmc.executebuiltin("Container.Refresh")
