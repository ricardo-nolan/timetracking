# Time Tracker

A comprehensive Python-based time tracking application with a modern graphical user interface, SQLite database, and advanced PDF/Email export functionality.

## Features

- **Project Management**: Create, edit, and manage multiple projects with multiple email addresses
- **Time Tracking**: Start/stop timers for different projects with real-time display
- **Time Entry Editing**: Edit existing time entries with real-time duration calculation
- **Data Storage**: SQLite database for persistent storage with automatic migrations
- **Filtering**: Filter time entries by project and date range
- **Export Options**:
  - PDF reports with formatted tables and seconds precision
  - Email reports with multiple recipient selection and PDF attachments
- **Email Management**: 
  - Multiple email addresses per project
  - Primary email designation
  - Persistent email settings
  - Support for Gmail, Outlook, Yahoo, iCloud, and custom SMTP
- **Modern GUI**: Clean, intuitive interface with improved dialogs and better UX

## Installation

### Option 1: Install from PyPI (Recommended)
```bash
pip install timetracking
```

### Option 2: Install from Source
```bash
git clone https://github.com/ricardo-nolan/timetracking.git
cd timetracking
pip install -e .
```

### Option 3: Development Setup
```bash
git clone https://github.com/ricardo-nolan/timetracking.git
cd timetracking
./install.sh
```

### Prerequisites
- Python 3.7 or higher
- tkinter support (macOS with Homebrew):
   ```bash
   brew install python-tk
   ```

## Usage

### Quick Start
```bash
timetracking
```

### Development Mode
```bash
# Option 1: Using the startup script
./run.sh

# Option 2: Manual activation
source venv/bin/activate
python main.py
```

2. **Project Management**:
   - **Adding Projects**: Enter project name, description, and default email
   - **Editing Projects**: Click "Edit Project" to modify project details and manage email addresses
   - **Multiple Emails**: Add multiple email addresses per project and set one as primary
   - **Email Management**: Add, remove, and set primary emails for each project

3. **Time Tracking**:
   - Select a project from the dropdown
   - Add an optional description
   - Click "Start Timer" to begin tracking
   - Click "Stop Timer" to stop and save the entry
   - Real-time display shows elapsed time with seconds precision

4. **Time Entry Management**:
   - **Viewing Entries**: Use the filter dropdown to view entries by project
   - **Date Filters**: Use date range filters (Today, This Week, This Month, etc.)
   - **Editing Entries**: Click "Edit Entry" to modify existing time entries
   - **Real-time Updates**: Duration updates automatically when editing times

5. **Exporting**:
   - **PDF Export**: Click "Export to PDF" with predefined filename format
   - **Email Export**: Click "Send Email" with multiple recipient selection
   - **Email Settings**: Configure SMTP settings for your email provider

## Testing

The application includes a comprehensive test suite with 42 tests covering:

- **Database Operations**: Unit tests for all database methods
- **PDF Export**: Tests for PDF generation and formatting
- **Email Export**: Tests for email sending with SMTP mocking
- **GUI Components**: Tests for GUI functionality and dialogs
- **Integration Tests**: End-to-end workflow testing

### Running Tests

```bash
# Run all tests with coverage
./run_tests.sh

# Run specific test files
python -m pytest tests/test_database.py -v

# Run tests with coverage report
python -m pytest tests/ --cov=. --cov-report=html
```

### Test Coverage

Current test coverage: **50%** overall
- Database operations: **99%** coverage
- PDF export: **98%** coverage  
- Email export: **99%** coverage
- GUI components: **99%** coverage
- Integration tests: **99%** coverage
- Main application: **81%** coverage

**All 42 tests passing (100% pass rate)**

Coverage reports are generated in `htmlcov/index.html`

## Email Configuration

The application supports multiple email providers with easy setup:

### **Supported Providers:**
- **Gmail**: Use your Gmail address and app password (recommended)
- **Outlook/Hotmail**: smtp-mail.outlook.com:587
- **Yahoo**: smtp.mail.yahoo.com:587
- **iCloud**: smtp.mail.me.com:587
- **Custom**: Enter your own SMTP server and port

### **Setup Process:**
1. Click "Email Settings" in the main application
2. Select your email provider from the dropdown
3. Enter your email address and password/app password
4. Click "Test Connection" to verify settings
5. Click "Save Settings" to store configuration

### **Gmail Setup:**
1. Enable 2-factor authentication on your Google account
2. Generate an App Password: Google Account → Security → App passwords
3. Use your Gmail address and the generated app password

## Database

The application uses SQLite for data storage with automatic schema migrations:
- **Projects**: Name, description, default email
- **Project Emails**: Multiple email addresses per project with primary designation
- **Time Entries**: Project, description, start/end times, duration
- **Automatic Migration**: Database schema updates automatically when needed

## File Structure

```
timer/
├── main.py              # Application entry point
├── gui.py               # GUI interface with all dialogs
├── database.py          # Database operations and migrations
├── pdf_export.py        # PDF export functionality
├── email_export.py      # Email export functionality
├── requirements.txt     # Python dependencies
├── run.sh              # Startup script
├── .gitignore          # Git ignore file
└── README.md           # This file
```

## Requirements

- Python 3.7+
- reportlab (for PDF generation)
- Pillow (for image handling)
- pytest (for testing)
- pytest-cov (for test coverage)
- tkinter (included with Python)
- sqlite3 (included with Python)

## Troubleshooting

- **Timer not starting**: Make sure no other timer is running for the selected project
- **Email not sending**: 
  - Check your email credentials and SMTP settings
  - For Gmail, ensure you're using an App Password, not your regular password
  - Test connection in Email Settings dialog
- **PDF export failing**: Ensure you have write permissions in the selected directory
- **Database errors**: The application automatically handles database migrations
- **GUI issues**: Ensure tkinter is properly installed (`brew install python-tk` on macOS)

## Development

### Running Tests
```bash
./run_tests.sh
```

### Test Coverage
```bash
./run_tests.sh --cov
```

### Building Distribution
```bash
# Install build tools
pip install build twine

# Build package
python -m build

# Upload to PyPI (requires PyPI account)
twine upload dist/*
```

### Package Structure
```
timetracking/
├── __init__.py
├── main.py          # Entry point
├── database.py      # SQLite operations
├── gui.py           # Tkinter interface
├── pdf_export.py    # PDF generation
├── email_export.py  # Email functionality
└── password_utils.py # Encryption utilities
```

## License

This project is open source and available under the MIT License.
