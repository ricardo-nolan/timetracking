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
            
            # Check if any project has a rate set
            has_rates = any(entry[7] is not None for entry in time_entries)
            if has_rates:
                table_data[0].extend(['Rate', 'Amount'])
            
            total_duration = 0
            total_amount = 0.0
            for entry in time_entries:
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
                
                row_data = [
                    date_str,
                    project_name,
                    description or "",
                    start_time_str,
                    end_time_str,
                    duration_str
                ]
                
                if has_rates:
                    row_data.extend([rate_str, amount_str])
                
                table_data.append(row_data)
            
            # Create table with dynamic column widths
            if has_rates:
                col_widths = [1*inch, 1.2*inch, 2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch]
            else:
                col_widths = [1*inch, 1.2*inch, 2*inch, 0.8*inch, 0.8*inch, 0.8*inch]
            
            table = Table(table_data, colWidths=col_widths)
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
            
            # Total amount if rates are present
            if has_rates and total_amount > 0:
                # Use the currency from the first entry with a rate
                first_currency = None
                for entry in time_entries:
                    if entry[7] is not None and entry[7] > 0:  # rate > 0
                        first_currency = entry[8]  # currency
                        break
                currency_symbol = "€" if first_currency == "EUR" else "$"
                story.append(Paragraph(f"<b>Total Amount: {currency_symbol}{total_amount:.2f}</b>", self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        return output_path
