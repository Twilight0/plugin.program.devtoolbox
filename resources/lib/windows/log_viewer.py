# -*- coding: utf-8 -*-
"""
Rich Log Viewer Window (WindowXML)
Displays Kodi log lines in a numbered, syntax-highlighted editor style
with live error toggling, search, line inspection, and upload.
"""
import os
import re
import xbmc
import xbmcgui
import xbmcaddon

# XML Control IDs
CONTROL_LIST = 100
BTN_FILTER_ERRORS = 201
BTN_REFRESH = 202
BTN_SEARCH = 203
BTN_INSPECT = 204
BTN_UPLOAD = 205
BTN_CLOSE = 206
LABEL_TITLE = 1
LABEL_PATH = 2
LABEL_STATUS = 3


def colorize_log_line(line):
    """Apply distinct colors to timestamps, log levels, and messages."""
    if not line:
        return " "

    # Check for ERROR / EXCEPTION / CRITICAL
    if re.search(r"\b(ERROR|EXCEPTION|CRITICAL|FATAL)\b", line, re.IGNORECASE):
        return f"[COLOR FFFF5555]{line}[/COLOR]"

    # Check for WARNING
    if re.search(r"\b(WARNING|WARN)\b", line, re.IGNORECASE):
        return f"[COLOR FFFFA800]{line}[/COLOR]"

    # Check for INFO
    if re.search(r"\b(INFO)\b", line, re.IGNORECASE):
        # Colorize prefix and keep rest readable
        return f"[COLOR FF00D4FF]{line[:35]}[/COLOR][COLOR FFFFFFFF]{line[35:]}[/COLOR]" if len(line) > 35 else f"[COLOR FF00D4FF]{line}[/COLOR]"

    # Check for DEBUG
    if re.search(r"\b(DEBUG)\b", line, re.IGNORECASE):
        return f"[COLOR FF8A9BA8]{line}[/COLOR]"

    return f"[COLOR FFDCDFE4]{line}[/COLOR]"


class LogViewerWindow(xbmcgui.WindowXML):
    def __init__(self, *args, **kwargs):
        self.log_path = kwargs.pop("log_path", "")
        self.filter_errors = kwargs.pop("filter_errors", False)
        self.search_query = None
        self.raw_lines = []
        self.displayed_lines = []
        super(LogViewerWindow, self).__init__(*args, **kwargs)

    def onInit(self):
        self.load_log_file()
        self.apply_filter_and_populate()
        self.setFocusId(CONTROL_LIST)

    def load_log_file(self):
        if not self.log_path or not os.path.exists(self.log_path):
            self.raw_lines = ["No log file found at path: " + str(self.log_path)]
            return

        try:
            with open(self.log_path, "r", encoding="utf-8", errors="replace") as f:
                self.raw_lines = [l.rstrip("\r\n") for l in f.readlines()]
            # Keep up to latest 3000 lines for high performance in Kodi GUI
            self.raw_lines = self.raw_lines[-3000:]
        except Exception as e:
            self.raw_lines = [f"Failed to read log file: {e}"]

    def apply_filter_and_populate(self, select_idx=None):
        filtered = []
        for line in self.raw_lines:
            if self.filter_errors:
                if not re.search(r"\b(ERROR|WARNING|EXCEPTION|CRITICAL|FATAL)\b", line, re.IGNORECASE):
                    continue
            if self.search_query:
                if self.search_query.lower() not in line.lower():
                    continue
            filtered.append(line)

        self.displayed_lines = filtered
        list_ctrl = self.getControl(CONTROL_LIST)
        list_ctrl.reset()

        for i, line in enumerate(self.displayed_lines):
            line_no = f"{i + 1:04d}"
            colored = colorize_log_line(line)
            item = xbmcgui.ListItem(label=line_no, label2=colored)
            list_ctrl.addItem(item)

        self.update_header()

        if select_idx is not None and 0 <= select_idx < len(self.displayed_lines):
            list_ctrl.selectItem(select_idx)
        elif self.displayed_lines:
            # Focus on bottom (most recent log entry)
            list_ctrl.selectItem(len(self.displayed_lines) - 1)

    def update_header(self):
        addon = xbmcaddon.Addon()
        filter_status = "[COLOR FFFF5555]ERRORS ONLY[/COLOR]" if self.filter_errors else "[COLOR FF55FF55]ALL LOGS[/COLOR]"
        search_status = f"   |   Search: '[COLOR FFFFA800]{self.search_query}[/COLOR]'" if self.search_query else ""
        self.getControl(LABEL_PATH).setLabel(
            f"Log: [COLOR FFFFFFFF]{os.path.basename(self.log_path)}[/COLOR]   |   Mode: {filter_status}{search_status}   |   Total: {len(self.displayed_lines)} lines"
        )
        self.getControl(LABEL_STATUS).setLabel(
            f"Path: {self.log_path}   |   Navigate with D-Pad/Arrows, Enter to inspect line"
        )

    def onClick(self, controlId):
        if controlId == CONTROL_LIST:
            self.inspect_selected_line()
        elif controlId == BTN_FILTER_ERRORS:
            self.filter_errors = not self.filter_errors
            self.apply_filter_and_populate()
        elif controlId == BTN_REFRESH:
            self.load_log_file()
            self.apply_filter_and_populate()
        elif controlId == BTN_SEARCH:
            self.prompt_search()
        elif controlId == BTN_INSPECT:
            self.inspect_selected_line()
        elif controlId == BTN_UPLOAD:
            self.close()
            from ..log_tools import upload_kodi_log
            upload_kodi_log()
        elif controlId == BTN_CLOSE:
            self.close()

    def onAction(self, action):
        action_id = action.getId()
        if action_id in (9, 10, 92):  # BACK / ESC
            self.close()

    def get_selected_index(self):
        list_ctrl = self.getControl(CONTROL_LIST)
        pos = list_ctrl.getSelectedPosition()
        if pos < 0 or pos >= len(self.displayed_lines):
            return -1
        return pos

    def inspect_selected_line(self):
        idx = self.get_selected_index()
        if idx >= 0 and idx < len(self.displayed_lines):
            line = self.displayed_lines[idx]
            xbmcgui.Dialog().textviewer(f"Log Line #{idx + 1}", line)

    def prompt_search(self):
        dialog = xbmcgui.Dialog()
        query = dialog.input("Search / Filter in Log:", defaultt=self.search_query or "", type=xbmcgui.INPUT_ALPHANUM)
        self.search_query = query.strip() if query else None
        self.apply_filter_and_populate()
