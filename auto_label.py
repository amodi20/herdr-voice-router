#!/usr/bin/env python3
"""Claude Code SessionStart hook: name an unnamed Herdr pane after its folder.

~/code/billing-api -> "billing api". Panes that already have
a name are left alone, so names you pick yourself always win.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pane_router import herdr  # noqa: E402


def main():
    pane_id = os.environ.get("HERDR_PANE_ID")
    if os.environ.get("HERDR_ENV") != "1" or not pane_id:
        return
    pane = herdr("pane", "get", pane_id)["pane"]
    if pane.get("label"):
        return
    folder = os.path.basename(pane.get("cwd") or os.getcwd())
    name = re.sub(r"[-_.]+", " ", folder).strip().lower()
    if name:
        herdr("pane", "rename", pane_id, *name.split())


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # never get in the way of Claude starting
