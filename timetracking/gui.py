import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date, timedelta
from typing import Optional
import threading
import time
import os
import sqlite3

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
        
        # Create email dialog
        email_dialog = EmailDialog(self.root, self.db, self.pdf_exporter, self.email_exporter, project_emails)
        self.root.wait_window(email_dialog.dialog)
    
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
        
        self.include_pdf = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="Include PDF attachment", variable=self.include_pdf).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=(20, 0))
        
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
        """Handle project selection change"""
        selection = self.project_selector.get()
        if selection:
            try:
                project_id = int(selection.split("(ID: ")[1].split(")")[0])
                projects = self.db.get_projects()
                for proj_id, name, desc, email in projects:
                    if proj_id == project_id:
                        self.project_id = proj_id
                        self.name_var.set(name)
                        self.desc_var.set(desc or "")
                        self.load_emails()
                        break
            except (IndexError, ValueError):
                pass
    
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
        
        ttk.Label(main_frame, text="Password/App Password:").grid(row=6, column=0, sticky=tk.W, pady=(0, 5))
        self.sender_password = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.sender_password, show="*", width=40).grid(row=6, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        
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
        
        ttk.Label(main_frame, text=help_text, font=("Arial", 9), justify=tk.LEFT).grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=(20, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=(30, 20), sticky=(tk.W, tk.E))
        
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
            
            if not all([smtp_server, sender_email, sender_password]):
                messagebox.showerror("Error", "Please fill in all fields")
                return
            
            # Update email exporter settings
            self.email_exporter.smtp_server = smtp_server
            self.email_exporter.smtp_port = smtp_port
            
            # Store credentials (password will be encrypted automatically)
            self.email_exporter.sender_email = sender_email
            self.email_exporter.sender_password = sender_password
            
            # Save to config file
            self.email_exporter.save_config()
            
            messagebox.showinfo("Success", "Email settings saved successfully!")
            self.dialog.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
