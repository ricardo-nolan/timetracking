"""
Comprehensive PDF export tests to improve coverage
"""
import unittest
import tempfile
import os
import sys
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from timetracking.pdf_export import PDFExporter


class TestPDFExportComprehensive(unittest.TestCase):
    """Comprehensive test cases for PDF export functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.pdf_exporter = PDFExporter()
        
        # Create sample time entries with rate and currency
        self.sample_entries = [
            (1, 1, "Project A", "Task 1", "2024-01-01T09:00:00", "2024-01-01T10:30:00", 90, 25.0, "EUR"),
            (2, 1, "Project A", "Task 2", "2024-01-01T11:00:00", "2024-01-01T12:00:00", 60, 25.0, "EUR"),
        ]
        
    def tearDown(self):
        """Clean up test files"""
        pass
    
    def test_export_with_rates_and_currency(self):
        """Test PDF export with rate calculations and currency"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            success = self.pdf_exporter.export_time_report(
                self.sample_entries,
                output_path
            )
            
            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_path))
            self.assertGreater(os.path.getsize(output_path), 0)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_export_without_rates(self):
        """Test PDF export without rate calculations"""
        entries_no_rates = [
            (1, 1, "Project A", "Task 1", "2024-01-01T09:00:00", "2024-01-01T10:30:00", 90, None, "EUR"),
            (2, 1, "Project A", "Task 2", "2024-01-01T11:00:00", "2024-01-01T12:00:00", 60, None, "EUR"),
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            success = self.pdf_exporter.export_time_report(
                entries_no_rates,
                output_path
            )
            
            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_path))
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_export_with_mixed_rates(self):
        """Test PDF export with mixed rate entries"""
        mixed_entries = [
            (1, 1, "Project A", "Task 1", "2024-01-01T09:00:00", "2024-01-01T10:30:00", 90, 25.0, "EUR"),
            (2, 1, "Project A", "Task 2", "2024-01-01T11:00:00", "2024-01-01T12:00:00", 60, None, "EUR"),
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            success = self.pdf_exporter.export_time_report(
                mixed_entries,
                output_path
            )
            
            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_path))
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_export_with_usd_currency(self):
        """Test PDF export with USD currency"""
        usd_entries = [
            (1, 1, "Project A", "USD Task", "2024-01-01T09:00:00", "2024-01-01T10:00:00", 60, 30.0, "USD"),
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            success = self.pdf_exporter.export_time_report(
                usd_entries,
                output_path
            )
            
            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_path))
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_export_with_running_entries(self):
        """Test PDF export with running (incomplete) entries"""
        running_entries = [
            (1, 1, "Project A", "Running Task", "2024-01-01T09:00:00", None, None, 25.0, "EUR"),
            (2, 1, "Project A", "Completed Task", "2024-01-01T11:00:00", "2024-01-01T12:00:00", 60, 25.0, "EUR"),
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            success = self.pdf_exporter.export_time_report(
                running_entries,
                output_path
            )
            
            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_path))
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_export_with_zero_duration(self):
        """Test PDF export with zero duration entries"""
        zero_duration_entries = [
            (1, 1, "Project A", "Zero Duration Task", "2024-01-01T09:00:00", "2024-01-01T09:00:00", 0, 25.0, "EUR"),
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            success = self.pdf_exporter.export_time_report(
                zero_duration_entries,
                output_path
            )
            
            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_path))
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_export_with_very_short_duration(self):
        """Test PDF export with very short duration entries"""
        short_duration_entries = [
            (1, 1, "Project A", "Short Task", "2024-01-01T09:00:00", "2024-01-01T09:00:30", 0, 25.0, "EUR"),
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            success = self.pdf_exporter.export_time_report(
                short_duration_entries,
                output_path
            )
            
            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_path))
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_export_with_very_long_duration(self):
        """Test PDF export with very long duration entries"""
        long_duration_entries = [
            (1, 1, "Project A", "Long Task", "2024-01-01T09:00:00", "2024-01-01T18:30:00", 570, 25.0, "EUR"),
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            success = self.pdf_exporter.export_time_report(
                long_duration_entries,
                output_path
            )
            
            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_path))
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_export_with_empty_entries(self):
        """Test PDF export with empty entries"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            success = self.pdf_exporter.export_time_report(
                [],
                output_path
            )
            
            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_path))
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_export_with_single_entry(self):
        """Test PDF export with single entry"""
        single_entry = [
            (1, 1, "Project A", "Single Task", "2024-01-01T09:00:00", "2024-01-01T10:00:00", 60, 25.0, "EUR"),
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            success = self.pdf_exporter.export_time_report(
                single_entry,
                output_path
            )
            
            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_path))
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_export_with_multiple_projects(self):
        """Test PDF export with multiple projects"""
        multi_project_entries = [
            (1, 1, "Project A", "Task A1", "2024-01-01T09:00:00", "2024-01-01T10:00:00", 60, 25.0, "EUR"),
            (2, 2, "Project B", "Task B1", "2024-01-01T11:00:00", "2024-01-01T12:00:00", 60, 30.0, "USD"),
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            success = self.pdf_exporter.export_time_report(
                multi_project_entries,
                output_path
            )
            
            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_path))
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_export_with_different_currencies(self):
        """Test PDF export with different currencies"""
        multi_currency_entries = [
            (1, 1, "Project A", "EUR Task", "2024-01-01T09:00:00", "2024-01-01T10:00:00", 60, 25.0, "EUR"),
            (2, 2, "Project B", "USD Task", "2024-01-01T11:00:00", "2024-01-01T12:00:00", 60, 30.0, "USD"),
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            success = self.pdf_exporter.export_time_report(
                multi_currency_entries,
                output_path
            )
            
            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_path))
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_export_with_large_dataset(self):
        """Test PDF export with large dataset"""
        large_entries = []
        for i in range(50):  # 50 entries
            start_time = datetime(2024, 1, 1, 9, 0) + timedelta(hours=i)
            end_time = start_time + timedelta(hours=1)
            large_entries.append((
                i + 1, 1, "Project A", f"Task {i + 1}",
                start_time.isoformat(), end_time.isoformat(),
                60, 25.0, "EUR"
            ))
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            success = self.pdf_exporter.export_time_report(
                large_entries,
                output_path
            )
            
            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_path))
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_export_with_special_characters(self):
        """Test PDF export with special characters in descriptions"""
        special_char_entries = [
            (1, 1, "Project A", "Task with émojis 🚀 and spëcial chars", "2024-01-01T09:00:00", "2024-01-01T10:00:00", 60, 25.0, "EUR"),
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            success = self.pdf_exporter.export_time_report(
                special_char_entries,
                output_path
            )
            
            self.assertTrue(success)
            self.assertTrue(os.path.exists(output_path))
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


if __name__ == '__main__':
    unittest.main()
