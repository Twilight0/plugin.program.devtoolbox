# -*- coding: utf-8 -*-
"""
Rich Code & Text Editor Window for Kodi
Features full-screen WindowXML interface, direct inline editing, bulk full-document editing,
syntax highlighting, search/replace, snippets, and script execution.
"""
import os
import re
import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs

# XML Control IDs
CONTROL_LIST = 100
EDIT_DIRECT = 50
BTN_APPLY_DIRECT = 51
LABEL_PATH = 2
LABEL_STATUS = 3
BTN_EDIT_WHOLE = 201
BTN_INSERT_ABOVE = 202
BTN_INSERT_BELOW = 203
BTN_DELETE_LINE = 204
BTN_COMPLETION = 205
BTN_FIND_REPLACE = 206
BTN_OPEN_FILE = 207
BTN_SAVE_FILE = 208
BTN_RUN_SCRIPT = 209
BTN_CLOSE = 210

PY_KEYWORDS = {
    "def", "class", "import", "from", "as", "return", "if", "elif", "else",
    "for", "while", "try", "except", "finally", "with", "yield", "pass", "break",
    "continue", "in", "is", "not", "and", "or", "True", "False", "None", "lambda", "async", "await"
}

KODI_COMPLETIONS = [
    ("xbmc.log(msg, level)", "xbmc.log('Message', xbmc.LOGINFO)"),
    ("xbmc.executebuiltin", "xbmc.executebuiltin('ReloadSkin()')"),
    ("Notification dialog", "xbmcgui.Dialog().notification('Title', 'Message', xbmcgui.NOTIFICATION_INFO, 3000, sound=False)"),
    ("OK dialog", "xbmcgui.Dialog().ok('Title', 'Message')"),
    ("Yes/No dialog", "xbmcgui.Dialog().yesno('Title', 'Do you want to proceed?')"),
    ("Select dialog", "choice = xbmcgui.Dialog().select('Options', ['Option 1', 'Option 2'])"),
    ("Input dialog", "user_text = xbmcgui.Dialog().input('Enter text:', type=xbmcgui.INPUT_ALPHANUM)"),
    ("translatePath special://", "xbmcvfs.translatePath('special://home/')"),
    ("Addon settings getter", "xbmcaddon.Addon().getSetting('setting_id')"),
    ("Addon settings setter", "xbmcaddon.Addon().setSetting('setting_id', 'value')"),
    ("JSONRPC execute", "xbmc.executeJSONRPC('{\"jsonrpc\":\"2.0\",\"method\":\"GUI.ShowNotification\",\"params\":{\"title\":\"Hello\",\"message\":\"World\"},\"id\":1}')"),
]


def highlight_code_line(line, ext="py"):
    """Format code lines with Kodi color tags for rich syntax highlighting."""
    if not line:
        return " "

    leading_spaces = len(line) - len(line.lstrip(" "))
    indent = " " * leading_spaces
    stripped = line.strip()

    if ext in ("py", "python"):
        if stripped.startswith("#"):
            return f"{indent}[COLOR FF5C6370]{stripped}[/COLOR]"

        def replace_str(match):
            return f"[COLOR FF98C379]{match.group(0)}[/COLOR]"
        highlighted = re.sub(r'("[^"]*"|\'[^\']*\')', replace_str, stripped)

        tokens = re.split(r'(\b\w+\b)', highlighted)
        res = []
        for token in tokens:
            if token in PY_KEYWORDS:
                res.append(f"[COLOR FFE06C75]{token}[/COLOR]")
            elif token.startswith("xbmc") or token.startswith("xbmcgui") or token.startswith("xbmcvfs"):
                res.append(f"[COLOR FF61AFEF]{token}[/COLOR]")
            else:
                res.append(token)
        return indent + "".join(res)

    elif ext in ("xml", "json"):
        if stripped.startswith("<!--") and stripped.endswith("-->"):
            return f"{indent}[COLOR FF5C6370]{stripped}[/COLOR]"
        hl = re.sub(r'(</?[\w\:\-]+>?|[/>])', r'[COLOR FFE06C75]\1[/COLOR]', stripped)
        hl = re.sub(r'("[^"]*")', r'[COLOR FF98C379]\1[/COLOR]', hl)
        return indent + hl

    return line


class EditorWindow(xbmcgui.WindowXML):
    def __init__(self, *args, **kwargs):
        self.filepath = kwargs.pop("filepath", None)
        self.lines = []
        self.modified = False
        super(EditorWindow, self).__init__(*args, **kwargs)

    def onInit(self):
        if self.filepath and os.path.exists(self.filepath):
            self.load_file(self.filepath)
        else:
            self.lines = [
                "# Dev Toolbox Python Scratchpad",
                "import xbmc",
                "import xbmcgui",
                "",
                "xbmc.log('Executed from Dev Toolbox editor!', xbmc.LOGINFO)",
                "xbmcgui.Dialog().notification('Dev Toolbox', 'Scratch script executed successfully!', xbmcgui.NOTIFICATION_INFO, 2500, sound=False)"
            ]
            self.filepath = None
            self.modified = False

        self.update_header()
        self.populate_list()
        self.sync_direct_edit_field()
        self.setFocusId(CONTROL_LIST)

    def update_header(self):
        name = os.path.basename(self.filepath) if self.filepath else "Scratchpad (Unsaved)"
        status_flag = "[COLOR FFFF5555]* Modified[/COLOR]" if self.modified else "[COLOR FF55FF55]Saved[/COLOR]"
        self.getControl(LABEL_PATH).setLabel(f"File: [COLOR FFFFFFFF]{name}[/COLOR]   |   {status_flag}   |   Path: {self.filepath or 'N/A'}")
        ext = os.path.splitext(self.filepath)[1].lstrip(".") if self.filepath else "py"
        self.getControl(LABEL_STATUS).setLabel(f"Lines: {len(self.lines)}   |   Syntax: {ext.upper()}   |   Down: Direct Edit box")

    def load_file(self, path):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                self.lines = [l.rstrip("\r\n") for l in f.readlines()]
            self.filepath = path
            self.modified = False
        except Exception as e:
            xbmcgui.Dialog().ok("Editor Error", f"Unable to read file: {e}")
            if not self.lines:
                self.lines = [""]

    def populate_list(self, select_idx=None):
        list_ctrl = self.getControl(CONTROL_LIST)
        list_ctrl.reset()
        ext = os.path.splitext(self.filepath)[1].lstrip(".").lower() if self.filepath else "py"

        for i, line in enumerate(self.lines):
            line_no = f"{i + 1:03d}"
            hl = highlight_code_line(line, ext=ext)
            item = xbmcgui.ListItem(label=line_no, label2=hl)
            list_ctrl.addItem(item)

        if select_idx is not None and 0 <= select_idx < len(self.lines):
            list_ctrl.selectItem(select_idx)
        self.update_header()

    def get_selected_index(self):
        list_ctrl = self.getControl(CONTROL_LIST)
        pos = list_ctrl.getSelectedPosition()
        if pos < 0 or pos >= len(self.lines):
            return -1
        return pos

    def sync_direct_edit_field(self):
        idx = self.get_selected_index()
        if 0 <= idx < len(self.lines):
            try:
                self.getControl(EDIT_DIRECT).setText(self.lines[idx])
            except Exception:
                pass

    def apply_direct_edit(self):
        idx = self.get_selected_index()
        if idx == -1:
            idx = 0
            if not self.lines:
                self.lines.append("")
        try:
            new_text = self.getControl(EDIT_DIRECT).getText()
            if new_text != self.lines[idx]:
                self.lines[idx] = new_text
                self.modified = True
                self.populate_list(select_idx=idx)
                xbmcgui.Dialog().notification("Editor", f"Updated line {idx + 1}", xbmcgui.NOTIFICATION_INFO, 1500, sound=False)
        except Exception:
            pass

    def edit_whole_file(self):
        """Allow directly pasting or editing the entire document content in a multi-line input."""
        current_full = "\n".join(self.lines)
        dialog = xbmcgui.Dialog()
        new_full = dialog.textviewer(f"Full File View ({len(self.lines)} lines)", current_full)
        choice = dialog.select("File Edit Options", ["Replace / Paste Full File Content", "Keep Line-by-Line Mode"])
        if choice == 0:
            pasted = dialog.input("Paste or enter full content (newlines supported):", defaultt=current_full)
            if pasted is not None and pasted != current_full:
                self.lines = pasted.split("\n")
                self.modified = True
                self.populate_list(select_idx=0)
                dialog.notification("Editor", f"Loaded {len(self.lines)} lines", xbmcgui.NOTIFICATION_INFO, 2000, sound=False)

    def onClick(self, controlId):
        if controlId == CONTROL_LIST:
            self.sync_direct_edit_field()
            self.setFocusId(EDIT_DIRECT)
        elif controlId == EDIT_DIRECT:
            self.apply_direct_edit()
        elif controlId == BTN_APPLY_DIRECT:
            self.apply_direct_edit()
        elif controlId == BTN_EDIT_WHOLE:
            self.edit_whole_file()
        elif controlId == BTN_INSERT_ABOVE:
            self.insert_line(above=True)
        elif controlId == BTN_INSERT_BELOW:
            self.insert_line(above=False)
        elif controlId == BTN_DELETE_LINE:
            self.delete_selected_line()
        elif controlId == BTN_COMPLETION:
            self.insert_snippet()
        elif controlId == BTN_FIND_REPLACE:
            self.find_replace()
        elif controlId == BTN_OPEN_FILE:
            self.open_file_dialog()
        elif controlId == BTN_SAVE_FILE:
            self.save_file()
        elif controlId == BTN_RUN_SCRIPT:
            self.run_current_script()
        elif controlId == BTN_CLOSE:
            self.handle_close()

    def onAction(self, action):
        action_id = action.getId()
        if action_id in (9, 10, 92):  # BACK
            self.handle_close()
        elif action_id in (3, 4):  # UP / DOWN
            self.sync_direct_edit_field()

    def handle_close(self):
        if self.modified:
            dialog = xbmcgui.Dialog()
            if dialog.yesno("Dev Editor", "Save modified changes before closing?"):
                self.save_file()
        self.close()

    def insert_line(self, above=False):
        idx = self.get_selected_index()
        if idx == -1:
            idx = len(self.lines)

        target_idx = idx if above else idx + 1
        new_text = xbmcgui.Dialog().input("Enter text for new line:", type=xbmcgui.INPUT_ALPHANUM)
        if new_text is not None:
            self.lines.insert(target_idx, new_text)
            self.modified = True
            self.populate_list(select_idx=target_idx)
            self.sync_direct_edit_field()

    def delete_selected_line(self):
        idx = self.get_selected_index()
        if idx == -1:
            return
        if xbmcgui.Dialog().yesno("Delete Line", f"Delete line {idx + 1}:\n{self.lines[idx]}?"):
            del self.lines[idx]
            if not self.lines:
                self.lines.append("")
            self.modified = True
            new_idx = min(idx, len(self.lines) - 1)
            self.populate_list(select_idx=new_idx)
            self.sync_direct_edit_field()

    def insert_snippet(self):
        dialog = xbmcgui.Dialog()
        labels = [f"{title} -> {code}" for title, code in KODI_COMPLETIONS]
        idx = dialog.select("Select Kodi Snippet / API Completion", labels)
        if idx >= 0:
            snippet_code = KODI_COMPLETIONS[idx][1]
            pos = self.get_selected_index()
            insert_pos = pos + 1 if pos >= 0 else len(self.lines)
            self.lines.insert(insert_pos, snippet_code)
            self.modified = True
            self.populate_list(select_idx=insert_pos)
            self.sync_direct_edit_field()

    def find_replace(self):
        dialog = xbmcgui.Dialog()
        mode = dialog.select("Find / Replace", ["Find Text in Lines", "Replace Text in All Lines"])
        if mode == 0:
            search_str = dialog.input("Search query:")
            if not search_str:
                return
            matches = [i for i, line in enumerate(self.lines) if search_str.lower() in line.lower()]
            if not matches:
                dialog.notification("Search", f"'{search_str}' not found", xbmcgui.NOTIFICATION_INFO, 2000, sound=False)
                return
            match_labels = [f"Line {m + 1}: {self.lines[m]}" for m in matches]
            chosen = dialog.select(f"Found {len(matches)} match(es)", match_labels)
            if chosen >= 0:
                self.populate_list(select_idx=matches[chosen])
                self.sync_direct_edit_field()

        elif mode == 1:
            old_str = dialog.input("Text to find:")
            if not old_str:
                return
            new_str = dialog.input(f"Replace '{old_str}' with:")
            if new_str is None:
                return
            count = 0
            for i, line in enumerate(self.lines):
                if old_str in line:
                    self.lines[i] = line.replace(old_str, new_str)
                    count += 1
            if count > 0:
                self.modified = True
                self.populate_list()
                dialog.notification("Replace", f"Replaced {count} occurrence(s)", xbmcgui.NOTIFICATION_INFO, 2500, sound=False)
            else:
                dialog.notification("Replace", f"'{old_str}' not found", xbmcgui.NOTIFICATION_INFO, 2000, sound=False)

    def open_file_dialog(self):
        if self.modified:
            if xbmcgui.Dialog().yesno("Save Current File?", "Save current file before opening another?"):
                self.save_file()
        path = xbmcgui.Dialog().browse(1, "Open Script / XML File", "files", defaultt=xbmcvfs.translatePath("special://home/"))
        if path and os.path.isfile(path):
            self.load_file(path)
            self.populate_list(select_idx=0)
            self.sync_direct_edit_field()

    def save_file(self):
        if not self.filepath:
            folder = xbmcgui.Dialog().browse(0, "Select Folder to Save", "files", defaultt=xbmcvfs.translatePath("special://home/"))
            if not folder:
                return
            fname = xbmcgui.Dialog().input("Enter file name (e.g. test.py):", defaultt="test_script.py")
            if not fname:
                return
            self.filepath = os.path.join(folder, fname)

        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(self.lines))
            self.modified = False
            self.update_header()
            xbmcgui.Dialog().notification("Dev Editor", f"Saved: {os.path.basename(self.filepath)}", xbmcgui.NOTIFICATION_INFO, 2500, sound=False)
        except Exception as e:
            xbmcgui.Dialog().ok("Save Error", str(e))

    def run_current_script(self):
        if not self.filepath:
            xbmcgui.Dialog().ok("Dev Editor", "Please save the scratchpad to a file before running.")
            return
        self.save_file()
        xbmc.executebuiltin(f"RunScript({self.filepath})")
        xbmcgui.Dialog().notification("Dev Editor", f"Executed: {os.path.basename(self.filepath)}", xbmcgui.NOTIFICATION_INFO, 2000, sound=False)


def open_rich_editor(filepath=None):
    addon_path = xbmcaddon.Addon().getAddonInfo("path")
    win = EditorWindow(
        "script-devtoolbox-editor.xml",
        addon_path,
        "Default",
        "720p",
        filepath=filepath
    )
    win.doModal()
    del win


def browse_and_open_editor():
    open_rich_editor(filepath=None)
