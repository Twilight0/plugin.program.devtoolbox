# -*- coding: utf-8 -*-
"""
Theme Manager for Dev Toolbox
Manages artwork themes and coordinates distinct asset paths to bypass Kodi's texture cache.
"""
import os
import re
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

ADDON_ID = "plugin.program.devtoolbox"

THEMES = {
    "default": {
        "id": "default",
        "name": "Default (Neon Cyber Suite)",
        "icon_rel": "resources/media/icon_default.png",
        "fanart_rel": "resources/media/fanart_default.jpg",
    },
    "cyber": {
        "id": "cyber",
        "name": "Cyber Workstation HUD (Set 1)",
        "icon_rel": "resources/media/icon_cyber.png",
        "fanart_rel": "resources/media/fanart_cyber.jpg",
    },
    "modern": {
        "id": "modern",
        "name": "Modern Glassmorphism (Set 2)",
        "icon_rel": "resources/media/icon_modern.png",
        "fanart_rel": "resources/media/fanart_modern.jpg",
    },
}

THEME_ORDER = ["default", "cyber", "modern"]


def get_addon():
    try:
        return xbmcaddon.Addon(ADDON_ID)
    except Exception:
        return xbmcaddon.Addon()


def get_addon_path():
    return get_addon().getAddonInfo("path")


def get_current_theme_id():
    addon = get_addon()
    theme_id = addon.getSetting("theme")
    if not theme_id or theme_id not in THEMES:
        theme_id = "default"
    return theme_id


def get_theme_art(theme_id=None):
    """Return absolute paths (icon, fanart) for the selected or active theme."""
    if not theme_id or theme_id not in THEMES:
        theme_id = get_current_theme_id()
    info = THEMES[theme_id]
    addon_path = get_addon_path()
    icon_path = os.path.join(addon_path, info["icon_rel"])
    fanart_path = os.path.join(addon_path, info["fanart_rel"])
    return icon_path, fanart_path


def update_addon_xml_assets(theme_id):
    """Update <assets> section in addon.xml so Kodi core sees unique relative paths."""
    if theme_id not in THEMES:
        theme_id = "default"
    info = THEMES[theme_id]
    addon_path = get_addon_path()
    addon_xml_path = os.path.join(addon_path, "addon.xml")

    if not os.path.isfile(addon_xml_path):
        return False

    try:
        with open(addon_xml_path, "r", encoding="utf-8") as f:
            content = f.read()

        new_assets = (
            f"        <assets>\n"
            f"            <icon>{info['icon_rel']}</icon>\n"
            f"            <fanart>{info['fanart_rel']}</fanart>\n"
            f"        </assets>"
        )

        assets_pattern = re.compile(r"\s*<assets>.*?</assets>", re.DOTALL)
        if assets_pattern.search(content):
            new_content = assets_pattern.sub(f"\n{new_assets}", content, count=1)
        else:
            closing_metadata = "</extension>"
            idx = content.rfind(closing_metadata)
            if idx != -1:
                new_content = content[:idx] + f"{new_assets}\n    " + content[idx:]
            else:
                new_content = content

        if new_content != content:
            with open(addon_xml_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True
    except Exception as e:
        xbmc.log(f"[DevToolbox] Error updating addon.xml assets: {e}", xbmc.LOGWARNING)
    return False


def apply_theme(theme_id, notify=True):
    """Set the theme in addon settings, update addon.xml, and refresh container."""
    if theme_id not in THEMES:
        theme_id = "default"
    addon = get_addon()
    addon.setSetting("theme", theme_id)
    update_addon_xml_assets(theme_id)

    name = THEMES[theme_id]["name"]
    if notify:
        try:
            msg = addon.getLocalizedString(30009) % name
        except Exception:
            msg = f"Theme set to: {name}. Restart Kodi to apply addon.xml changes."
        xbmcgui.Dialog().notification(
            "Dev Toolbox",
            msg,
            xbmcgui.NOTIFICATION_INFO,
            3500,
            sound=False
        )
    xbmc.executebuiltin("Container.Refresh")


def change_theme_dialog():
    """Interactive theme selection modal."""
    current = get_current_theme_id()
    options = []
    keys = []
    current_index = 0

    for idx, key in enumerate(THEME_ORDER):
        theme_info = THEMES[key]
        marker = " [COLOR FF55FF55](Active)[/COLOR]" if key == current else ""
        options.append(f"{theme_info['name']}{marker}")
        keys.append(key)
        if key == current:
            current_index = idx

    dialog = xbmcgui.Dialog()
    selected = dialog.select("Select Dev Toolbox Artwork Theme", options, preselect=current_index)
    if selected >= 0:
        chosen_key = keys[selected]
        apply_theme(chosen_key, notify=True)


def sync_theme_if_needed():
    """Ensure addon.xml assets match the current theme setting."""
    current = get_current_theme_id()
    addon_path = get_addon_path()
    addon_xml_path = os.path.join(addon_path, "addon.xml")
    if not os.path.isfile(addon_xml_path):
        return

    try:
        with open(addon_xml_path, "r", encoding="utf-8") as f:
            content = f.read()

        expected_icon = THEMES[current]["icon_rel"]
        if f"<icon>{expected_icon}</icon>" not in content:
            update_addon_xml_assets(current)
    except Exception:
        pass
