"""
Comprehensive email export tests to improve coverage
"""
import unittest
import tempfile
import os
import sys
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from timetracking.email_export import EmailExporter


class TestEmailExportComprehensive(unittest.TestCase):
    """Comprehensive test cases for email export functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_config.close()
        
        # Create sample time entries with rate and currency
        self.sample_entries = [
            (1, 1, "Project A", "Task 1", "2024-01-01T09:00:00", "2024-01-01T10:30:00", 90, 25.0, "EUR"),
            (2, 1, "Project A", "Task 2", "2024-01-01T11:00:00", "2024-01-01T12:00:00", 60, 25.0, "EUR"),
        ]
        
    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.temp_config.name):
            os.unlink(self.temp_config.name)
    
    def test_email_body_creation_with_rates(self):
        """Test email body creation with rate calculations"""
        exporter = EmailExporter()
        
        # Test with entries that have rates
        body = exporter._create_email_body(
            self.sample_entries,
            "Project A",
            "2024-01-01",
            "2024-01-01"
        )
        
        self.assertIn("Project A", body)
        self.assertIn("Task 1", body)
        self.assertIn("Task 2", body)
        self.assertIn("€25.00/h", body)  # Rate display
        self.assertIn("€37.50", body)  # Amount for 1.5 hours
        self.assertIn("€25.00", body)  # Amount for 1 hour
    
    def test_email_body_creation_without_rates(self):
        """Test email body creation without rates"""
        exporter = EmailExporter()
        
        # Create entries without rates
        entries_no_rates = [
            (1, 1, "Project A", "Task 1", "2024-01-01T09:00:00", "2024-01-01T10:30:00", 90, None, "EUR"),
            (2, 1, "Project A", "Task 2", "2024-01-01T11:00:00", "2024-01-01T12:00:00", 60, None, "EUR"),
        ]
        
        body = exporter._create_email_body(
            entries_no_rates,
            "Project A",
            "2024-01-01",
            "2024-01-01"
        )
        
        self.assertIn("Project A", body)
        self.assertIn("Task 1", body)
        self.assertIn("Task 2", body)
        self.assertNotIn("€", body)  # No currency symbols
        self.assertNotIn("Rate", body)  # No rate column
    
    def test_email_body_creation_mixed_rates(self):
        """Test email body creation with mixed rate entries"""
        exporter = EmailExporter()
        
        # Create entries with mixed rates
        mixed_entries = [
            (1, 1, "Project A", "Task 1", "2024-01-01T09:00:00", "2024-01-01T10:30:00", 90, 25.0, "EUR"),
            (2, 1, "Project A", "Task 2", "2024-01-01T11:00:00", "2024-01-01T12:00:00", 60, None, "EUR"),
        ]
        
        body = exporter._create_email_body(
            mixed_entries,
            "Project A",
            "2024-01-01",
            "2024-01-01"
        )
        
        self.assertIn("Project A", body)
        self.assertIn("Task 1", body)
        self.assertIn("Task 2", body)
        self.assertIn("€25.00/h", body)  # Rate for first task
        self.assertIn("N/A", body)  # No rate for second task
    
    def test_email_body_creation_usd_currency(self):
        """Test email body creation with USD currency"""
        exporter = EmailExporter()
        
        # Create entries with USD currency
        usd_entries = [
            (1, 1, "Project A", "Task 1", "2024-01-01T09:00:00", "2024-01-01T10:30:00", 90, 30.0, "USD"),
        ]
        
        body = exporter._create_email_body(
            usd_entries,
            "Project A",
            "2024-01-01",
            "2024-01-01"
        )
        
        self.assertIn("$30.00/h", body)  # USD rate
        self.assertIn("$45.00", body)  # USD amount
    
    def test_email_body_creation_running_entries(self):
        """Test email body creation with running entries"""
        exporter = EmailExporter()
        
        # Create entries with running (incomplete) entries
        running_entries = [
            (1, 1, "Project A", "Running Task", "2024-01-01T09:00:00", None, None, 25.0, "EUR"),
            (2, 1, "Project A", "Completed Task", "2024-01-01T11:00:00", "2024-01-01T12:00:00", 60, 25.0, "EUR"),
        ]
        
        body = exporter._create_email_body(
            running_entries,
            "Project A",
            "2024-01-01",
            "2024-01-01"
        )
        
        self.assertIn("Running", body)  # Running task
        self.assertIn("Completed Task", body)  # Completed task
        self.assertIn("€25.00/h", body)  # Rate display
    
    def test_email_body_creation_zero_duration(self):
        """Test email body creation with zero duration entries"""
        exporter = EmailExporter()
        
        # Create entries with zero duration
        zero_duration_entries = [
            (1, 1, "Project A", "Zero Duration Task", "2024-01-01T09:00:00", "2024-01-01T09:00:00", 0, 25.0, "EUR"),
        ]
        
        body = exporter._create_email_body(
            zero_duration_entries,
            "Project A",
            "2024-01-01",
            "2024-01-01"
        )
        
        self.assertIn("Zero Duration Task", body)
        self.assertIn("0s", body)  # Zero duration display
        self.assertIn("€0.00", body)  # Zero amount
    
    def test_email_body_creation_very_short_duration(self):
        """Test email body creation with very short duration entries"""
        exporter = EmailExporter()
        
        # Create entries with very short duration
        short_duration_entries = [
            (1, 1, "Project A", "Short Task", "2024-01-01T09:00:00", "2024-01-01T09:00:30", 0, 25.0, "EUR"),
        ]
        
        body = exporter._create_email_body(
            short_duration_entries,
            "Project A",
            "2024-01-01",
            "2024-01-01"
        )
        
        self.assertIn("Short Task", body)
        self.assertIn("30s", body)  # 30 seconds display
        self.assertIn("€0.21", body)  # Small amount (30 seconds * 25/3600)
    
    def test_email_body_creation_very_long_duration(self):
        """Test email body creation with very long duration entries"""
        exporter = EmailExporter()
        
        # Create entries with very long duration
        long_duration_entries = [
            (1, 1, "Project A", "Long Task", "2024-01-01T09:00:00", "2024-01-01T18:30:00", 570, 25.0, "EUR"),
        ]
        
        body = exporter._create_email_body(
            long_duration_entries,
            "Project A",
            "2024-01-01",
            "2024-01-01"
        )
        
        self.assertIn("Long Task", body)
        self.assertIn("9h 30m 0s", body)  # Long duration display
        self.assertIn("€237.50", body)  # Large amount (9.5 hours * 25)
    
    def test_email_body_creation_empty_entries(self):
        """Test email body creation with empty entries"""
        exporter = EmailExporter()
        
        body = exporter._create_email_body(
            [],
            "Project A",
            "2024-01-01",
            "2024-01-01"
        )
        
        self.assertIn("Project A", body)
        self.assertIn("No time entries found", body)
    
    def test_email_body_creation_single_entry(self):
        """Test email body creation with single entry"""
        exporter = EmailExporter()
        
        single_entry = [
            (1, 1, "Project A", "Single Task", "2024-01-01T09:00:00", "2024-01-01T10:00:00", 60, 25.0, "EUR"),
        ]
        
        body = exporter._create_email_body(
            single_entry,
            "Project A",
            "2024-01-01",
            "2024-01-01"
        )
        
        self.assertIn("Project A", body)
        self.assertIn("Single Task", body)
        self.assertIn("€25.00/h", body)
        self.assertIn("€25.00", body)
    
    def test_email_body_creation_multiple_projects(self):
        """Test email body creation with multiple projects"""
        exporter = EmailExporter()
        
        # Create entries from multiple projects
        multi_project_entries = [
            (1, 1, "Project A", "Task A1", "2024-01-01T09:00:00", "2024-01-01T10:00:00", 60, 25.0, "EUR"),
            (2, 2, "Project B", "Task B1", "2024-01-01T11:00:00", "2024-01-01T12:00:00", 60, 30.0, "USD"),
        ]
        
        body = exporter._create_email_body(
            multi_project_entries,
            "Multiple Projects",
            "2024-01-01",
            "2024-01-01"
        )
        
        self.assertIn("Multiple Projects", body)
        self.assertIn("Task A1", body)
        self.assertIn("Task B1", body)
        self.assertIn("€25.00/h", body)  # EUR rate
        self.assertIn("$30.00/h", body)  # USD rate
    
    def test_email_body_creation_different_currencies(self):
        """Test email body creation with different currencies"""
        exporter = EmailExporter()
        
        # Create entries with different currencies
        multi_currency_entries = [
            (1, 1, "Project A", "EUR Task", "2024-01-01T09:00:00", "2024-01-01T10:00:00", 60, 25.0, "EUR"),
            (2, 2, "Project B", "USD Task", "2024-01-01T11:00:00", "2024-01-01T12:00:00", 60, 30.0, "USD"),
        ]
        
        body = exporter._create_email_body(
            multi_currency_entries,
            "Multi-Currency",
            "2024-01-01",
            "2024-01-01"
        )
        
        self.assertIn("Multi-Currency", body)
        self.assertIn("€25.00/h", body)  # EUR rate
        self.assertIn("$30.00/h", body)  # USD rate
        self.assertIn("€25.00", body)  # EUR amount
        self.assertIn("$30.00", body)  # USD amount


if __name__ == '__main__':
    unittest.main()
