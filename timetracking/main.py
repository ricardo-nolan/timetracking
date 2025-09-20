#!/usr/bin/env python3
"""
Time Tracker Application
A Python-based time tracking application with GUI, SQLite database, and PDF/Email export functionality.
"""

import sys
import os
from .gui import TimeTrackerGUI

def main():
    """Main entry point for the Time Tracker application"""
    try:
        app = TimeTrackerGUI()
        app.run()
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
