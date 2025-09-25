import sqlite3
import datetime
import os
from typing import List, Optional, Tuple

class TimeTrackerDB:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Use user's home directory for database
            home_dir = os.path.expanduser("~")
            self.db_path = os.path.join(home_dir, "time_tracker.db")
        else:
            self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add default_email column if it doesn't exist (migration)
        try:
            cursor.execute("ALTER TABLE projects ADD COLUMN default_email TEXT")
        except sqlite3.OperationalError:
            # Column already exists, ignore
            pass
        
        # Add rate column if it doesn't exist (migration)
        try:
            cursor.execute("ALTER TABLE projects ADD COLUMN rate REAL")
        except sqlite3.OperationalError:
            # Column already exists, ignore
            pass
        
        # Add currency column if it doesn't exist (migration)
        try:
            cursor.execute("ALTER TABLE projects ADD COLUMN currency TEXT DEFAULT 'EUR'")
        except sqlite3.OperationalError:
            # Column already exists, ignore
            pass
        
        # Create project_emails table for multiple emails per project
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                is_primary BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        ''')
        
        # Create time_entries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS time_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                description TEXT,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                duration_minutes INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_project(self, name: str, description: str = "", default_email: str = "", rate: float = None, currency: str = "EUR") -> int:
        """Add a new project and return its ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO projects (name, description, default_email, rate, currency) VALUES (?, ?, ?, ?, ?)",
                (name, description, default_email, rate, currency)
            )
            project_id = cursor.lastrowid
            conn.commit()
            return project_id
        except sqlite3.IntegrityError:
            raise ValueError(f"Project '{name}' already exists")
        finally:
            conn.close()
    
    def get_projects(self) -> List[Tuple[int, str, str, str, float, str]]:
        """Get all projects"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, description, default_email, rate, currency FROM projects ORDER BY name")
        projects = cursor.fetchall()
        conn.close()
        return projects
    
    def start_timer(self, project_id: int, description: str = "") -> int:
        """Start a new time entry and return its ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Validate project exists
        cursor.execute("SELECT 1 FROM projects WHERE id = ?", (project_id,))
        if cursor.fetchone() is None:
            conn.close()
            return None

        # Check if there's already a running timer for this project
        cursor.execute(
            "SELECT id FROM time_entries WHERE project_id = ? AND end_time IS NULL",
            (project_id,)
        )
        existing = cursor.fetchone()
        if existing:
            conn.close()
            raise ValueError("Timer is already running for this project")
        
        cursor.execute(
            "INSERT INTO time_entries (project_id, description, start_time) VALUES (?, ?, ?)",
            (project_id, description, datetime.datetime.now())
        )
        entry_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return entry_id
    
    def stop_timer(self, project_id: int) -> Optional[int]:
        """Stop the running timer for a project and return duration in minutes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, start_time FROM time_entries WHERE project_id = ? AND end_time IS NULL",
            (project_id,)
        )
        entry = cursor.fetchone()
        
        if not entry:
            conn.close()
            return None
        
        entry_id, start_time = entry
        end_time = datetime.datetime.now()
        start_dt = datetime.datetime.fromisoformat(start_time)
        duration = int((end_time - start_dt).total_seconds() / 60)
        
        cursor.execute(
            "UPDATE time_entries SET end_time = ?, duration_minutes = ? WHERE id = ?",
            (end_time.isoformat(), duration, entry_id)
        )
        
        conn.commit()
        conn.close()
        return duration
    
    def get_time_entries(self, project_id: Optional[int] = None, 
                        start_date: Optional[datetime.date] = None,
                        end_date: Optional[datetime.date] = None) -> List[Tuple]:
        """Get time entries with optional filters"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT te.id, te.project_id, p.name, te.description, 
                   te.start_time, te.end_time, te.duration_minutes, p.rate, p.currency
            FROM time_entries te
            JOIN projects p ON te.project_id = p.id
            WHERE 1=1
        """
        params = []
        
        if project_id:
            query += " AND te.project_id = ?"
            params.append(project_id)
        
        if start_date:
            query += " AND DATE(te.start_time) >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND DATE(te.start_time) <= ?"
            params.append(end_date.isoformat())
        
        query += " ORDER BY te.start_time DESC"
        
        cursor.execute(query, params)
        entries = cursor.fetchall()
        conn.close()
        return entries
    
    def get_running_timer(self, project_id: int) -> Optional[Tuple]:
        """Get the currently running timer for a project"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, start_time, description FROM time_entries WHERE project_id = ? AND end_time IS NULL",
            (project_id,)
        )
        entry = cursor.fetchone()
        conn.close()
        return entry
    
    def update_entry(self, entry_id: int, description: str = None, 
                    start_time: str = None, end_time: str = None, project_id: int = None) -> bool:
        """Update a time entry"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build update query dynamically based on provided parameters
        updates = []
        params = []
        
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        
        if project_id is not None:
            updates.append("project_id = ?")
            params.append(project_id)
        
        if start_time is not None:
            # Accept datetime objects too
            if not isinstance(start_time, str):
                if isinstance(start_time, datetime.datetime):
                    start_time = start_time.isoformat()
                else:
                    start_time = str(start_time)
            updates.append("start_time = ?")
            params.append(start_time)
        
        if end_time is not None:
            # Accept datetime objects too
            if not isinstance(end_time, str):
                if isinstance(end_time, datetime.datetime):
                    end_time = end_time.isoformat()
                else:
                    end_time = str(end_time)
            updates.append("end_time = ?")
            params.append(end_time)
            
            # Recalculate duration if end_time is provided
            if start_time is not None:
                start_dt = datetime.datetime.fromisoformat(start_time)
                end_dt = datetime.datetime.fromisoformat(end_time)
                duration = int((end_dt - start_dt).total_seconds() / 60)
                updates.append("duration_minutes = ?")
                params.append(duration)
            else:
                # Get current start_time to recalculate duration
                cursor.execute("SELECT start_time FROM time_entries WHERE id = ?", (entry_id,))
                result = cursor.fetchone()
                if result:
                    start_dt = datetime.datetime.fromisoformat(result[0])
                    end_dt = datetime.datetime.fromisoformat(end_time)
                    duration = int((end_dt - start_dt).total_seconds() / 60)
                    updates.append("duration_minutes = ?")
                    params.append(duration)
        
        if not updates:
            conn.close()
            return False
        
        params.append(entry_id)
        query = f"UPDATE time_entries SET {', '.join(updates)} WHERE id = ?"
        
        cursor.execute(query, params)
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated
    
    def get_entry(self, entry_id: int) -> Optional[Tuple]:
        """Get a specific time entry by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT te.id, te.project_id, p.name, te.description, 
                   te.start_time, te.end_time, te.duration_minutes
            FROM time_entries te
            JOIN projects p ON te.project_id = p.id
            WHERE te.id = ?
        """, (entry_id,))
        
        entry = cursor.fetchone()
        conn.close()
        return entry
    
    def delete_entry(self, entry_id: int) -> bool:
        """Delete a time entry"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM time_entries WHERE id = ?", (entry_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
    
    def get_latest_entry_project(self) -> Optional[int]:
        """Get the project ID of the most recent time entry"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT project_id 
            FROM time_entries 
            ORDER BY start_time DESC 
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def add_project_email(self, project_id: int, email: str, is_primary: bool = False) -> int:
        """Add an email to a project"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # If this is primary, unset other primary emails for this project
        if is_primary:
            cursor.execute("UPDATE project_emails SET is_primary = 0 WHERE project_id = ?", (project_id,))
        
        cursor.execute(
            "INSERT INTO project_emails (project_id, email, is_primary) VALUES (?, ?, ?)",
            (project_id, email, is_primary)
        )
        email_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return email_id
    
    def get_project_emails(self, project_id: int) -> List[Tuple[int, str, bool]]:
        """Get all emails for a project"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, email, is_primary FROM project_emails WHERE project_id = ? ORDER BY is_primary DESC, email",
            (project_id,)
        )
        emails = cursor.fetchall()
        conn.close()
        return emails
    
    def delete_project_email(self, email_id: int) -> bool:
        """Delete a project email"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM project_emails WHERE id = ?", (email_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    def remove_project_email(self, project_id: int, email_id: int) -> bool:
        """Backward-compatible wrapper to remove a project email.
        The project_id is accepted for compatibility but not required here.
        """
        return self.delete_project_email(email_id)

    def set_primary_email(self, project_id: int, email_id: int) -> bool:
        """Set a specific email as primary for a project"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE project_emails SET is_primary = 0 WHERE project_id = ?", (project_id,))
            cursor.execute("UPDATE project_emails SET is_primary = 1 WHERE id = ? AND project_id = ?", (email_id, project_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def update_project(self, project_id: int, name: str = None, description: str = None, rate: float = None, currency: str = None) -> bool:
        """Update a project"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        
        if rate is not None:
            updates.append("rate = ?")
            params.append(rate)
        
        if currency is not None:
            updates.append("currency = ?")
            params.append(currency)
        
        if not updates:
            conn.close()
            return False
        
        params.append(project_id)
        query = f"UPDATE projects SET {', '.join(updates)} WHERE id = ?"
        
        cursor.execute(query, params)
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated
