"""
Unit tests for PDF export functionality
"""
import unittest
import tempfile
import os
import sys
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from timetracking.pdf_export import PDFExporter


class TestPDFExporter(unittest.TestCase):
    """Test cases for PDFExporter class"""
    
    def setUp(self):
        """Set up test data"""
        self.pdf_exporter = PDFExporter()
        
        # Create sample time entries (id, project_id, project_name, description, start_time, end_time, duration, rate, currency)
        self.sample_entries = [
            (1, 1, "Project A", "Test Task 1", "2024-01-01T09:00:00", "2024-01-01T10:30:00", 90, 25.0, "EUR"),
            (2, 1, "Project A", "Test Task 2", "2024-01-01T11:00:00", "2024-01-01T12:00:00", 60, 25.0, "EUR"),
            (3, 2, "Project B", "Another Task", "2024-01-02T09:00:00", "2024-01-02T10:00:00", 60, 30.0, "USD"),
        ]
        
        # Create sample projects
        self.sample_projects = [
            (1, "Project A", "Description A", "projecta@example.com"),
            (2, "Project B", "Description B", "projectb@example.com"),
        ]
    
    def test_export_time_report(self):
        """Test PDF export functionality"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            # Test export
            success = self.pdf_exporter.export_time_report(
                self.sample_entries, 
                output_path
            )
            
            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_path))
            self.assertGreater(os.path.getsize(output_path), 0)
            
        finally:
            # Clean up
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_export_empty_entries(self):
        """Test PDF export with empty entries"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            # Test export with empty data
            success = self.pdf_exporter.export_time_report(
                [], 
                output_path
            )
            
            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_path))
            
        finally:
            # Clean up
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_export_with_running_entry(self):
        """Test PDF export with running (incomplete) entry"""
        # Create entry with no end time
        running_entries = [
            (1, 1, "Project A", "Running Task", "2024-01-01T09:00:00", None, None, 25.0, "EUR"),
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            # Test export
            success = self.pdf_exporter.export_time_report(
                running_entries, 
                output_path
            )
            
            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_path))
            
        finally:
            # Clean up
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_duration_formatting(self):
        """Test duration formatting with seconds"""
        # Test various duration scenarios
        test_cases = [
            (3600, "1h 0m 0s"),  # 1 hour
            (3661, "1h 1m 1s"),  # 1 hour 1 minute 1 second
            (61, "1m 1s"),        # 1 minute 1 second
            (1, "1s"),            # 1 second
            (0, "0s"),            # 0 seconds
        ]
        
        for total_seconds, expected in test_cases:
            # Create test entry
            start_time = datetime.now()
            end_time = start_time + timedelta(seconds=total_seconds)
            
            test_entries = [
                (1, 1, "Project A", "Test Task", start_time.isoformat(), end_time.isoformat(), total_seconds // 60, 25.0, "EUR")
            ]
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                output_path = tmp_file.name
            
            try:
                success = self.pdf_exporter.export_time_report(
                    test_entries, 
                    output_path
                )
                
                self.assertTrue(success)
                
            finally:
                # Clean up
                if os.path.exists(output_path):
                    os.unlink(output_path)


if __name__ == '__main__':
    unittest.main()
