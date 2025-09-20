import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, date
from typing import List, Tuple, Optional
import json
import os
from .password_utils import password_encryption

class EmailExporter:
    def __init__(self, smtp_server: str = "smtp.gmail.com", smtp_port: int = 587):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = None
        self.sender_password = None
        # Use user's home directory for config file
        home_dir = os.path.expanduser("~")
        self.config_file = os.path.join(home_dir, "email_config.json")
        self.load_config()
    
    def send_time_report(self, time_entries: List[Tuple],
                        sender_email: str,
                        sender_password: str,
                        recipient_email: str,
                        project_name: Optional[str] = None,
                        start_date: Optional[date] = None,
                        end_date: Optional[date] = None,
                        pdf_path: Optional[str] = None):
        """Send time report via email"""
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        
        # Subject
        subject = "Time Tracking Report"
        if project_name:
            subject += f" - {project_name}"
        msg['Subject'] = subject
        
        # Create email body
        body = self._create_email_body(time_entries, project_name, start_date, end_date)
        msg.attach(MIMEText(body, 'html'))
        
        # Attach PDF if provided
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(pdf_path)}'
            )
            msg.attach(part)
        
        # Send email
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, recipient_email, text)
            server.quit()
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def load_config(self):
        """Load email configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.smtp_server = config.get('smtp_server', 'smtp.gmail.com')
                    self.smtp_port = config.get('smtp_port', 587)
                    self.sender_email = config.get('sender_email')
                    
                    # Decrypt password if it's encrypted
                    encrypted_password = config.get('sender_password')
                    if encrypted_password:
                        self.sender_password = password_encryption.decrypt_password(encrypted_password)
                    else:
                        self.sender_password = None
        except Exception:
            pass  # Use defaults if config file is corrupted
    
    def save_config(self):
        """Save email configuration to file"""
        try:
            # Encrypt password before saving
            encrypted_password = None
            if self.sender_password:
                encrypted_password = password_encryption.encrypt_password(self.sender_password)
            
            config = {
                'smtp_server': self.smtp_server,
                'smtp_port': self.smtp_port,
                'sender_email': self.sender_email,
                'sender_password': encrypted_password
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception:
            pass  # Silently fail if can't save config
    
    def _create_email_body(self, time_entries: List[Tuple],
                          project_name: Optional[str] = None,
                          start_date: Optional[date] = None,
                          end_date: Optional[date] = None) -> str:
        """Create HTML email body"""
        
        # Header
        html = f"""
        <html>
        <body>
        <h2>Time Tracking Report</h2>
        """
        
        if project_name:
            html += f"<h3>Project: {project_name}</h3>"
        
        # Date range
        if start_date and end_date:
            date_range = f"From {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}"
        elif start_date:
            date_range = f"From {start_date.strftime('%B %d, %Y')}"
        elif end_date:
            date_range = f"Until {end_date.strftime('%B %d, %Y')}"
        else:
            date_range = f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        
        html += f"<p><strong>{date_range}</strong></p>"
        
        if not time_entries:
            html += "<p>No time entries found for the selected criteria.</p>"
        else:
            # Check if any project has a rate set
            has_rates = any(entry[7] is not None for entry in time_entries)
            
            # Create table
            html += """
            <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f2f2f2;">
                <th>Date</th>
                <th>Project</th>
                <th>Description</th>
                <th>Start Time</th>
                <th>End Time</th>
                <th>Duration</th>
            """
            
            if has_rates:
                html += """
                <th>Rate</th>
                <th>Amount</th>
                """
            
            html += """
            </tr>
            """
            
            total_duration = 0
            total_amount = 0.0
            for entry in time_entries:
                entry_id, project_id, proj_name, description, start_time, end_time, duration, rate, currency = entry
                
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
                    # Calculate precise duration from timestamps
                    start_dt = datetime.fromisoformat(start_time)
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
                        
                        # Add to total in minutes for calculation
                        total_duration += total_seconds // 60
                    else:
                        # Fallback to stored duration
                        hours = duration // 60
                        minutes = duration % 60
                        if hours > 0:
                            duration_str = f"{hours}h {minutes}m"
                        else:
                            duration_str = f"{minutes}m"
                        total_duration += duration
                else:
                    duration_str = "Running"
                
                # Calculate rate and amount
                rate_str = ""
                amount_str = ""
                if has_rates:
                    if rate is not None and rate > 0:
                        currency_symbol = "€" if currency == "EUR" else "$"
                        rate_str = f"{currency_symbol}{rate:.2f}/h"
                        if duration is not None and duration > 0:
                            # Calculate amount based on duration in hours
                            hours = duration / 60.0  # Convert minutes to hours
                            amount = hours * rate
                            total_amount += amount
                            amount_str = f"{currency_symbol}{amount:.2f}"
                        else:
                            amount_str = f"{currency_symbol}0.00"
                    else:
                        rate_str = "N/A"
                        amount_str = "N/A"
                
                html += f"""
                <tr>
                    <td>{date_str}</td>
                    <td>{proj_name}</td>
                    <td>{description or ""}</td>
                    <td>{start_time_str}</td>
                    <td>{end_time_str}</td>
                    <td>{duration_str}</td>
                """
                
                if has_rates:
                    html += f"""
                    <td>{rate_str}</td>
                    <td>{amount_str}</td>
                    """
                
                html += """
                </tr>
                """
            
            html += "</table>"
            
            # Total duration
            total_hours = total_duration // 60
            total_minutes = total_duration % 60
            if total_hours > 0:
                total_str = f"{total_hours} hours and {total_minutes} minutes"
            else:
                total_str = f"{total_minutes} minutes"
            
            html += f"<p><strong>Total Time: {total_str}</strong></p>"
            
            # Total amount if rates are present
            if has_rates and total_amount > 0:
                # Use the currency from the first entry with a rate
                first_currency = None
                for entry in time_entries:
                    if entry[7] is not None and entry[7] > 0:  # rate > 0
                        first_currency = entry[8]  # currency
                        break
                currency_symbol = "€" if first_currency == "EUR" else "$"
                html += f"<p><strong>Total Amount: {currency_symbol}{total_amount:.2f}</strong></p>"
        
        html += """
        </body>
        </html>
        """
        
        return html
