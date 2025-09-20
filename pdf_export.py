from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime, date
from typing import List, Tuple, Optional
import os

class PDFExporter:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            alignment=1  # Center alignment
        ))
    
    def export_time_report(self, time_entries: List[Tuple], 
                          output_path: str,
                          project_name: Optional[str] = None,
                          start_date: Optional[date] = None,
                          end_date: Optional[date] = None):
        """Export time entries to PDF"""
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []
        
        # Title
        title = "Time Tracking Report"
        if project_name:
            title += f" - {project_name}"
        story.append(Paragraph(title, self.styles['CustomTitle']))
        
        # Date range
        if start_date and end_date:
            date_range = f"From {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}"
        elif start_date:
            date_range = f"From {start_date.strftime('%B %d, %Y')}"
        elif end_date:
            date_range = f"Until {end_date.strftime('%B %d, %Y')}"
        else:
            date_range = f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        
        story.append(Paragraph(date_range, self.styles['CustomSubtitle']))
        story.append(Spacer(1, 20))
        
        if not time_entries:
            story.append(Paragraph("No time entries found for the selected criteria.", self.styles['Normal']))
        else:
            # Create table data
            table_data = [['Date', 'Project', 'Description', 'Start Time', 'End Time', 'Duration']]
            
            total_duration = 0
            for entry in time_entries:
                entry_id, project_id, project_name, description, start_time, end_time, duration = entry
                
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
                
                table_data.append([
                    date_str,
                    project_name,
                    description or "",
                    start_time_str,
                    end_time_str,
                    duration_str
                ])
            
            # Create table
            table = Table(table_data, colWidths=[1*inch, 1.2*inch, 2*inch, 0.8*inch, 0.8*inch, 0.8*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            
            story.append(table)
            story.append(Spacer(1, 20))
            
            # Total duration
            total_hours = total_duration // 60
            total_minutes = total_duration % 60
            if total_hours > 0:
                total_str = f"{total_hours} hours and {total_minutes} minutes"
            else:
                total_str = f"{total_minutes} minutes"
            
            story.append(Paragraph(f"<b>Total Time: {total_str}</b>", self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        return output_path
