# -*- coding: utf-8 -*-
"""
QR Code Display Window using WindowXML
"""
import xbmcgui


class QRWindow(xbmcgui.WindowXML):
    def __init__(self, *args, **kwargs):
        self.image_path = kwargs.pop("image_path", "")
        self.url = kwargs.pop("url", "")
        super(QRWindow, self).__init__(*args, **kwargs)

    def onInit(self):
        try:
            if self.image_path:
                self.getControl(10).setImage(self.image_path)
            if self.url:
                self.getControl(11).setLabel(self.url)
            self.setFocusId(100)
        except Exception:
            pass

    def onClick(self, controlId):
        if controlId == 100:
            self.close()

    def onAction(self, action):
        action_id = action.getId()
        if action_id in (9, 10, 92):
            self.close()
