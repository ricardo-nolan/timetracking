#!/usr/bin/env python3
"""
Time Tracker Application
A Python-based time tracking application with GUI, SQLite database, and PDF/Email export functionality.
"""

import sys
import os
from . import gui as gui_module
import tkinter as tk

def main():
    """Main entry point for the Time Tracker application"""
    try:
        # Ensure a Tk root exists before GUI constructs StringVars in tests
        try:
            if tk._default_root is None:
                tk.Tk().withdraw()
        except Exception:
            pass
        app = gui_module.TimeTrackerGUI()
        app.run()
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
