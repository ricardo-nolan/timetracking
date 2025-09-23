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
- tkinter (included with Python on most systems)

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

The application includes a comprehensive test suite with **87 tests** covering:

- **Database Operations**: Unit tests for all database methods and edge cases
- **PDF Export**: Tests for PDF generation, formatting, and rate calculations
- **Email Export**: Tests for email sending with SMTP mocking and encryption
- **GUI Components**: Comprehensive tests for GUI functionality, dialogs, and validation
- **Integration Tests**: End-to-end workflow testing and error handling
- **Password Security**: Tests for password encryption and decryption
- **Main Application**: Tests for application startup and error handling

### Running Tests

```bash
# Run all tests with coverage
./run_tests.sh

# Run specific test files
python -m pytest tests/test_database.py -v

# Run GUI tests
python -m pytest tests/test_gui_logic.py tests/test_gui_dialogs.py tests/test_gui_validation.py tests/test_gui_integration.py

# Run tests with coverage report
python -m pytest tests/ --cov=timetracking --cov-report=html
```

### Test Coverage

Current test coverage: **36%** overall
- **Database operations**: **75%** coverage (up from 73%)
- **PDF export**: **88%** coverage (maintained)
- **Email export**: **87%** coverage (up from 83%)
- **Password utilities**: **80%** coverage (maintained)
- **Main application**: **83%** coverage (maintained)
- **GUI components**: **8%** coverage (expected due to Tkinter complexity)

**78/87 tests passing (90% pass rate)**

### GUI Test Suite

The application includes **51 comprehensive GUI tests** covering:

- **GUI Logic Tests** (10 tests): Duration calculations, rate validation, currency handling
- **GUI Dialog Tests** (13 tests): Project editing, time entry editing, email settings
- **GUI Validation Tests** (13 tests): Input validation, data type validation, error handling
- **GUI Integration Tests** (15 tests): Database integration, export workflows, configuration

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
├── password_utils.py    # Password encryption utilities
├── requirements.txt     # Python dependencies
├── run.sh              # Startup script
├── run_tests.sh        # Test runner script
├── install.sh          # Installation script
├── .gitignore          # Git ignore file
├── tests/              # Comprehensive test suite
│   ├── test_database.py           # Database operation tests
│   ├── test_email_export.py       # Email export tests
│   ├── test_pdf_export.py         # PDF export tests
│   ├── test_password_utils.py     # Password encryption tests
│   ├── test_main.py               # Main application tests
│   ├── test_gui_logic.py          # GUI logic tests
│   ├── test_gui_dialogs.py        # GUI dialog tests
│   ├── test_gui_validation.py     # GUI validation tests
│   └── test_gui_integration.py    # GUI integration tests
└── README.md           # This file
```

## Requirements

- Python 3.7+
- reportlab (for PDF generation)
- Pillow (for image handling)
- pytest (for testing)
- pytest-cov (for test coverage)
- cryptography (for password encryption)
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
- **GUI issues**: 
  - **macOS with Homebrew**: `brew install python-tk` (if tkinter missing)
  - **Ubuntu/Debian**: `sudo apt-get install python3-tk`
  - **CentOS/RHEL**: `sudo yum install tkinter` or `sudo dnf install python3-tkinter`
  - **Windows**: tkinter is included with Python

## Development

### Running Tests
```bash
# Run all tests with coverage
./run_tests.sh

# Run specific test categories
python -m pytest tests/test_database.py -v
python -m pytest tests/test_gui_logic.py tests/test_gui_dialogs.py tests/test_gui_validation.py tests/test_gui_integration.py -v
```

### Test Coverage
```bash
# Generate coverage report
./run_tests.sh --cov

# Generate HTML coverage report
python -m pytest --cov=timetracking --cov-report=html --cov-report=term-missing
```

### Test Suite Overview
- **87 total tests** with **78 passing** (90% pass rate)
- **36% overall coverage** with comprehensive GUI testing
- **51 GUI-specific tests** covering logic, dialogs, validation, and integration
- **HTML coverage report** available in `htmlcov/index.html`

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
