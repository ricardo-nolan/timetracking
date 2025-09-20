"""
Pytest configuration and fixtures
"""
import pytest
import tempfile
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import TimeTrackerDB
from pdf_export import PDFExporter
from email_export import EmailExporter


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    
    db = TimeTrackerDB(temp_file.name)
    db.init_database()
    
    yield db
    
    # Cleanup
    if os.path.exists(temp_file.name):
        os.unlink(temp_file.name)


@pytest.fixture
def sample_projects():
    """Create sample projects for testing"""
    return [
        (1, "Project A", "Description A", "projecta@example.com"),
        (2, "Project B", "Description B", "projectb@example.com"),
    ]


@pytest.fixture
def sample_time_entries():
    """Create sample time entries for testing"""
    base_time = datetime.now()
    return [
        (1, 1, "Task 1", base_time.isoformat(), (base_time + timedelta(hours=1)).isoformat(), 60),
        (2, 1, "Task 2", (base_time + timedelta(hours=2)).isoformat(), (base_time + timedelta(hours=3)).isoformat(), 60),
        (3, 2, "Task 3", (base_time + timedelta(hours=4)).isoformat(), (base_time + timedelta(hours=5)).isoformat(), 60),
    ]


@pytest.fixture
def pdf_exporter():
    """Create PDF exporter for testing"""
    return PDFExporter()


@pytest.fixture
def email_exporter():
    """Create email exporter for testing"""
    return EmailExporter()


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    temp_file.close()
    
    yield temp_file.name
    
    # Cleanup
    if os.path.exists(temp_file.name):
        os.unlink(temp_file.name)
