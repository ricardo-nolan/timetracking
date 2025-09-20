# Time Tracker

A Python-based time tracking application with a graphical user interface, SQLite database, and PDF/Email export functionality.

## Features

- **Project Management**: Create and manage multiple projects
- **Time Tracking**: Start/stop timers for different projects
- **Real-time Display**: Live timer display showing elapsed time
- **Data Storage**: SQLite database for persistent storage
- **Filtering**: Filter time entries by project and date range
- **Export Options**:
  - PDF reports with formatted tables
  - Email reports (HTML format with optional PDF attachment)
- **Modern GUI**: Clean, intuitive interface built with tkinter

## Installation

1. Install Python 3.7 or higher
2. Install tkinter support (macOS with Homebrew):
   ```bash
   brew install python-tk
   ```
3. Create and activate virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
4. Install required dependencies:
   ```bash
   pip install reportlab
   ```

## Usage

1. Run the application:
   ```bash
   # Option 1: Using the startup script
   ./run.sh
   
   # Option 2: Manual activation
   source venv/bin/activate
   python main.py
   ```

2. **Adding Projects**:
   - Enter project name and description
   - Click "Add Project"

3. **Time Tracking**:
   - Select a project from the dropdown
   - Add an optional description
   - Click "Start Timer" to begin tracking
   - Click "Stop Timer" to stop and save the entry

4. **Viewing Entries**:
   - Use the filter dropdown to view entries by project
   - Use date range filters (Today, This Week, This Month, etc.)
   - Click "Refresh" to update the display

5. **Exporting**:
   - **PDF Export**: Click "Export to PDF" to save a formatted report
   - **Email Export**: Click "Send Email" to send reports via email

## Email Configuration

For email functionality, you'll need to configure your email settings:

- **Gmail**: Use your Gmail address and app password
- **Other providers**: Update SMTP settings in `email_export.py`

## Database

The application uses SQLite for data storage. The database file (`time_tracker.db`) will be created automatically in the application directory.

## File Structure

```
timer/
├── main.py              # Application entry point
├── gui.py               # GUI interface
├── database.py          # Database operations
├── pdf_export.py        # PDF export functionality
├── email_export.py      # Email export functionality
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Requirements

- Python 3.7+
- reportlab (for PDF generation)
- tkinter (included with Python)
- sqlite3 (included with Python)

## Troubleshooting

- **Timer not starting**: Make sure no other timer is running for the selected project
- **Email not sending**: Check your email credentials and SMTP settings
- **PDF export failing**: Ensure you have write permissions in the selected directory

## License

This project is open source and available under the MIT License.
