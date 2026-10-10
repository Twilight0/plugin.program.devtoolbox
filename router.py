# -*- coding: utf-8 -*-
"""
Dev Toolbox - Entry Router & Plugin Dispatcher
Author: Twilight0
"""
import sys
import urllib.parse
from urldispatcher import urldispatcher

from resources.lib import navigator  # noqa: F401
from resources.lib.theme_manager import sync_theme_if_needed


def run(argv=None):
    args = argv or sys.argv
    params_str = args[2][1:] if len(args) > 2 and args[2] else ""
    params = dict(urllib.parse.parse_qsl(params_str))

    # Synchronize addon.xml assets with current theme setting if changed externally
    try:
        sync_theme_if_needed()
    except Exception:
        pass

    action = params.get("action") or "root"
    urldispatcher.dispatch(action, params)


if __name__ == "__main__":
    run()
