# -*- coding: utf-8 -*-
"""
Dev Toolbox - Debug & Developer Toggles
"""
import json
import xbmc
import xbmcgui


def execute_jsonrpc(method, params=None):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "id": 1
    }
    if params:
        payload["params"] = params
    try:
        response_str = xbmc.executeJSONRPC(json.dumps(payload))
        return json.loads(response_str).get("result", {})
    except Exception as e:
        xbmc.log(f"[DevToolbox] JSONRPC Error: {e}", xbmc.LOGERROR)
        return {}


def get_setting_bool(setting_id):
    res = execute_jsonrpc("Settings.GetSettingValue", {"setting": setting_id})
    return bool(res.get("value", False))


def set_setting_bool(setting_id, value):
    return execute_jsonrpc("Settings.SetSettingValue", {"setting": setting_id, "value": value})


def toggle_kodi_debug_logging():
    """Toggle debug logging silently without audio chime."""
    curr = get_setting_bool("debug.showloginfo")
    new_state = not curr
    set_setting_bool("debug.showloginfo", new_state)
    status_str = "ENABLED" if new_state else "DISABLED"
    # sound=False ensures silent notification
    xbmcgui.Dialog().notification("Kodi Debug Logging", f"Debug Overlay & Logging: {status_str}", xbmcgui.NOTIFICATION_INFO, 2000, sound=False)


def toggle_skin_debugging():
    """Toggle skin debug overlay silently without audio chime."""
    xbmc.executebuiltin("Skin.ToggleDebug()")
    xbmcgui.Dialog().notification("Dev Toolbox", "Toggled Skin Debug Overlay", xbmcgui.NOTIFICATION_INFO, 2000, sound=False)


def reload_skin():
    xbmc.executebuiltin("ReloadSkin()")
    xbmcgui.Dialog().notification("Dev Toolbox", "Skin reloaded successfully", xbmcgui.NOTIFICATION_INFO, 2000, sound=False)


def restart_kodi():
    dialog = xbmcgui.Dialog()
    if dialog.yesno("Dev Toolbox", "Do you want to restart Kodi?"):
        xbmc.executebuiltin("RestartApp")
