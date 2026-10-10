# -*- coding: utf-8 -*-
"""
Keymap Editor window using a custom WindowXML
Supports multi-scope keymapping (Global, FullscreenVideo, Home, VideoOSD, VirtualKeyboard, etc.)
"""
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import xbmc
import xbmcgui
import xbmcvfs

# XML Control IDs
CONTROL_LIST = 100
BTN_SCOPE = 200
BTN_ADD = 201
BTN_EDIT = 202
BTN_DELETE = 203
BTN_RESET = 204
BTN_SAVE = 205
BTN_CLOSE = 206
BTN_SWITCH_SCOPE = 207

AVAILABLE_SCOPES = [
    "global",
    "FullscreenVideo",
    "Home",
    "VideoOSD",
    "VirtualKeyboard",
    "Visualisation",
    "FileManager",
    "Pictures",
    "Music",
    "Videos",
    "DialogSelect",
    "DialogConfirm"
]

COMMON_ACTIONS = [
    "ReloadSkin()",
    "Skin.ToggleDebug()",
    "ToggleDebug()",
    "ActivateWindow(Home)",
    "ActivateWindow(FileManager)",
    "ActivateWindow(Settings)",
    "ActivateWindow(addonbrowser)",
    "TakeScreenshot",
    "Notification(Dev, Key Triggered, 2000)",
    "Action(Back)",
    "Action(ContextMenu)",
    "Action(Info)",
    "Action(Pause)",
    "Action(Play)",
    "Action(Stop)",
    "Action(ShowSubtitles)",
    "Action(AudioDelay)",
    "Action(NextSubtitle)",
    "Action(VolumeUp)",
    "Action(VolumeDown)",
    "Action(Mute)",
    "Action(StepForward)",
    "Action(StepBack)",
    "Action(BigStepForward)",
    "Action(BigStepBack)",
    "RunScript(plugin.program.devtoolbox)",
]

DEFAULT_KEYMAPS = {
    "global": [
        ("f5", "ReloadSkin()"),
        ("f7", "Skin.ToggleDebug()"),
        ("f8", "TakeScreenshot"),
        ("f9", "ActivateWindow(FileManager)"),
        ("f10", "ActivateWindow(Settings)"),
        ("c", "Action(ContextMenu)"),
        ("i", "Action(Info)"),
        ("space", "Action(Pause)"),
        ("x", "Action(Stop)"),
    ],
    "FullscreenVideo": [
        ("space", "Action(Pause)"),
        ("x", "Action(Stop)"),
        ("m", "Action(ShowOSD)"),
        ("z", "Action(AspectRatio)"),
    ],
    "Home": [
        ("f5", "ReloadSkin()"),
    ]
}


class KeymapWindow(xbmcgui.WindowXML):
    def __init__(self, *args, **kwargs):
        super(KeymapWindow, self).__init__(*args, **kwargs)
        self.keymap_dir = xbmcvfs.translatePath("special://userdata/keymaps")
        self.keymap_file = os.path.join(self.keymap_dir, "devtoolbox_keymap.xml")
        self.current_scope = "global"
        # dict: {scope_name: [(key, action), ...]}
        self.scope_data = {}
        self.modified = False

    def onInit(self):
        self.load_all_keymaps()
        self.update_scope_button()
        self.populate_list()
        self.setFocusId(CONTROL_LIST)

    def load_all_keymaps(self):
        self.scope_data = {s: [] for s in AVAILABLE_SCOPES}

        if os.path.exists(self.keymap_file):
            try:
                tree = ET.parse(self.keymap_file)
                root = tree.getroot()
                for scope_elem in root:
                    scope_name = scope_elem.tag
                    kb_elem = scope_elem.find("keyboard")
                    mappings = []
                    if kb_elem is not None:
                        for child in kb_elem:
                            mappings.append((child.tag, child.text or ""))
                    self.scope_data[scope_name] = mappings
            except Exception as e:
                xbmc.log(f"[DevToolbox] Error reading keymap file: {e}", xbmc.LOGERROR)

        # Seed defaults if completely empty
        if not any(self.scope_data.values()):
            for sc, lst in DEFAULT_KEYMAPS.items():
                self.scope_data[sc] = list(lst)

    def update_scope_button(self):
        try:
            scope_btn = self.getControl(BTN_SCOPE)
            scope_btn.setLabel(f"Scope: [COLOR FFFFA800]{self.current_scope}[/COLOR] (Click to change)")
        except Exception:
            pass

    def populate_list(self):
        list_ctrl = self.getControl(CONTROL_LIST)
        list_ctrl.reset()
        mappings = self.scope_data.get(self.current_scope, [])
        for key, action in mappings:
            item = xbmcgui.ListItem(label=f"Key: {key.upper()}", label2=f"Action: {action}")
            list_ctrl.addItem(item)

    def onClick(self, controlId):
        if controlId == CONTROL_LIST:
            self.edit_selected_action()
        elif controlId in (BTN_SCOPE, BTN_SWITCH_SCOPE):
            self.change_scope()
        elif controlId == BTN_ADD:
            self.add_key_mapping()
        elif controlId == BTN_EDIT:
            self.edit_selected_action()
        elif controlId == BTN_DELETE:
            self.delete_selected_key()
        elif controlId == BTN_RESET:
            self.reset_current_scope_keys()
        elif controlId == BTN_SAVE:
            self.save_and_apply()
        elif controlId == BTN_CLOSE:
            self.close()

    def onAction(self, action):
        action_id = action.getId()
        if action_id in (9, 10, 92):  # BACK / PREVIOUS_MENU / NAV_BACK
            if self.modified:
                dialog = xbmcgui.Dialog()
                if dialog.yesno("Keymap Editor", "Save modified key mappings before exiting?"):
                    self.save_and_apply()
            self.close()

    def change_scope(self):
        dialog = xbmcgui.Dialog()
        # Offer all scopes plus custom entry
        choices = AVAILABLE_SCOPES + ["(Enter Custom Scope / Window ID...)"]
        idx = dialog.select(f"Select Keymap Scope (Current: {self.current_scope})", choices)
        if idx < 0:
            return
        if idx == len(AVAILABLE_SCOPES):
            custom = dialog.input("Enter Window Name or Window ID (e.g. MyVideoNav, Visualisation):")
            if not custom:
                return
            scope_name = custom.strip()
            if scope_name not in self.scope_data:
                self.scope_data[scope_name] = []
            self.current_scope = scope_name
        else:
            self.current_scope = AVAILABLE_SCOPES[idx]

        self.update_scope_button()
        self.populate_list()

    def get_selected_index(self):
        list_ctrl = self.getControl(CONTROL_LIST)
        pos = list_ctrl.getSelectedPosition()
        mappings = self.scope_data.get(self.current_scope, [])
        if pos < 0 or pos >= len(mappings):
            return -1
        return pos

    def add_key_mapping(self):
        dialog = xbmcgui.Dialog()
        key_name = dialog.input(f"[{self.current_scope}] Enter Key identifier (e.g. f5, c, space):", type=xbmcgui.INPUT_ALPHANUM)
        if not key_name:
            return
        key_name = key_name.strip().lower()

        choices = ["(Enter Custom Kodi Action...)"] + COMMON_ACTIONS
        choice_idx = dialog.select(f"Choose Action for '{key_name}' [{self.current_scope}]", choices)
        if choice_idx < 0:
            return
        if choice_idx == 0:
            action = dialog.input(f"Action for '{key_name}':", type=xbmcgui.INPUT_ALPHANUM)
            if not action:
                return
        else:
            action = choices[choice_idx]

        if self.current_scope not in self.scope_data:
            self.scope_data[self.current_scope] = []
        self.scope_data[self.current_scope].append((key_name, action))
        self.modified = True
        self.populate_list()
        self.getControl(CONTROL_LIST).selectItem(len(self.scope_data[self.current_scope]) - 1)

    def edit_selected_action(self):
        idx = self.get_selected_index()
        if idx == -1:
            xbmcgui.Dialog().notification("Dev Toolbox", "Select a key binding first", xbmcgui.NOTIFICATION_INFO, 2000)
            return
        mappings = self.scope_data[self.current_scope]
        key_name, current_action = mappings[idx]
        dialog = xbmcgui.Dialog()

        choices = ["(Custom Action...)"] + COMMON_ACTIONS
        choice_idx = dialog.select(f"Change Action for '{key_name.upper()}' (Current: {current_action})", choices)
        if choice_idx < 0:
            return
        if choice_idx == 0:
            new_action = dialog.input(f"New Action for '{key_name}':", defaultt=current_action, type=xbmcgui.INPUT_ALPHANUM)
            if not new_action:
                return
        else:
            new_action = choices[choice_idx]

        mappings[idx] = (key_name, new_action)
        self.modified = True
        self.populate_list()
        self.getControl(CONTROL_LIST).selectItem(idx)

    def delete_selected_key(self):
        idx = self.get_selected_index()
        if idx == -1:
            return
        mappings = self.scope_data[self.current_scope]
        key_name, _ = mappings[idx]
        dialog = xbmcgui.Dialog()
        if dialog.yesno("Keymap Editor", f"Remove mapping for '{key_name.upper()}' from scope '{self.current_scope}'?"):
            del mappings[idx]
            self.modified = True
            self.populate_list()

    def reset_current_scope_keys(self):
        dialog = xbmcgui.Dialog()
        if dialog.yesno("Keymap Editor", f"Reset keys for '{self.current_scope}' scope?"):
            if self.current_scope in DEFAULT_KEYMAPS:
                self.scope_data[self.current_scope] = list(DEFAULT_KEYMAPS[self.current_scope])
            else:
                self.scope_data[self.current_scope] = []
            self.modified = True
            self.populate_list()

    def save_and_apply(self):
        try:
            if not os.path.exists(self.keymap_dir):
                os.makedirs(self.keymap_dir, exist_ok=True)

            root = ET.Element("keymap")
            for scope, lst in self.scope_data.items():
                if not lst:
                    continue
                scope_elem = ET.SubElement(root, scope)
                kb_elem = ET.SubElement(scope_elem, "keyboard")
                for key, action in lst:
                    k_elem = ET.SubElement(kb_elem, key.lower())
                    k_elem.text = action

            xml_str = ET.tostring(root, encoding="utf-8")
            parsed = minidom.parseString(xml_str)
            pretty_xml = parsed.toprettyxml(indent="    ")

            with open(self.keymap_file, "w", encoding="utf-8") as f:
                f.write(pretty_xml)

            # Reload keymaps into Kodi
            xbmc.executebuiltin("Action(reloadkeymaps)")
            self.modified = False
            total_keys = sum(len(v) for v in self.scope_data.values())
            xbmcgui.Dialog().notification("Keymap Editor", f"Saved {total_keys} keys across scopes!", xbmcgui.NOTIFICATION_INFO, 3000)
        except Exception as e:
            xbmcgui.Dialog().ok("Error Saving Keymap", str(e))
