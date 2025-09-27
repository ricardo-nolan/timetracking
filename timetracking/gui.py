import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date, timedelta
from typing import Optional
import threading
import time
import os
import sqlite3
import subprocess
import sys
import shutil
import requests
import json

from .database import TimeTrackerDB
from .pdf_export import PDFExporter
from .email_export import EmailExporter

class TimeTrackerGUI:
    def __init__(self):
        self.db = TimeTrackerDB()
        self.pdf_exporter = PDFExporter()
        self.email_exporter = EmailExporter()
        
        self.root = tk.Tk()
        self.root.title("Time Tracker")
        self.root.geometry("900x700")
        # Ensure tkinter default root is set (helps tests with mocked Tk)
        try:
            if getattr(tk, "_default_root", None) is None:
                tk._default_root = self.root
        except Exception:
            pass
        
        # Timer variables
        self.current_timer = None
        self.timer_running = False
        self.timer_thread = None
        
        self.setup_ui()
        self.refresh_projects()
        self.refresh_entries()
    
    def setup_ui(self):
        """Setup the main UI"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Project management section
        project_frame = ttk.LabelFrame(main_frame, text="Project Management", padding="5")
        project_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        project_frame.columnconfigure(1, weight=1)
        
        ttk.Label(project_frame, text="Project Name:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.project_name_var = tk.StringVar()
        ttk.Entry(project_frame, textvariable=self.project_name_var, width=30).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Label(project_frame, text="Description:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.project_desc_var = tk.StringVar()
        ttk.Entry(project_frame, textvariable=self.project_desc_var, width=30).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 5), pady=(5, 0))
        
        ttk.Label(project_frame, text="Default Email:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.project_email_var = tk.StringVar()
        ttk.Entry(project_frame, textvariable=self.project_email_var, width=30).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(0, 5), pady=(5, 0))
        
        # Rate and currency frame
        rate_frame = ttk.Frame(project_frame)
        rate_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        rate_frame.columnconfigure(1, weight=1)
        rate_frame.columnconfigure(3, weight=1)
        
        ttk.Label(rate_frame, text="Hourly Rate:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.project_rate_var = tk.StringVar()
        ttk.Entry(rate_frame, textvariable=self.project_rate_var, width=15).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Label(rate_frame, text="Currency:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.project_currency_var = tk.StringVar(value="EUR")
        currency_combo = ttk.Combobox(rate_frame, textvariable=self.project_currency_var, width=10, state="readonly")
        currency_combo['values'] = ['EUR', 'USD']
        currency_combo.grid(row=0, column=3, sticky=(tk.W, tk.E))
        
        ttk.Button(project_frame, text="Add Project", command=self.add_project).grid(row=0, column=2, padx=(5, 0))
        ttk.Button(project_frame, text="Edit Project", command=self.edit_project).grid(row=1, column=2, padx=(5, 0), pady=(5, 0))
        ttk.Button(project_frame, text="Delete Project", command=self.delete_project).grid(row=2, column=2, padx=(5, 0), pady=(5, 0))
        
        # Timer section
        timer_frame = ttk.LabelFrame(main_frame, text="Timer", padding="5")
        timer_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        timer_frame.columnconfigure(1, weight=1)
        
        ttk.Label(timer_frame, text="Project:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.project_combo = ttk.Combobox(timer_frame, state="readonly", width=27)
        self.project_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Label(timer_frame, text="Description:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.timer_desc_var = tk.StringVar()
        ttk.Entry(timer_frame, textvariable=self.timer_desc_var, width=30).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 5), pady=(5, 0))
        
        # Timer controls
        control_frame = ttk.Frame(timer_frame)
        control_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        self.start_button = ttk.Button(control_frame, text="Start Timer", command=self.start_timer)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(control_frame, text="Stop Timer", command=self.stop_timer, state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Timer display
        self.timer_label = ttk.Label(control_frame, text="00:00:00", font=("Arial", 16, "bold"))
        self.timer_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # Time entries section
        entries_frame = ttk.LabelFrame(main_frame, text="Time Entries", padding="5")
        entries_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        entries_frame.columnconfigure(0, weight=1)
        entries_frame.rowconfigure(1, weight=1)
        
        # Filter frame
        filter_frame = ttk.Frame(entries_frame)
        filter_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        filter_frame.columnconfigure(1, weight=1)
        
        ttk.Label(filter_frame, text="Filter Project:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.filter_combo = ttk.Combobox(filter_frame, state="readonly")
        self.filter_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        self.filter_combo.bind("<<ComboboxSelected>>", self.on_filter_change)
        
        ttk.Label(filter_frame, text="Date Range:").grid(row=0, column=2, sticky=tk.W, padx=(20, 5))
        self.date_range_var = tk.StringVar(value="Last 7 Days")
        date_combo = ttk.Combobox(filter_frame, textvariable=self.date_range_var, state="readonly", width=15)
        date_combo['values'] = ("All Time", "Today", "This Week", "This Month", "Last 7 Days", "Last 30 Days")
        date_combo.grid(row=0, column=3, sticky=tk.W, padx=(0, 5))
        date_combo.bind("<<ComboboxSelected>>", self.on_filter_change)
        
        ttk.Button(filter_frame, text="Refresh", command=self.refresh_entries).grid(row=0, column=4, padx=(5, 0))
        
        # Treeview for entries
        columns = ("Date", "Project", "Description", "Start", "End", "Duration")
        self.entries_tree = ttk.Treeview(entries_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.entries_tree.heading(col, text=col)
            self.entries_tree.column(col, width=100)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(entries_frame, orient=tk.VERTICAL, command=self.entries_tree.yview)
        self.entries_tree.configure(yscrollcommand=scrollbar.set)
        
        self.entries_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        # Export section
        export_frame = ttk.LabelFrame(main_frame, text="Export", padding="5")
        export_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        ttk.Button(export_frame, text="Export to PDF", command=self.export_pdf).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(export_frame, text="Send Email", command=self.send_email).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(export_frame, text="Email Settings", command=self.email_settings).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(export_frame, text="Edit Entry", command=self.edit_entry).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(export_frame, text="Delete Entry", command=self.delete_entry).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(export_frame, text="Check for Updates", command=self.check_for_updates).pack(side=tk.LEFT, padx=(0, 5))
    
    def refresh_projects(self):
        """Refresh the projects combobox"""
        projects = self.db.get_projects()
        project_names = [f"{name} (ID: {id})" for id, name, desc, email, rate, currency in projects]
        self.project_combo['values'] = project_names
        self.filter_combo['values'] = ["All Projects"] + project_names
        
        if project_names:
            # Set default project to the project of the latest entry
            latest_project_id = self.db.get_latest_entry_project()
            if latest_project_id:
                # Find the index of the latest project
                for i, (id, name, desc, email, rate, currency) in enumerate(projects):
                    if id == latest_project_id:
                        self.project_combo.current(i)
                        self.filter_combo.current(i + 1)  # +1 because filter_combo has "All Projects" at index 0
                        break
                else:
                    # If latest project not found, default to first project
                    self.project_combo.current(0)
                    self.filter_combo.current(0)
            else:
                # No entries yet, default to first project
                self.project_combo.current(0)
                self.filter_combo.current(0)
    
    def refresh_entries(self):
        """Refresh the time entries display"""
        # Clear existing entries
        for item in self.entries_tree.get_children():
            self.entries_tree.delete(item)
        
        # Get filter values
        filter_value = self.filter_combo.get()
        date_range = self.date_range_var.get()
        
        # Determine project filter
        project_id = None
        if filter_value and filter_value != "All Projects":
            try:
                project_id = int(filter_value.split("(ID: ")[1].split(")")[0])
            except (IndexError, ValueError):
                pass
        
        # Determine date range
        start_date = None
        end_date = None
        today = date.today()
        
        if date_range == "Today":
            start_date = end_date = today
        elif date_range == "This Week":
            start_date = today - timedelta(days=today.weekday())
        elif date_range == "This Month":
            start_date = today.replace(day=1)
        elif date_range == "Last 7 Days":
            start_date = today - timedelta(days=7)
        elif date_range == "Last 30 Days":
            start_date = today - timedelta(days=30)
        
        # Get entries
        entries = self.db.get_time_entries(project_id, start_date, end_date)
        
        # Populate treeview
        for entry in entries:
            entry_id, proj_id, proj_name, description, start_time, end_time, duration, rate, currency = entry
            
            # Format date
            start_dt = datetime.fromisoformat(start_time)
            date_str = start_dt.strftime('%Y-%m-%d')
            
            # Format times
            start_time_str = start_dt.strftime('%H:%M')
            if end_time:
                end_dt = datetime.fromisoformat(end_time)
                end_time_str = end_dt.strftime('%H:%M')
            else:
                end_time_str = "Running"
            
            # Format duration
            if duration is not None:
                # Calculate precise duration from timestamps
                if end_time:
                    end_dt = datetime.fromisoformat(end_time)
                    total_seconds = int((end_dt - start_dt).total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60
                    
                    if hours > 0:
                        duration_str = f"{hours}h {minutes}m {seconds}s"
                    elif minutes > 0:
                        duration_str = f"{minutes}m {seconds}s"
                    else:
                        duration_str = f"{seconds}s"
                else:
                    # Fallback to stored duration
                    hours = duration // 60
                    minutes = duration % 60
                    if hours > 0:
                        duration_str = f"{hours}h {minutes}m"
                    else:
                        duration_str = f"{minutes}m"
            else:
                duration_str = "Running"
            
            self.entries_tree.insert("", "end", values=(
                date_str, proj_name, description or "", start_time_str, end_time_str, duration_str
            ), tags=(str(entry_id),))
    
    def add_project(self):
        """Add a new project"""
        name = self.project_name_var.get().strip()
        description = self.project_desc_var.get().strip()
        email = self.project_email_var.get().strip()
        rate_str = self.project_rate_var.get().strip()
        currency = self.project_currency_var.get()
        
        if not name:
            messagebox.showerror("Error", "Project name is required")
            return
        
        # Parse rate if provided
        rate = None
        if rate_str:
            try:
                rate = float(rate_str)
                if rate < 0:
                    messagebox.showerror("Error", "Rate must be positive")
                    return
            except ValueError:
                messagebox.showerror("Error", "Rate must be a valid number")
                return
        
        try:
            self.db.add_project(name, description, email, rate, currency)
            messagebox.showinfo("Success", f"Project '{name}' added successfully")
            self.project_name_var.set("")
            self.project_desc_var.set("")
            self.project_email_var.set("")
            self.project_rate_var.set("")
            self.project_currency_var.set("EUR")
            self.refresh_projects()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    
    def edit_project(self):
        """Edit selected project"""
        selection = self.project_combo.get()
        if not selection:
            messagebox.showerror("Error", "Please select a project to edit")
            return
        
        try:
            project_id = int(selection.split("(ID: ")[1].split(")")[0])
            project_name = selection.split(" (ID:")[0]
            
            # Get project details
            projects = self.db.get_projects()
            project_details = None
            for proj_id, name, desc, email, rate, currency in projects:
                if proj_id == project_id:
                    project_details = (proj_id, name, desc, email, rate, currency)
                    break
            
            if project_details:
                edit_dialog = ProjectEditDialog(self.root, self.db, project_details, self.refresh_projects)
                self.root.wait_window(edit_dialog.dialog)
        except (IndexError, ValueError):
            messagebox.showerror("Error", "Invalid project selection")
    
    def delete_project(self):
        """Delete selected project"""
        selection = self.project_combo.get()
        if not selection:
            messagebox.showerror("Error", "Please select a project to delete")
            return
        
        try:
            project_id = int(selection.split("(ID: ")[1].split(")")[0])
            project_name = selection.split(" (ID:")[0]
            
            if messagebox.askyesno("Confirm", f"Are you sure you want to delete project '{project_name}'?\n\nThis will also delete all associated time entries."):
                # Delete associated time entries and project emails first
                conn = sqlite3.connect(self.db.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM time_entries WHERE project_id = ?", (project_id,))
                cursor.execute("DELETE FROM project_emails WHERE project_id = ?", (project_id,))
                cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Success", f"Project '{project_name}' deleted successfully")
                self.refresh_projects()
        except (IndexError, ValueError):
            messagebox.showerror("Error", "Invalid project selection")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete project: {str(e)}")
    
    def start_timer(self):
        """Start the timer"""
        selection = self.project_combo.get()
        if not selection:
            messagebox.showerror("Error", "Please select a project")
            return
        
        try:
            project_id = int(selection.split("(ID: ")[1].split(")")[0])
            description = self.timer_desc_var.get().strip()
            
            # Check if timer is already running for this project
            running_timer = self.db.get_running_timer(project_id)
            if running_timer:
                messagebox.showerror("Error", "Timer is already running for this project")
                return
            
            # Start timer
            entry_id = self.db.start_timer(project_id, description)
            self.current_timer = entry_id
            self.timer_running = True
            
            # Update UI
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.project_combo.config(state="disabled")
            
            # Start timer thread
            self.timer_thread = threading.Thread(target=self.timer_loop, daemon=True)
            self.timer_thread.start()
            
            messagebox.showinfo("Success", "Timer started")
            
        except (IndexError, ValueError):
            messagebox.showerror("Error", "Invalid project selection")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def stop_timer(self):
        """Stop the timer"""
        if not self.timer_running:
            return
        
        try:
            selection = self.project_combo.get()
            project_id = int(selection.split("(ID: ")[1].split(")")[0])
            
            duration = self.db.stop_timer(project_id)
            if duration is not None:
                # Get the actual entry to calculate precise duration
                entries = self.db.get_time_entries(project_id)
                if entries:
                    entry = entries[0]  # Most recent entry
                    entry_id, proj_id, proj_name, description, start_time, end_time, duration_minutes, rate, currency = entry
                    if end_time:
                        start_dt = datetime.fromisoformat(start_time)
                        end_dt = datetime.fromisoformat(end_time)
                        total_seconds = int((end_dt - start_dt).total_seconds())
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        seconds = total_seconds % 60
                        
                        if hours > 0:
                            duration_str = f"{hours}h {minutes}m {seconds}s"
                        elif minutes > 0:
                            duration_str = f"{minutes}m {seconds}s"
                        else:
                            duration_str = f"{seconds}s"
                    else:
                        # Fallback to stored duration
                        hours = duration // 60
                        minutes = duration % 60
                        duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
                else:
                    # Fallback to stored duration
                    hours = duration // 60
                    minutes = duration % 60
                    duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
                
                messagebox.showinfo("Success", f"Timer stopped. Duration: {duration_str}")
            else:
                messagebox.showerror("Error", "No running timer found")
            
            # Reset UI
            self.timer_running = False
            self.current_timer = None
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.project_combo.config(state="readonly")
            self.timer_label.config(text="00:00:00")
            
            # Refresh entries
            self.refresh_entries()
            
        except (IndexError, ValueError):
            messagebox.showerror("Error", "Invalid project selection")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def timer_loop(self):
        """Timer display loop"""
        start_time = datetime.now()
        while self.timer_running:
            elapsed = datetime.now() - start_time
            hours, remainder = divmod(elapsed.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            
            self.root.after(0, lambda: self.timer_label.config(text=time_str))
            time.sleep(1)
    
    def on_filter_change(self, event=None):
        """Handle filter changes"""
        self.refresh_entries()
    
    def export_pdf(self):
        """Export time entries to PDF"""
        # Get current filter settings
        filter_value = self.filter_combo.get()
        date_range = self.date_range_var.get()
        
        # Determine project filter
        project_id = None
        project_name = None
        if filter_value and filter_value != "All Projects":
            try:
                project_id = int(filter_value.split("(ID: ")[1].split(")")[0])
                project_name = filter_value.split(" (ID:")[0]
            except (IndexError, ValueError):
                pass
        
        # Determine date range
        start_date = None
        end_date = None
        today = date.today()
        
        if date_range == "Today":
            start_date = end_date = today
        elif date_range == "This Week":
            start_date = today - timedelta(days=today.weekday())
        elif date_range == "This Month":
            start_date = today.replace(day=1)
        elif date_range == "Last 7 Days":
            start_date = today - timedelta(days=7)
        elif date_range == "Last 30 Days":
            start_date = today - timedelta(days=30)
        
        # Get entries
        entries = self.db.get_time_entries(project_id, start_date, end_date)
        
        if not entries:
            messagebox.showwarning("Warning", "No time entries found to export")
            return
        
        # Generate default filename with current date
        today = date.today()
        default_filename = f"timesheet_{today.day}_{today.month}_{today.year}.pdf"
        
        # Choose save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save PDF Report",
            initialfile=default_filename
        )
        
        if filename:
            try:
                self.pdf_exporter.export_time_report(
                    entries, filename, project_name, start_date, end_date
                )
                messagebox.showinfo("Success", f"PDF exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export PDF: {e}")
    
    def email_settings(self):
        """Configure email settings"""
        settings_dialog = EmailSettingsDialog(self.root, self.email_exporter)
        self.root.wait_window(settings_dialog.dialog)
    
    def send_email(self):
        """Send time report via email"""
        # Get current project selection
        project_selection = self.project_combo.get()
        project_emails = []
        if project_selection:
            try:
                project_id = int(project_selection.split("(ID: ")[1].split(")")[0])
                project_emails = self.db.get_project_emails(project_id)
            except:
                pass
        
        # Create weekly report dialog with reflection
        weekly_dialog = WeeklyReportDialog(self.root, self.db, self.pdf_exporter, self.email_exporter, project_emails)
        self.root.wait_window(weekly_dialog.dialog)
    
    def edit_entry(self):
        """Edit selected time entry"""
        selection = self.entries_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select an entry to edit")
            return
        
        item = self.entries_tree.item(selection[0])
        entry_id = int(item['tags'][0])
        
        # Get the entry details
        entry = self.db.get_entry(entry_id)
        if not entry:
            messagebox.showerror("Error", "Entry not found")
            return
        
        # Create edit dialog
        edit_dialog = EditEntryDialog(self.root, self.db, entry, self.refresh_entries)
        self.root.wait_window(edit_dialog.dialog)
    
    def delete_entry(self):
        """Delete selected time entry"""
        selection = self.entries_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select an entry to delete")
            return
        
        item = self.entries_tree.item(selection[0])
        entry_id = int(item['tags'][0])
        
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this entry?"):
            if self.db.delete_entry(entry_id):
                messagebox.showinfo("Success", "Entry deleted successfully")
                self.refresh_entries()
            else:
                messagebox.showerror("Error", "Failed to delete entry")
    
    def check_for_updates(self):
        """Check for updates from PyPI"""
        try:
            # Get current version
            current_version = self._get_current_version()
            if not current_version:
                messagebox.showerror("Error", "Could not determine current version")
                return
            
            # Get latest version from PyPI
            latest_version = self._get_latest_version()
            if not latest_version:
                messagebox.showerror("Error", "Could not check for updates. Please check your internet connection.")
                return
            
            # Compare versions
            if self._version_tuple(current_version) < self._version_tuple(latest_version):
                self._run_upgrade_and_prompt_restart(latest_version)
            else:
                messagebox.showinfo("Updates", f"You are running the latest version ({current_version})")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to check for updates: {str(e)}")
    
    def _get_current_version(self):
        """Get current version from package metadata"""
        try:
            import pkg_resources
            return pkg_resources.get_distribution("timetracking").version
        except:
            # Fallback to reading from setup.py or pyproject.toml
            try:
                with open("pyproject.toml", "r") as f:
                    content = f.read()
                    for line in content.split("\n"):
                        if line.strip().startswith("version ="):
                            return line.split("=")[1].strip().strip('"')
            except:
                return "1.0.39"  # Fallback version
    
    def _get_latest_version(self):
        """Get latest version from PyPI"""
        try:
            response = requests.get("https://pypi.org/pypi/timetracking/json", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data["info"]["version"]
            return None
        except:
            return None
    
    def _version_tuple(self, version_str):
        """Convert version string to tuple for comparison"""
        try:
            return tuple(map(int, version_str.split(".")))
        except:
            return (0, 0, 0)
    
    def _run_upgrade_and_prompt_restart(self, target_version):
        """Run upgrade and prompt for restart"""
        result = messagebox.askyesno(
            "Update Available", 
            f"Version {target_version} is available. Would you like to update now?"
        )
        
        if result:
            if self._attempt_upgrade(target_version):
                self._post_upgrade_dialog(target_version)
            else:
                messagebox.showerror("Update Failed", "Failed to update. Please try again later.")
    
    def _attempt_upgrade(self, target_version):
        """Attempt to upgrade the package"""
        try:
            # Check if running under pipx
            if shutil.which('timetracking'):
                # Running under pipx
                cmd = ['pipx', 'upgrade', 'timetracking']
            else:
                # Running under regular pip
                cmd = [sys.executable, '-m', 'pip', 'install', '--upgrade', '--no-cache-dir', f'timetracking=={target_version}']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return result.returncode == 0
        except Exception as e:
            print(f"Upgrade failed: {e}")
            return False
    
    def _post_upgrade_dialog(self, target_version):
        """Show dialog after upgrade with version verification"""
        # Wait for PyPI propagation and verify version
        import time
        max_wait_time = 60  # 1 minute
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            current_version = self._get_current_version()
            if current_version and self._version_tuple(current_version) >= self._version_tuple(target_version):
                # Version successfully updated
                result = messagebox.askyesno(
                    "Restart Required", 
                    f"Successfully updated to version {current_version}. Restart the application now?"
                )
                if result:
                    self._restart_app()
                return
        
        # Timeout - version not updated
        messagebox.showerror(
            "Update Failed", 
            f"Package was not updated to version {target_version} as it hasn't propagated yet. "
            f"Please try again in a few minutes or check your internet connection."
        )
    
    def _restart_app(self):
        """Restart the application"""
        try:
            # Check if running under pipx
            if shutil.which('timetracking'):
                # Running under pipx
                subprocess.Popen(['timetracking'])
            else:
                # Running under regular python
                subprocess.Popen([sys.executable, '-m', 'timetracking'])
            
            # Close current application
            self.root.quit()
            sys.exit(0)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restart: {str(e)}")
    
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()

class EmailDialog:
    def __init__(self, parent, db, pdf_exporter, email_exporter, project_emails=None):
        self.db = db
        self.pdf_exporter = pdf_exporter
        self.email_exporter = email_exporter
        self.project_emails = project_emails or []
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Send Email Report")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup email dialog UI"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Check if email settings are configured
        if not self.email_exporter.sender_email or not self.email_exporter.sender_password:
            ttk.Label(main_frame, text="Email settings not configured!", font=("Arial", 12, "bold"), foreground="red").grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
            ttk.Label(main_frame, text="Please configure your email settings first.").grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 20))
            
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=2, column=0, columnspan=2, pady=(20, 0))
            ttk.Button(button_frame, text="Configure Email Settings", command=self.open_settings).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT)
            return
        
        # Email settings are configured
        ttk.Label(main_frame, text=f"From: {self.email_exporter.sender_email}", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Recipient emails section
        ttk.Label(main_frame, text="Recipient Emails:", font=("Arial", 10, "bold")).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # Email selection frame with checkboxes
        email_frame = ttk.Frame(main_frame)
        email_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Create checkboxes for each project email
        self.email_checkboxes = {}
        self.email_vars = {}
        
        if self.project_emails:
            ttk.Label(email_frame, text="Select recipients:", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
            
            for i, (email_id, email, is_primary) in enumerate(self.project_emails):
                # Create checkbox variable
                var = tk.BooleanVar(value=is_primary)  # Pre-select primary emails
                self.email_vars[email_id] = var
                
                # Create checkbox with label
                checkbox = ttk.Checkbutton(
                    email_frame, 
                    text=f"{email} {'(Primary)' if is_primary else ''}",
                    variable=var
                )
                checkbox.grid(row=i+1, column=0, sticky=tk.W, pady=2)
                self.email_checkboxes[email_id] = checkbox
        else:
            ttk.Label(email_frame, text="No project emails configured", font=("Arial", 9), foreground="gray").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # Custom email entry
        ttk.Label(main_frame, text="Custom Email:").grid(row=3, column=0, sticky=tk.W, pady=(10, 5))
        self.custom_email = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.custom_email, width=40).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=(10, 5))
        
        # Options
        ttk.Label(main_frame, text="Options:").grid(row=4, column=0, sticky=tk.W, pady=(10, 5))
        
        self.include_pdf = tk.BooleanVar(value=False)
        ttk.Checkbutton(main_frame, text="Include PDF attachment", variable=self.include_pdf).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # Include reflection checkbox (pre-selected)
        self.include_reflection = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="Include weekly reflection", variable=self.include_reflection).grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=(20, 0))
        
        ttk.Button(button_frame, text="Send", command=self.send_email_report).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Email Settings", command=self.open_settings).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT)
    
    
    def open_settings(self):
        """Open email settings dialog"""
        from gui import EmailSettingsDialog
        settings_dialog = EmailSettingsDialog(self.dialog, self.email_exporter)
        self.dialog.wait_window(settings_dialog.dialog)
        
        # After settings dialog closes, refresh the email dialog
        self.refresh_dialog()
    
    def refresh_dialog(self):
        """Refresh the email dialog after settings are updated"""
        # Reload email configuration
        self.email_exporter.load_config()
        
        # Clear all widgets from the dialog
        for widget in self.dialog.winfo_children():
            widget.destroy()
        
        # Rebuild the UI with updated settings
        self.setup_ui()
    
    def send_email_report(self):
        """Send the email report"""
        # Get selected emails from checkboxes
        selected_emails = []
        for email_id, var in self.email_vars.items():
            if var.get():  # Checkbox is selected
                # Find the email address for this ID
                for proj_email_id, email, is_primary in self.project_emails:
                    if proj_email_id == email_id:
                        selected_emails.append(email)
                        break
        
        # Get custom email
        custom_email = self.custom_email.get().strip()
        if custom_email:
            selected_emails.append(custom_email)
        
        if not selected_emails:
            messagebox.showerror("Error", "Please select at least one email or enter a custom email")
            return
        
        try:
            # Get time entries from database
            time_entries = self.db.get_time_entries()
            
            # Generate PDF if requested
            pdf_path = None
            if self.include_pdf.get():
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                    pdf_path = tmp_file.name
                    self.pdf_exporter.export_time_report(time_entries, pdf_path)
            
            # Send email to all selected recipients
            success_count = 0
            for recipient in selected_emails:
                try:
                    success = self.email_exporter.send_time_report(
                        time_entries,
                        self.email_exporter.sender_email,
                        self.email_exporter.sender_password,
                        recipient,
                        pdf_path=pdf_path
                    )
                    if success:
                        success_count += 1
                except Exception as e:
                    print(f"Failed to send to {recipient}: {str(e)}")
            
            if success_count > 0:
                messagebox.showinfo("Success", f"Email sent successfully to {success_count} recipient(s)!")
                self.dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to send email to any recipients")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send email: {str(e)}")
        finally:
            # Clean up temporary PDF file
            if pdf_path and os.path.exists(pdf_path):
                try:
                    os.unlink(pdf_path)
                except:
                    pass  # Ignore cleanup errors

class ProjectEditDialog:
    def __init__(self, parent, db, project_details, refresh_callback):
        self.db = db
        self.project_id, self.project_name, self.project_desc, self.project_email, self.project_rate, self.project_currency = project_details
        self.refresh_callback = refresh_callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Project")
        self.dialog.geometry("900x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the project edit dialog UI"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(1, weight=1)
        
        # Project selector
        ttk.Label(main_frame, text="Select Project:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.project_selector = ttk.Combobox(main_frame, state="readonly", width=50)
        self.project_selector.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        self.project_selector.bind("<<ComboboxSelected>>", self.on_project_change)
        
        # Load projects
        self.load_projects()
        
        # Project details
        ttk.Label(main_frame, text="Project Name:").grid(row=1, column=0, sticky=tk.W, pady=(10, 5))
        self.name_var = tk.StringVar(value=self.project_name)
        ttk.Entry(main_frame, textvariable=self.name_var, width=50).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(10, 5))
        
        ttk.Label(main_frame, text="Description:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.desc_var = tk.StringVar(value=self.project_desc or "")
        ttk.Entry(main_frame, textvariable=self.desc_var, width=50).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Rate and currency frame
        rate_currency_frame = ttk.Frame(main_frame)
        rate_currency_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        rate_currency_frame.columnconfigure(1, weight=1)
        rate_currency_frame.columnconfigure(3, weight=1)
        
        ttk.Label(rate_currency_frame, text="Hourly Rate:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.rate_var = tk.StringVar(value=str(self.project_rate) if self.project_rate is not None else "")
        ttk.Entry(rate_currency_frame, textvariable=self.rate_var, width=15).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Label(rate_currency_frame, text="Currency:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.currency_var = tk.StringVar(value=self.project_currency or "EUR")
        currency_combo = ttk.Combobox(rate_currency_frame, textvariable=self.currency_var, width=10, state="readonly")
        currency_combo['values'] = ['EUR', 'USD']
        currency_combo.grid(row=0, column=3, sticky=(tk.W, tk.E))
        
        # Project emails section
        ttk.Label(main_frame, text="Project Emails:", font=("Arial", 10, "bold")).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(20, 5))
        
        # Email list frame
        email_frame = ttk.Frame(main_frame)
        email_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        email_frame.columnconfigure(0, weight=1)
        
        # Email listbox
        self.email_listbox = tk.Listbox(email_frame, height=6)
        self.email_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        # Email scrollbar
        email_scrollbar = ttk.Scrollbar(email_frame, orient=tk.VERTICAL, command=self.email_listbox.yview)
        email_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.email_listbox.configure(yscrollcommand=email_scrollbar.set)
        
        # Email management buttons
        email_btn_frame = ttk.Frame(main_frame)
        email_btn_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        email_btn_frame.columnconfigure(1, weight=1)
        
        ttk.Label(email_btn_frame, text="New Email:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.new_email_var = tk.StringVar()
        ttk.Entry(email_btn_frame, textvariable=self.new_email_var, width=40).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(email_btn_frame, text="Add Email", command=self.add_email).grid(row=0, column=2, padx=(5, 0))
        ttk.Button(email_btn_frame, text="Remove Selected", command=self.remove_email).grid(row=0, column=3, padx=(5, 0))
        ttk.Button(email_btn_frame, text="Set as Primary", command=self.set_primary).grid(row=0, column=4, padx=(5, 0))
        
        # Load existing emails
        self.load_emails()
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=(20, 0))
        
        ttk.Button(button_frame, text="Save", command=self.save_project).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT)
    
    def load_projects(self):
        """Load all projects into the selector"""
        projects = self.db.get_projects()
        project_names = [f"{name} (ID: {id})" for id, name, desc, email, rate, currency in projects]
        self.project_selector['values'] = project_names
        
        # Set current project as selected
        current_project_name = f"{self.project_name} (ID: {self.project_id})"
        for i, project_name in enumerate(project_names):
            if project_name == current_project_name:
                self.project_selector.current(i)
                break
    
    def on_project_change(self, event=None):
        """Handle project selection change and refresh all fields"""
        selection = self.project_selector.get()
        if not selection:
            return
        try:
            project_id = int(selection.split("(ID: ")[1].split(")")[0])
        except (IndexError, ValueError):
            return

        # Find the selected project and update all related fields
        projects = self.db.get_projects()
        for proj in projects:
            # Unpack full tuple: (id, name, desc, email, rate, currency)
            try:
                proj_id, name, desc, email, rate, currency = proj
            except ValueError:
                # Skip malformed rows
                continue
            if proj_id == project_id:
                self.project_id = proj_id
                self.project_name = name
                self.project_desc = desc or ""
                self.project_email = email
                self.project_rate = rate
                self.project_currency = currency or "EUR"

                # Update UI variables
                self.name_var.set(self.project_name)
                self.desc_var.set(self.project_desc)
                self.rate_var.set("" if self.project_rate is None else str(self.project_rate))
                self.currency_var.set(self.project_currency)

                # Reload emails for the newly selected project
                self.load_emails()
                break
    
    def load_emails(self):
        """Load project emails into the listbox"""
        self.email_listbox.delete(0, tk.END)
        self.email_data = {}  # Store email_id -> email mapping
        emails = self.db.get_project_emails(self.project_id)
        for email_id, email, is_primary in emails:
            display_text = f"{email} {'(Primary)' if is_primary else ''}"
            self.email_listbox.insert(tk.END, display_text)
            # Store email_id mapping
            self.email_data[display_text] = email_id
    
    def add_email(self):
        """Add a new email to the project"""
        email = self.new_email_var.get().strip()
        if not email:
            messagebox.showerror("Error", "Please enter an email address")
            return
        
        if "@" not in email:
            messagebox.showerror("Error", "Please enter a valid email address")
            return
        
        try:
            self.db.add_project_email(self.project_id, email)
            self.new_email_var.set("")
            self.load_emails()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add email: {str(e)}")
    
    def remove_email(self):
        """Remove selected email from the project"""
        selection = self.email_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select an email to remove")
            return
        
        # Get the email ID from the selected display text
        selected_index = selection[0]
        display_text = self.email_listbox.get(selected_index)
        if display_text in self.email_data:
            email_id = self.email_data[display_text]
            try:
                self.db.delete_project_email(email_id)
                self.load_emails()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to remove email: {str(e)}")
    
    def set_primary(self):
        """Set selected email as primary"""
        selection = self.email_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select an email to set as primary")
            return
        
        # Get the email ID from the selected display text
        selected_index = selection[0]
        display_text = self.email_listbox.get(selected_index)
        if display_text in self.email_data:
            email_id = self.email_data[display_text]
            try:
                # First, unset all primary emails for this project
                emails = self.db.get_project_emails(self.project_id)
                for eid, email, is_primary in emails:
                    if is_primary:
                        # Update to non-primary
                        conn = sqlite3.connect(self.db.db_path)
                        cursor = conn.cursor()
                        cursor.execute("UPDATE project_emails SET is_primary = 0 WHERE id = ?", (eid,))
                        conn.commit()
                        conn.close()
                
                # Set the selected email as primary
                conn = sqlite3.connect(self.db.db_path)
                cursor = conn.cursor()
                cursor.execute("UPDATE project_emails SET is_primary = 1 WHERE id = ?", (email_id,))
                conn.commit()
                conn.close()
                
                self.load_emails()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to set primary email: {str(e)}")
    
    def save_project(self):
        """Save project changes"""
        name = self.name_var.get().strip()
        description = self.desc_var.get().strip()
        rate_str = self.rate_var.get().strip()
        currency = self.currency_var.get()
        
        if not name:
            messagebox.showerror("Error", "Project name is required")
            return
        
        # Parse rate if provided, allow empty to unset rate
        rate = None
        if rate_str:
            try:
                rate = float(rate_str)
                if rate < 0:
                    messagebox.showerror("Error", "Rate must be positive")
                    return
            except ValueError:
                messagebox.showerror("Error", "Rate must be a valid number")
                return
        
        try:
            self.db.update_project(self.project_id, name, description, rate, currency)
            messagebox.showinfo("Success", "Project updated successfully")
            self.refresh_callback()
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update project: {str(e)}")

class EditEntryDialog:
    def __init__(self, parent, db, entry, refresh_callback):
        self.db = db
        self.entry = entry
        self.refresh_callback = refresh_callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Time Entry")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup edit dialog UI"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Entry ID (read-only)
        ttk.Label(main_frame, text="Entry ID:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.entry_id_var = tk.StringVar(value=str(self.entry[0]))
        ttk.Entry(main_frame, textvariable=self.entry_id_var, state="readonly", width=20).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Project (selectable)
        ttk.Label(main_frame, text="Project:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.project_combo = ttk.Combobox(main_frame, state="readonly", width=37)
        self.project_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Populate projects
        projects = self.db.get_projects()
        project_names = [f"{name} (ID: {id})" for id, name, desc, email, rate, currency in projects]
        self.project_combo['values'] = project_names
        
        # Set current project as selected
        current_project_id = self.entry[1]
        for i, (id, name, desc, email, rate, currency) in enumerate(projects):
            if id == current_project_id:
                self.project_combo.current(i)
                break
        
        # Description
        ttk.Label(main_frame, text="Description:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.description_var = tk.StringVar(value=self.entry[3] or "")
        ttk.Entry(main_frame, textvariable=self.description_var, width=40).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Start time
        ttk.Label(main_frame, text="Start Time:").grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        start_dt = datetime.fromisoformat(self.entry[4])
        self.start_date_var = tk.StringVar(value=start_dt.strftime('%Y-%m-%d'))
        self.start_time_var = tk.StringVar(value=start_dt.strftime('%H:%M:%S'))
        
        start_frame = ttk.Frame(main_frame)
        start_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        ttk.Entry(start_frame, textvariable=self.start_date_var, width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(start_frame, textvariable=self.start_time_var, width=12).pack(side=tk.LEFT)
        
        # Bind events to update duration when times change
        self.start_date_var.trace_add('write', self.update_duration)
        self.start_time_var.trace_add('write', self.update_duration)
        
        # End time
        ttk.Label(main_frame, text="End Time:").grid(row=4, column=0, sticky=tk.W, pady=(0, 5))
        if self.entry[5]:  # If end_time exists
            end_dt = datetime.fromisoformat(self.entry[5])
            self.end_date_var = tk.StringVar(value=end_dt.strftime('%Y-%m-%d'))
            self.end_time_var = tk.StringVar(value=end_dt.strftime('%H:%M:%S'))
        else:
            self.end_date_var = tk.StringVar(value="")
            self.end_time_var = tk.StringVar(value="")
        
        end_frame = ttk.Frame(main_frame)
        end_frame.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        ttk.Entry(end_frame, textvariable=self.end_date_var, width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(end_frame, textvariable=self.end_time_var, width=12).pack(side=tk.LEFT)
        
        # Bind events to update duration when times change
        self.end_date_var.trace_add('write', self.update_duration)
        self.end_time_var.trace_add('write', self.update_duration)
        
        # Duration (calculated, read-only)
        ttk.Label(main_frame, text="Duration:").grid(row=5, column=0, sticky=tk.W, pady=(0, 5))
        
        # Initialize duration variable
        self.duration_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.duration_var, state="readonly", width=20).grid(row=5, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Calculate initial duration
        self.update_duration()
        
        # Help text
        help_text = "Date format: YYYY-MM-DD\nTime format: HH:MM:SS\nLeave end time empty for running timers"
        ttk.Label(main_frame, text=help_text, font=("Arial", 8)).grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=(20, 0))
        
        ttk.Button(button_frame, text="Save", command=self.save_entry).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT)
    
    def update_duration(self, *args):
        """Update the duration display when time fields change"""
        try:
            # Get start time
            start_date = self.start_date_var.get().strip()
            start_time = self.start_time_var.get().strip()
            
            if not start_date or not start_time:
                self.duration_var.set("Invalid start time")
                return
            
            start_datetime_str = f"{start_date}T{start_time}"
            start_dt = datetime.fromisoformat(start_datetime_str)
            
            # Get end time
            end_date = self.end_date_var.get().strip()
            end_time = self.end_time_var.get().strip()
            
            if not end_date or not end_time:
                self.duration_var.set("Running")
                return
            
            end_datetime_str = f"{end_date}T{end_time}"
            end_dt = datetime.fromisoformat(end_datetime_str)
            
            # Calculate duration
            if end_dt < start_dt:
                self.duration_var.set("Invalid (end < start)")
                return
            
            total_seconds = int((end_dt - start_dt).total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            if hours > 0:
                duration_str = f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                duration_str = f"{minutes}m {seconds}s"
            else:
                duration_str = f"{seconds}s"
            
            self.duration_var.set(duration_str)
            
        except ValueError:
            self.duration_var.set("Invalid format")
        except Exception:
            self.duration_var.set("Error calculating")
    
    def save_entry(self):
        """Save the edited entry"""
        try:
            # Validate and parse start time
            start_date = self.start_date_var.get().strip()
            start_time = self.start_time_var.get().strip()
            if not start_date or not start_time:
                messagebox.showerror("Error", "Start date and time are required")
                return
            
            start_datetime_str = f"{start_date}T{start_time}"
            datetime.fromisoformat(start_datetime_str)  # Validate format
            
            # Validate and parse end time (if provided)
            end_date = self.end_date_var.get().strip()
            end_time = self.end_time_var.get().strip()
            end_datetime_str = None
            
            if end_date and end_time:
                end_datetime_str = f"{end_date}T{end_time}"
                datetime.fromisoformat(end_datetime_str)  # Validate format
            elif end_date or end_time:
                messagebox.showerror("Error", "Both end date and time must be provided, or leave both empty")
                return
            
            # Get selected project ID (default to current if unchanged)
            project_selection = self.project_combo.get()
            if project_selection:
                try:
                    project_id = int(project_selection.split("(ID: ")[1].split(")")[0])
                except (IndexError, ValueError):
                    messagebox.showerror("Error", "Invalid project selection")
                    return
            else:
                project_id = self.entry[1]
            
            # Update the entry
            description = self.description_var.get().strip() or None
            success = self.db.update_entry(
                self.entry[0],  # entry_id
                description=description,
                start_time=start_datetime_str,
                end_time=end_datetime_str,
                project_id=project_id
            )
            
            if success:
                messagebox.showinfo("Success", "Entry updated successfully")
                self.refresh_callback()
                self.dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to update entry")
                
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid date/time format: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update entry: {e}")

class WeeklyReportDialog:
    def __init__(self, parent, db, pdf_exporter, email_exporter, project_emails=None):
        self.db = db
        self.pdf_exporter = pdf_exporter
        self.email_exporter = email_exporter
        self.project_emails = project_emails or []
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Weekly Report with Reflection")
        self.dialog.geometry("800x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup weekly report dialog UI"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Check if email settings are configured
        if not self.email_exporter.sender_email or not self.email_exporter.sender_password:
            ttk.Label(main_frame, text="Email settings not configured!", font=("Arial", 12, "bold"), foreground="red").grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
            ttk.Label(main_frame, text="Please configure your email settings first.").grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 20))
            
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=2, column=0, columnspan=2, pady=(20, 0))
            ttk.Button(button_frame, text="Configure Email Settings", command=self.open_settings).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT)
            return
        
        # Email settings are configured
        ttk.Label(main_frame, text=f"From: {self.email_exporter.sender_email}", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Recipient emails section
        ttk.Label(main_frame, text="Recipient Emails:", font=("Arial", 10, "bold")).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # Email selection frame with checkboxes
        email_frame = ttk.Frame(main_frame)
        email_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Create checkboxes for each project email
        self.email_checkboxes = {}
        self.email_vars = {}
        
        if self.project_emails:
            ttk.Label(email_frame, text="Select recipients:", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
            
            for i, (email_id, email, is_primary) in enumerate(self.project_emails):
                # Create checkbox variable
                var = tk.BooleanVar(value=is_primary)  # Pre-select primary emails
                self.email_vars[email_id] = var
                
                # Create checkbox with label
                checkbox = ttk.Checkbutton(
                    email_frame, 
                    text=f"{email} {'(Primary)' if is_primary else ''}",
                    variable=var
                )
                checkbox.grid(row=i+1, column=0, sticky=tk.W, pady=2)
                self.email_checkboxes[email_id] = checkbox
        else:
            ttk.Label(email_frame, text="No project emails configured", font=("Arial", 9), foreground="gray").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # Custom email entry
        ttk.Label(main_frame, text="Custom Email:").grid(row=3, column=0, sticky=tk.W, pady=(10, 5))
        self.custom_email = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.custom_email, width=40).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=(10, 5))
        
        # Weekly Reflection Section
        ttk.Label(main_frame, text="Weekly Reflection (MSE Requirement):", font=("Arial", 10, "bold")).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(20, 5))
        
        # Reflection template
        reflection_template = """• Key achievements this week:
• Challenges encountered:
• Lessons learned:
• Goals for next week:
• Additional observations:"""
        
        ttk.Label(main_frame, text="Please reflect on your week using the template below:", font=("Arial", 9)).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # Reflection text area - make it bigger
        reflection_frame = ttk.Frame(main_frame)
        reflection_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.reflection_text = tk.Text(reflection_frame, height=12, width=80, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(reflection_frame, orient=tk.VERTICAL, command=self.reflection_text.yview)
        self.reflection_text.configure(yscrollcommand=scrollbar.set)
        
        self.reflection_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Insert template
        self.reflection_text.insert(tk.END, reflection_template)
        
        # Options
        ttk.Label(main_frame, text="Options:").grid(row=7, column=0, sticky=tk.W, pady=(10, 5))
        
        self.include_pdf = tk.BooleanVar(value=False)
        ttk.Checkbutton(main_frame, text="Include PDF attachment", variable=self.include_pdf).grid(row=8, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # Include reflection checkbox (pre-selected)
        self.include_reflection = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="Include weekly reflection", variable=self.include_reflection).grid(row=9, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=10, column=0, columnspan=2, pady=(20, 0))
        
        ttk.Button(button_frame, text="Send Weekly Report", command=self.send_weekly_report).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Email Settings", command=self.open_settings).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT)
    
    def open_settings(self):
        """Open email settings dialog"""
        settings_dialog = EmailSettingsDialog(self.dialog, self.email_exporter)
        self.dialog.wait_window(settings_dialog.dialog)
        
        # After settings dialog closes, refresh the dialog
        self.refresh_dialog()
    
    def refresh_dialog(self):
        """Refresh the dialog after settings are updated"""
        # Reload email configuration
        self.email_exporter.load_config()
        
        # Destroy and recreate the dialog
        self.dialog.destroy()
        # Note: This will require the parent to recreate the dialog
    
    def send_weekly_report(self):
        """Send the weekly report with reflection"""
        # Get selected emails from checkboxes
        selected_emails = []
        for email_id, var in self.email_vars.items():
            if var.get():  # Checkbox is selected
                # Find the email address for this ID
                for proj_email_id, email, is_primary in self.project_emails:
                    if proj_email_id == email_id:
                        selected_emails.append(email)
                        break
        
        # Get custom email
        custom_email = self.custom_email.get().strip()
        if custom_email:
            selected_emails.append(custom_email)
        
        if not selected_emails:
            messagebox.showerror("Error", "Please select at least one email or enter a custom email")
            return
        
        # Get reflection text (only if reflection is enabled)
        reflection_content = ""
        if self.include_reflection.get():
            reflection_content = self.reflection_text.get("1.0", tk.END).strip()
            if not reflection_content or reflection_content == "• Key achievements this week:\n• Challenges encountered:\n• Lessons learned:\n• Goals for next week:\n• Additional observations:":
                messagebox.showerror("Error", "Please provide your weekly reflection")
                return
        
        try:
            # Get time entries for the current week
            today = datetime.now().date()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            
            # Get entries for the week
            entries = self.db.get_time_entries()
            weekly_entries = []
            for entry in entries:
                entry_date = datetime.fromisoformat(entry[4]).date()  # start_time
                if start_of_week <= entry_date <= end_of_week:
                    weekly_entries.append(entry)
            
            if not weekly_entries:
                messagebox.showwarning("Warning", "No time entries found for this week")
                return
            
            # Create email content with reflection
            subject = f"Weekly Report - Week of {start_of_week.strftime('%B %d, %Y')}"
            
            # Generate timesheet content
            timesheet_content = self.generate_timesheet_content(weekly_entries)
            
            # Generate HTML formatted email
            html_timesheet = self.generate_html_timesheet(weekly_entries)
            
            # Combine timesheet and reflection in HTML format
            email_body = f"""
            <div style='font-family: Arial, sans-serif; line-height: 1.6; color: #333;'>
                <p>Please find attached my weekly timesheet for the week of {start_of_week.strftime('%B %d, %Y')}.</p>
                
                {html_timesheet}
                """
            
            # Add reflection section only if enabled
            if self.include_reflection.get() and reflection_content:
                email_body += f"""
                <div style='margin-top: 30px; padding: 20px; background-color: #f8f9fa; border-left: 4px solid #3498db;'>
                    <h3 style='color: #2c3e50; margin-top: 0; margin-bottom: 15px;'>WEEKLY REFLECTION:</h3>
                    <div style='white-space: pre-line; font-size: 14px;'>{reflection_content}</div>
                </div>
                """
            
            email_body += f"""
                
                <p style='margin-top: 30px;'>Best regards,<br>{getattr(self.email_exporter, 'student_name', 'Student')}</p>
            </div>
            """
            
            # Send email using the existing send_time_report method
            # We need to create a custom email with the reflection content
            success = self.send_custom_email(
                selected_emails,
                subject,
                email_body,
                weekly_entries if self.include_pdf.get() else None
            )
            
            if success:
                messagebox.showinfo("Success", "Weekly report sent successfully!")
                self.dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to send weekly report")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send weekly report: {str(e)}")
    
    def generate_timesheet_content(self, entries):
        """Generate timesheet content for email"""
        content = "TIMESHEET SUMMARY:\n\n"
        
        total_hours = 0
        for entry in entries:
            entry_id, project_id, project_name, description, start_time, end_time, duration, rate, currency = entry
            
            # Format dates and times
            start_dt = datetime.fromisoformat(start_time)
            date_str = start_dt.strftime('%Y-%m-%d')
            start_time_str = start_dt.strftime('%H:%M')
            
            if end_time:
                end_dt = datetime.fromisoformat(end_time)
                end_time_str = end_dt.strftime('%H:%M')
            else:
                end_time_str = "Running"
            
            # Format duration
            if duration is not None:
                hours = duration // 60
                minutes = duration % 60
                if hours > 0:
                    duration_str = f"{hours}h {minutes}m"
                else:
                    duration_str = f"{minutes}m"
                total_hours += duration / 60.0
            else:
                duration_str = "Running"
            
            content += f"Date: {date_str}\n"
            content += f"Project: {project_name}\n"
            content += f"Description: {description or 'N/A'}\n"
            content += f"Time: {start_time_str} - {end_time_str}\n"
            content += f"Duration: {duration_str}\n\n"
        
        content += f"Total Hours: {total_hours:.1f}\n"
        return content
    
    def generate_html_timesheet(self, entries):
        """Generate HTML formatted timesheet for email"""
        html = """
        <h3 style='color: #2c3e50; margin-bottom: 15px;'>TIMESHEET SUMMARY:</h3>
        <table border='1' cellpadding='8' cellspacing='0' style='border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size: 14px;'>
        <thead>
            <tr style='background-color: #34495e; color: white; font-weight: bold;'>
                <th style='padding: 10px; text-align: left;'>Date</th>
                <th style='padding: 10px; text-align: left;'>Project</th>
                <th style='padding: 10px; text-align: left;'>Description</th>
                <th style='padding: 10px; text-align: left;'>Time</th>
                <th style='padding: 10px; text-align: left;'>Duration</th>
            </tr>
        </thead>
        <tbody>
        """
        
        total_hours = 0
        for entry in entries:
            entry_id, project_id, project_name, description, start_time, end_time, duration, rate, currency = entry
            
            # Format dates and times
            start_dt = datetime.fromisoformat(start_time)
            date_str = start_dt.strftime('%Y-%m-%d')
            start_time_str = start_dt.strftime('%H:%M')
            
            if end_time:
                end_dt = datetime.fromisoformat(end_time)
                end_time_str = end_dt.strftime('%H:%M')
            else:
                end_time_str = "Running"
            
            # Format duration
            if duration is not None:
                hours = duration // 60
                minutes = duration % 60
                if hours > 0:
                    duration_str = f"{hours}h {minutes}m"
                else:
                    duration_str = f"{minutes}m"
                total_hours += duration / 60.0
            else:
                duration_str = "Running"
            
            html += f"""
            <tr style='background-color: #f8f9fa; border-bottom: 1px solid #dee2e6;'>
                <td style='padding: 10px; border-right: 1px solid #dee2e6;'>{date_str}</td>
                <td style='padding: 10px; border-right: 1px solid #dee2e6; font-weight: bold; color: #2c3e50;'>{project_name}</td>
                <td style='padding: 10px; border-right: 1px solid #dee2e6;'>{description or 'N/A'}</td>
                <td style='padding: 10px; border-right: 1px solid #dee2e6;'>{start_time_str} - {end_time_str}</td>
                <td style='padding: 10px; font-weight: bold; color: #27ae60;'>{duration_str}</td>
            </tr>
            """
        
        html += f"""
        </tbody>
        <tfoot>
            <tr style='background-color: #3498db; color: white; font-weight: bold; font-size: 16px;'>
                <td colspan='4' style='padding: 15px; text-align: right;'>Total Hours:</td>
                <td style='padding: 15px; text-align: center; font-size: 18px;'>{total_hours:.1f}</td>
            </tr>
        </tfoot>
        </table>
        """
        return html
    
    def send_custom_email(self, recipients, subject, body, time_entries=None):
        """Send custom email with optional PDF attachment"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            from email import encoders
            import tempfile
            import os
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_exporter.sender_email
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            # Add body as HTML with proper content type
            html_body = MIMEText(body, 'html', 'utf-8')
            msg.attach(html_body)
            
            # Add PDF attachment if requested and entries provided
            if time_entries and self.include_pdf.get():
                try:
                    # Create temporary PDF
                    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                        pdf_path = temp_file.name
                    
                    # Generate PDF
                    self.pdf_exporter.export_time_report(time_entries, pdf_path)
                    
                    # Attach PDF
                    with open(pdf_path, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= weekly_report.pdf'
                    )
                    msg.attach(part)
                    
                    # Clean up temp file
                    os.unlink(pdf_path)
                    
                except Exception as e:
                    print(f"Warning: Could not attach PDF: {e}")
            
            # Send email
            server = smtplib.SMTP(self.email_exporter.smtp_server, self.email_exporter.smtp_port)
            server.starttls()
            server.login(self.email_exporter.sender_email, self.email_exporter.sender_password)
            
            text = msg.as_string()
            server.sendmail(self.email_exporter.sender_email, recipients, text)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False

class EmailSettingsDialog:
    def __init__(self, parent, email_exporter):
        self.email_exporter = email_exporter
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Email Settings")
        self.dialog.geometry("600x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup email settings dialog UI"""
        # Create a canvas and scrollbar for scrollable content
        canvas = tk.Canvas(self.dialog)
        scrollbar = ttk.Scrollbar(self.dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        main_frame = ttk.Frame(scrollable_frame, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # SMTP Settings
        ttk.Label(main_frame, text="SMTP Settings", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Provider presets
        ttk.Label(main_frame, text="Email Provider:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.provider_combo = ttk.Combobox(main_frame, state="readonly", width=37)
        self.provider_combo['values'] = (
            "Custom (enter manually)",
            "Gmail (smtp.gmail.com:587)",
            "Outlook/Hotmail (smtp-mail.outlook.com:587)",
            "Yahoo (smtp.mail.yahoo.com:587)",
            "iCloud (smtp.mail.me.com:587)"
        )
        self.provider_combo.current(1)  # Set Gmail as default
        self.provider_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        self.provider_combo.bind("<<ComboboxSelected>>", self.on_provider_change)
        
        ttk.Label(main_frame, text="SMTP Server:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.smtp_server = tk.StringVar(value="smtp.gmail.com")
        ttk.Entry(main_frame, textvariable=self.smtp_server, width=40).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Label(main_frame, text="SMTP Port:").grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        self.smtp_port = tk.StringVar(value="587")
        ttk.Entry(main_frame, textvariable=self.smtp_port, width=40).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Email Credentials
        ttk.Label(main_frame, text="Email Credentials", font=("Arial", 12, "bold")).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(20, 10))
        
        ttk.Label(main_frame, text="Your Email:").grid(row=5, column=0, sticky=tk.W, pady=(0, 5))
        self.sender_email = tk.StringVar(value=self.email_exporter.sender_email or "")
        ttk.Entry(main_frame, textvariable=self.sender_email, width=40).grid(row=5, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Password field with status indicator
        password_label_text = "Password/App Password:"
        if self.email_exporter.sender_password:
            password_label_text += " (already configured)"
        ttk.Label(main_frame, text=password_label_text).grid(row=6, column=0, sticky=tk.W, pady=(0, 5))
        self.sender_password = tk.StringVar()
        password_entry = ttk.Entry(main_frame, textvariable=self.sender_password, show="*", width=40)
        password_entry.grid(row=6, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Add placeholder text if password is already stored
        if self.email_exporter.sender_password:
            password_entry.insert(0, "Leave blank to keep current password")
            password_entry.configure(foreground="gray")
            
            def on_password_focus_in(event):
                if password_entry.get() == "Leave blank to keep current password":
                    password_entry.delete(0, tk.END)
                    password_entry.configure(foreground="black")
            
            def on_password_focus_out(event):
                if not password_entry.get():
                    password_entry.insert(0, "Leave blank to keep current password")
                    password_entry.configure(foreground="gray")
            
            password_entry.bind("<FocusIn>", on_password_focus_in)
            password_entry.bind("<FocusOut>", on_password_focus_out)
        
        # Student Information
        ttk.Label(main_frame, text="Student Information", font=("Arial", 12, "bold")).grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=(20, 10))
        
        ttk.Label(main_frame, text="Student Name:").grid(row=8, column=0, sticky=tk.W, pady=(0, 5))
        self.student_name = tk.StringVar(value=getattr(self.email_exporter, 'student_name', '') or "")
        ttk.Entry(main_frame, textvariable=self.student_name, width=40).grid(row=8, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Help text
        help_text = """Common SMTP Settings:
• Gmail: smtp.gmail.com, port 587 (requires App Password)
• Outlook/Hotmail: smtp-mail.outlook.com, port 587
• Yahoo: smtp.mail.yahoo.com, port 587
• iCloud: smtp.mail.me.com, port 587
• Custom: Use your provider's SMTP settings

GMAIL USERS:
- Enable 2-Factor Authentication
- Generate App Password (not regular password)
- Use 16-character App Password

OTHER PROVIDERS:
- Usually use your regular email and password
- Some may require App Passwords (check with your provider)
- Port 587 is most common (TLS/STARTTLS)

Test your connection to verify settings work!"""
        
        ttk.Label(main_frame, text=help_text, font=("Arial", 9), justify=tk.LEFT).grid(row=9, column=0, columnspan=2, sticky=tk.W, pady=(20, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=10, column=0, columnspan=2, pady=(30, 20), sticky=(tk.W, tk.E))
        
        ttk.Button(button_frame, text="Test Connection", command=self.test_connection, width=15).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Save Settings", command=self.save_settings, width=15).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy, width=15).pack(side=tk.LEFT)
    
    def on_provider_change(self, event=None):
        """Handle provider selection change"""
        selection = self.provider_combo.get()
        
        if "Gmail" in selection:
            self.smtp_server.set("smtp.gmail.com")
            self.smtp_port.set("587")
        elif "Outlook" in selection:
            self.smtp_server.set("smtp-mail.outlook.com")
            self.smtp_port.set("587")
        elif "Yahoo" in selection:
            self.smtp_server.set("smtp.mail.yahoo.com")
            self.smtp_port.set("587")
        elif "iCloud" in selection:
            self.smtp_server.set("smtp.mail.me.com")
            self.smtp_port.set("587")
        elif "Custom" in selection:
            # Clear fields for custom configuration
            self.smtp_server.set("")
            self.smtp_port.set("")
    
    def test_connection(self):
        """Test SMTP connection"""
        try:
            smtp_server = self.smtp_server.get().strip()
            smtp_port = int(self.smtp_port.get().strip())
            sender_email = self.sender_email.get().strip()
            sender_password = self.sender_password.get().strip()
            
            if not all([smtp_server, sender_email, sender_password]):
                messagebox.showerror("Error", "Please fill in all fields")
                return
            
            # Test connection
            import smtplib
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            server.quit()
            
            messagebox.showinfo("Success", "SMTP connection successful!")
            
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
        except Exception as e:
            error_msg = str(e)
            if "Application-specific password required" in error_msg:
                messagebox.showerror("App Password Required", 
                    "This email provider requires an App Password.\n\n"
                    "Gmail: Enable 2FA → Generate App Password\n"
                    "Outlook: May need App Password for some accounts\n"
                    "Yahoo: Check security settings for App Passwords\n\n"
                    "Use the App Password (not your regular password)")
            elif "Authentication failed" in error_msg or "Invalid credentials" in error_msg:
                messagebox.showerror("Authentication Failed", 
                    "Invalid email or password.\n\n"
                    "Check:\n"
                    "• Email address is correct\n"
                    "• Password is correct\n"
                    "• Using App Password if required\n"
                    "• Account has SMTP access enabled")
            elif "Connection refused" in error_msg or "Connection timed out" in error_msg:
                messagebox.showerror("Connection Failed", 
                    "Cannot connect to SMTP server.\n\n"
                    "Check:\n"
                    "• SMTP server address is correct\n"
                    "• Port number is correct (usually 587)\n"
                    "• Internet connection is working\n"
                    "• Firewall isn't blocking the connection")
            else:
                messagebox.showerror("Connection Error", f"SMTP connection failed:\n\n{e}")
    
    def save_settings(self):
        """Save email settings"""
        try:
            smtp_server = self.smtp_server.get().strip()
            smtp_port = int(self.smtp_port.get().strip())
            sender_email = self.sender_email.get().strip()
            sender_password = self.sender_password.get().strip()
            student_name = self.student_name.get().strip()
            
            # Handle placeholder text
            if sender_password == "Leave blank to keep current password":
                sender_password = ""
            
            if not all([smtp_server, sender_email]):
                messagebox.showerror("Error", "Please fill in SMTP server and email address")
                return
            
            # Only require password if it's not already stored
            if not sender_password and not self.email_exporter.sender_password:
                messagebox.showerror("Error", "Please enter your password or app password")
                return
            
            # Update email exporter settings
            self.email_exporter.smtp_server = smtp_server
            self.email_exporter.smtp_port = smtp_port
            
            # Store credentials (password will be encrypted automatically)
            self.email_exporter.sender_email = sender_email
            # Only update password if a new one is provided
            if sender_password:
                self.email_exporter.sender_password = sender_password
            
            # Store student name
            self.email_exporter.student_name = student_name
            
            # Save to config file
            self.email_exporter.save_config()
            
            messagebox.showinfo("Success", "Email settings saved successfully!")
            self.dialog.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
