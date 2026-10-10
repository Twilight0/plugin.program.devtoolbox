# -*- coding: utf-8 -*-
"""
Dev Toolbox - Log Viewer and Uploader with QR Code display
"""
import json
import os
import sys
import urllib.request
import urllib.parse
import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs


def get_log_file_path():
    """Locate current kodi.log or kodi.old.log."""
    log_candidates = [
        xbmcvfs.translatePath("special://logpath/kodi.log"),
        xbmcvfs.translatePath("special://temp/kodi.log"),
        xbmcvfs.translatePath("special://home/kodi.log"),
    ]
    for path in log_candidates:
        if os.path.exists(path):
            return path
    return None


def view_kodi_log(filter_errors=False):
    """View log lines with optional ERROR/WARNING filtering in a scrollable dialog."""
    log_path = get_log_file_path()
    if not log_path or not os.path.exists(log_path):
        xbmcgui.Dialog().ok("Dev Toolbox", "Could not locate kodi.log on this system.")
        return

    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception as e:
        xbmcgui.Dialog().ok("Dev Toolbox", f"Failed to read log file: {e}")
        return

    lines = lines[-1500:]
    if filter_errors:
        lines = [line for line in lines if "ERROR" in line or "WARNING" in line or "EXCEPTION" in line]

    if not lines:
        xbmcgui.Dialog().ok("Dev Toolbox", "No matching log entries found.")
        return

    content = "".join(lines)
    title = "Kodi Log [ERRORS ONLY]" if filter_errors else "Kodi Log Viewer (Latest)"
    xbmcgui.Dialog().textviewer(title, content)


def upload_text_to_paste(text):
    """Upload text to paste service (paste.kodi.tv or pastebin fallback) and return URL."""
    url = "https://paste.kodi.tv/documents"
    try:
        req = urllib.request.Request(
            url,
            data=text.encode("utf-8"),
            headers={"User-Agent": "Kodi-Dev-Toolbox/0.0.1"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            key = data.get("key")
            if key:
                return f"https://paste.kodi.tv/{key}"
    except Exception as e:
        xbmc.log(f"[DevToolbox] paste.kodi.tv upload failed: {e}", xbmc.LOGWARNING)

    # Fallback to clbin
    try:
        req = urllib.request.Request(
            "https://clbin.com",
            data=urllib.parse.urlencode({"clbin": text}).encode("utf-8"),
            headers={"User-Agent": "Kodi-Dev-Toolbox/0.0.1"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode("utf-8").strip()
    except Exception as e2:
        xbmc.log(f"[DevToolbox] fallback upload failed: {e2}", xbmc.LOGERROR)

    return None


def ensure_qrcode_imported():
    """Ensure qrcode module is accessible from python sys.path."""
    try:
        import qrcode
        return qrcode
    except ImportError:
        pass

    qrcode_dir = xbmcvfs.translatePath("special://home/addons/script.module.qrcode/lib")
    if os.path.exists(qrcode_dir) and qrcode_dir not in sys.path:
        sys.path.insert(0, qrcode_dir)
        try:
            import qrcode
            return qrcode
        except ImportError:
            pass
    return None


def show_qr_dialog(url):
    """Generate QR code and display in custom WindowXML."""
    temp_dir = xbmcvfs.translatePath("special://temp/")
    qr_img_path = os.path.join(temp_dir, "devtoolbox_qr.png")

    generated = False
    qrcode_mod = ensure_qrcode_imported()
    if qrcode_mod:
        try:
            qr = qrcode_mod.QRCode(box_size=8, border=2)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(qr_img_path)
            generated = True
        except Exception as e:
            xbmc.log(f"[DevToolbox] qrcode creation error: {e}", xbmc.LOGERROR)

    if not generated:
        try:
            api_qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(url)}"
            urllib.request.urlretrieve(api_qr_url, qr_img_path)
            generated = True
        except Exception as e2:
            xbmc.log(f"[DevToolbox] QR fallback download error: {e2}", xbmc.LOGERROR)

    if generated and os.path.exists(qr_img_path):
        from .windows.qr import QRWindow
        addon_path = xbmcaddon.Addon().getAddonInfo("path")
        win = QRWindow(
            "script-devtoolbox-qr.xml",
            addon_path,
            "Default",
            "720p",
            image_path=qr_img_path,
            url=url
        )
        win.doModal()
        del win
    else:
        xbmcgui.Dialog().ok("Log Uploaded", f"URL:\n{url}")


def upload_kodi_log():
    log_path = get_log_file_path()
    if not log_path or not os.path.exists(log_path):
        xbmcgui.Dialog().ok("Dev Toolbox", "Could not locate kodi.log")
        return

    dialog = xbmcgui.Dialog()
    if not dialog.yesno("Upload Kodi Log", "Upload current kodi.log to secure paste service?"):
        return

    p_dialog = xbmcgui.DialogProgress()
    p_dialog.create("Dev Toolbox", "Reading and preparing log file...")
    p_dialog.update(30)

    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        content = "".join(lines[-2500:])

        p_dialog.update(60, "Uploading log to paste.kodi.tv...")
        url = upload_text_to_paste(content)
        p_dialog.update(100)
        p_dialog.close()

        if url:
            show_qr_dialog(url)
        else:
            dialog.ok("Upload Failed", "Unable to upload log. Check network connection.")
    except Exception as e:
        p_dialog.close()
        dialog.ok("Upload Error", str(e))
