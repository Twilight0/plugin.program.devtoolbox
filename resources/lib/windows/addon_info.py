# -*- coding: utf-8 -*-
"""
Custom safe Addon Information Dialog using WindowXML
Avoids Kodi's native DialogAddonInfo null-pointer crash on custom/virtual items
"""
import xbmcgui
from ..toggles import execute_jsonrpc


class AddonInfoWindow(xbmcgui.WindowXML):
    def __init__(self, *args, **kwargs):
        self.addon_id = kwargs.pop("addon_id", "")
        self.details = kwargs.pop("details", {})
        self.action_requested = None  # Tracks if user requested an action after window closes
        super(AddonInfoWindow, self).__init__(*args, **kwargs)

    def onInit(self):
        name = self.details.get("name") or self.addon_id
        version = self.details.get("version", "1.0.0")
        author = self.details.get("author", "Unknown")
        path = self.details.get("path", "")
        summary = self.details.get("summary", "")
        desc = self.details.get("description", "")
        is_enabled = self.details.get("enabled", True)
        icon = self.details.get("thumbnail", "")
        fanart = self.details.get("fanart", "")

        try:
            # Set fanart backdrop and preview
            if fanart:
                self.getControl(9).setImage(fanart)
                self.getControl(15).setImage(fanart)
                self.getControl(15).setVisible(True)
            else:
                self.getControl(15).setVisible(False)

            if icon:
                self.getControl(10).setImage(icon)

            self.getControl(11).setLabel(f"{name} [COLOR FF8A9BA8]v{version}[/COLOR]")
            self.getControl(12).setLabel(f"ID: {self.addon_id}   |   Author: {author}")
            self.getControl(13).setLabel(f"Path: {path}")
            state_text = "[COLOR FF55FF55]Status: Enabled[/COLOR]" if is_enabled else "[COLOR FFFF5555]Status: Disabled[/COLOR]"
            self.getControl(14).setLabel(state_text)

            body_sections = []
            if summary:
                body_sections.append(f"[B][COLOR FF00D4FF]Summary:[/COLOR][/B]\n{summary}")
            if desc:
                body_sections.append(f"[B][COLOR FF00D4FF]Description:[/COLOR][/B]\n{desc}")

            deps = self.details.get("dependencies", [])
            if deps:
                dep_lines = []
                for d in deps:
                    d_id = d.get("addonid", "")
                    d_ver = d.get("version", "")
                    d_opt = " [COLOR FF8A9BA8](Optional)[/COLOR]" if d.get("optional") else ""
                    dep_lines.append(f"  • [COLOR FFFFA800]{d_id}[/COLOR] (min v{d_ver}){d_opt}")
                body_sections.append(f"[B][COLOR FF00D4FF]Dependencies ({len(deps)}):[/COLOR][/B]\n" + "\n".join(dep_lines))

            self.getControl(20).setText("\n\n".join(body_sections).strip())
            self.setFocusId(101)
        except Exception:
            pass

    def onClick(self, controlId):
        if controlId == 101:  # Settings
            from ..addons_manager import open_addon_settings
            open_addon_settings(self.addon_id)
        elif controlId == 102:  # Toggle
            from ..addons_manager import toggle_addon_state
            is_enabled = self.details.get("enabled", True)
            toggle_addon_state(self.addon_id, is_enabled)
            self.details["enabled"] = not is_enabled
            state_text = "[COLOR FF55FF55]Status: Enabled[/COLOR]" if self.details["enabled"] else "[COLOR FFFF5555]Status: Disabled[/COLOR]"
            self.getControl(14).setLabel(state_text)
        elif controlId == 103:  # Edit addon.xml
            self.action_requested = "edit_xml"
            self.close()
        elif controlId == 104:  # Close
            self.close()

    def onAction(self, action):
        action_id = action.getId()
        if action_id in (9, 10, 92):
            self.close()
