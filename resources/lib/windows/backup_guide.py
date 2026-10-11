# -*- coding: utf-8 -*-
"""
Backup & Restore Guide Window (WindowXML)
Displays a read-only, editor-styled user guide explaining backup/restore architecture,
sanitization rules, manifest verification, and restore strategies.
"""
import os
import re
import textwrap
import xbmc
import xbmcgui
import xbmcaddon

CONTROL_LIST = 100
BTN_CLOSE = 201
LABEL_TITLE = 1
LABEL_SUBTITLE = 2
LABEL_FOOTER = 3

# Max characters per line in 720p item layout for font12
MAX_LINE_WIDTH = 80


def colorize_guide_line(line):
    """Format markdown guide lines with Kodi color tags."""
    if not line:
        return " "

    stripped = line.strip()

    # If the line already contains Kodi formatting tags, preserve and return as-is
    if "[" in stripped and "]" in stripped and any(tag in stripped for tag in ("[B]", "[I]", "[COLOR", "[/B]", "[/I]", "[/COLOR]")):
        # If it's a separator or bullet with tags
        if stripped == "---":
            return "[COLOR FF5C6370]────────────────────────────────────────────────────────[/COLOR]"
        return stripped

    # Main titles (##)
    if stripped.startswith("## "):
        return f"[B][COLOR FF00D4FF]{stripped[3:]}[/COLOR][/B]"
    # Main header (#)
    if stripped.startswith("# "):
        return f"[B][COLOR FFFFA800]{stripped[2:]}[/COLOR][/B]"
    # Sub-headers (###)
    if stripped.startswith("### "):
        return f"[B][COLOR FF98C379]{stripped[4:]}[/COLOR][/B]"
    # Separators
    if stripped == "---":
        return "[COLOR FF5C6370]────────────────────────────────────────────────────────[/COLOR]"
    # Bullet points
    if stripped.startswith("- ") or stripped.startswith("• "):
        bullet_text = stripped[2:]
        bullet_text = re.sub(r"\*\*(.*?)\*\*", r"[B][COLOR FFFFFFFF]\1[/COLOR][/B]", bullet_text)
        bullet_text = re.sub(r"`(.*?)`", r"[COLOR FFE5C07B]\1[/COLOR]", bullet_text)
        return f"[COLOR FF00D4FF]• [/COLOR][COLOR FFDCDFE4]{bullet_text}[/COLOR]"
    # Continuation indent for wrapped bullets
    if stripped.startswith("  "):
        cont_text = stripped[2:]
        cont_text = re.sub(r"\*\*(.*?)\*\*", r"[B][COLOR FFFFFFFF]\1[/COLOR][/B]", cont_text)
        cont_text = re.sub(r"`(.*?)`", r"[COLOR FFE5C07B]\1[/COLOR]", cont_text)
        return f"    [COLOR FFDCDFE4]{cont_text}[/COLOR]"
    # Numbered items (1. 2.)
    m_num = re.match(r"^(\d+\.)\s+(.*)", stripped)
    if m_num:
        num_prefix = m_num.group(1)
        rest = m_num.group(2)
        rest = re.sub(r"\*\*(.*?)\*\*", r"[B][COLOR FFFFFFFF]\1[/COLOR][/B]", rest)
        rest = re.sub(r"`(.*?)`", r"[COLOR FFE5C07B]\1[/COLOR]", rest)
        return f"[COLOR FFFFA800]{num_prefix} [/COLOR][COLOR FFDCDFE4]{rest}[/COLOR]"

    # General text with backticks or bold
    formatted = re.sub(r"\*\*(.*?)\*\*", r"[B][COLOR FFFFFFFF]\1[/COLOR][/B]", stripped)
    formatted = re.sub(r"`(.*?)`", r"[COLOR FFE5C07B]\1[/COLOR]", formatted)
    return f"[COLOR FFDCDFE4]{formatted}[/COLOR]"


def wrap_guide_lines(raw_lines, width=MAX_LINE_WIDTH):
    """Split long lines at word boundaries while preserving indent and markdown markers."""
    wrapped_lines = []
    for raw in raw_lines:
        line = raw.rstrip("\r\n")
        if not line:
            wrapped_lines.append("")
            continue

        stripped = line.strip()

        # Keep headers, titles, and horizontal rules untouched
        if stripped.startswith("#") or stripped == "---":
            wrapped_lines.append(line)
            continue

        # Bullet point handling
        if stripped.startswith("- "):
            bullet_body = stripped[2:]
            parts = textwrap.wrap(bullet_body, width=width - 4, break_long_words=False)
            if parts:
                wrapped_lines.append("- " + parts[0])
                for cont in parts[1:]:
                    wrapped_lines.append("  " + cont)
            else:
                wrapped_lines.append("- ")
            continue

        # Numbered item handling
        m_num = re.match(r"^(\d+\.)\s+(.*)", stripped)
        if m_num:
            prefix = m_num.group(1) + " "
            body = m_num.group(2)
            parts = textwrap.wrap(body, width=width - len(prefix), break_long_words=False)
            if parts:
                wrapped_lines.append(prefix + parts[0])
                indent_spaces = " " * len(prefix)
                for cont in parts[1:]:
                    wrapped_lines.append(indent_spaces + cont)
            else:
                wrapped_lines.append(prefix)
            continue

        # Standard paragraph wrapping
        parts = textwrap.wrap(line, width=width, break_long_words=False)
        if parts:
            wrapped_lines.extend(parts)
        else:
            wrapped_lines.append("")

    return wrapped_lines


class BackupGuideWindow(xbmcgui.WindowXML):
    def __init__(self, *args, **kwargs):
        self.guide_file_path = kwargs.pop("guide_file_path", "")
        self.lines = []
        super(BackupGuideWindow, self).__init__(*args, **kwargs)

    def onInit(self):
        self.load_guide_file()
        self.populate_list()
        try:
            self.setFocusId(CONTROL_LIST)
        except Exception:
            pass

    def load_guide_file(self):
        if not self.guide_file_path or not os.path.isfile(self.guide_file_path):
            self.lines = ["Backup guide file not found."]
            return

        try:
            with open(self.guide_file_path, "r", encoding="utf-8", errors="replace") as f:
                raw_lines = f.readlines()
            self.lines = wrap_guide_lines(raw_lines, width=MAX_LINE_WIDTH)
        except Exception as e:
            xbmc.log(f"[DevToolbox] Error reading guide file: {e}", xbmc.LOGERROR)
            self.lines = [f"Error reading guide file: {e}"]

    def populate_list(self):
        try:
            list_ctrl = self.getControl(CONTROL_LIST)
        except Exception:
            return

        list_ctrl.reset()
        items = []

        for idx, line in enumerate(self.lines):
            line_no_str = f"{idx + 1:03d}"
            formatted_text = colorize_guide_line(line)
            item = xbmcgui.ListItem(label=line_no_str, label2=formatted_text)
            items.append(item)

        list_ctrl.addItems(items)
        if items:
            list_ctrl.selectItem(0)

    def onClick(self, controlId):
        if controlId == BTN_CLOSE:
            self.close()

    def onAction(self, action):
        action_id = action.getId()
        if action_id in (9, 10, 92):  # BACK / ESC
            self.close()


def show_backup_guide():
    """Launch the WindowXML Backup Guide dialog."""
    addon = xbmcaddon.Addon("plugin.program.devtoolbox")
    addon_path = addon.getAddonInfo("path")
    guide_path = os.path.join(addon_path, "resources", "docs", "backup_guide.txt")

    win = BackupGuideWindow(
        "script-devtoolbox-guide.xml",
        addon_path,
        "Default",
        "720p",
        guide_file_path=guide_path
    )
    win.doModal()
    del win
