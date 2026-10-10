# -*- coding: utf-8 -*-
"""
Dev Toolbox - Global Context Menu Item
Launches the Dev Toolbox plugin immediately from any context menu.
"""
import xbmc

xbmc.executebuiltin("ActivateWindow(programs,plugin://plugin.program.devtoolbox/,return)")
