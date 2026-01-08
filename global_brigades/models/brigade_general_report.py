# -*- coding: utf-8 -*-
# License LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html)

import base64
from io import BytesIO
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    raise UserError(_("Please install openpyxl: pip install openpyxl"))


class GBBrigadeGeneralReport(models.Model):
    _name = 'gb.brigade.general.report'
    _description = 'Brigade General Report'
    _order = 'report_date desc, id desc'
    
    brigade_id = fields.Many2one(
        'gb.brigade',
        string='Brigade',
        required=True,
        ondelete='cascade',
    )
    
    report_date = fields.Datetime(
        string='Report Date',
        default=fields.Datetime.now,
        readonly=True,
    )
    
    excel_file = fields.Binary(
        string='Excel File',
        readonly=True,
    )
    
    excel_filename = fields.Char(
        string='Filename',
        readonly=True,
    )
    
    def generate_excel_report(self):
        """Generate comprehensive Excel report for the brigade."""
        self.ensure_one()
        
        brigade = self.brigade_id
        wb = Workbook()
        
        # Remove default sheet
        if 'Sheet' in wb.sheetnames:
            wb.remove(wb['Sheet'])
        
        # Create sheets
        self._create_brigade_info_sheet(wb, brigade)
        self._create_roster_sheet(wb, brigade)
        self._create_staff_sheet(wb, brigade)
        self._create_arrivals_sheet(wb, brigade)
        self._create_departures_sheet(wb, brigade)
        self._create_hotels_sheet(wb, brigade)
        self._create_transport_sheet(wb, brigade)
        self._create_activities_sheet(wb, brigade)
        self._create_programs_sheet(wb, brigade)
        self._create_statistics_sheet(wb, brigade)
        
        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Generate filename
        filename = f"Brigade_Report_{brigade.brigade_code or brigade.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # Update record
        self.write({
            'excel_file': base64.b64encode(output.read()),
            'excel_filename': filename,
        })
        
        return True
    
    def _create_brigade_info_sheet(self, wb, brigade):
        """Create Brigade Information sheet."""
        ws = wb.create_sheet('Brigade Info')
        
        # Header style
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        
        # Title
        ws['A1'] = 'BRIGADE GENERAL INFORMATION'
        ws['A1'].font = Font(bold=True, size=14)
        ws.merge_cells('A1:B1')
        
        row = 3
        data = [
            ('Brigade Code', brigade.brigade_code or ''),
            ('Chapter Name', brigade.name or ''),
            ('External Brigade Code', brigade.external_brigade_code or ''),
            ('Status', dict(brigade._fields['state'].selection).get(brigade.state, '')),
            ('Brigade Type', dict(brigade._fields['brigade_type'].selection).get(brigade.brigade_type, '')),
            ('Program', dict(brigade._fields['brigade_program'].selection).get(brigade.brigade_program, '') if brigade.brigade_program else ''),
            ('Tier', dict(brigade._fields['brigade_tier'].selection).get(brigade.brigade_tier, '') if brigade.brigade_tier else ''),
            ('Restrictions', dict(brigade._fields['brigade_restriction'].selection).get(brigade.brigade_restriction, '') if brigade.brigade_restriction else ''),
            ('Arrival Date', brigade.arrival_date.strftime('%Y-%m-%d') if brigade.arrival_date else ''),
            ('Departure Date', brigade.departure_date.strftime('%Y-%m-%d') if brigade.departure_date else ''),
            ('Arrival to Compound', brigade.arrival_time_compound.strftime('%Y-%m-%d %H:%M') if brigade.arrival_time_compound else ''),
            ('Departure from Compound', brigade.departure_time_compound.strftime('%Y-%m-%d %H:%M') if brigade.departure_time_compound else ''),
            ('Lead Coordinator', brigade.coordinator_id.name if brigade.coordinator_id else ''),
            ('Program Advisor', brigade.program_associate_id.name if brigade.program_associate_id else ''),
            ('Compound Supervisor', brigade.compound_manager_id.name if brigade.compound_manager_id else ''),
            ('Business Client', brigade.business_client_id.name if brigade.business_client_id else ''),
            ('Itinerary Link', brigade.lt_itinerary_link or ''),
            ('Total Volunteers', str(brigade.volunteer_count)),
            ('Total Programs', str(brigade.program_count)),
            ('Total Activities', str(brigade.activity_count)),
            ('Total Transports', str(brigade.transport_count)),
            ('Additional Info', brigade.extra_info or ''),
        ]
        
        for label, value in data:
            ws[f'A{row}'] = label
            ws[f'A{row}'].font = Font(bold=True)
            ws[f'A{row}'].fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
            ws[f'B{row}'] = value
            row += 1
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 50
    
    def _create_roster_sheet(self, wb, brigade):
        """Create Roster sheet with all volunteers."""
        ws = wb.create_sheet('Roster')
        
        headers = [
            'Name', 'Email', 'Phone', 'Gender', 'Birthdate', 'Spanish Speaker',
            'Passport No', 'Passport Expiry', 'Citizenship', 'T-Shirt Size',
            'Brigade Role', 'S.A.', 'Diet', 'Medical Condition', 'Medications',
            'Allergies', 'Emergency Contact', 'Emergency Email'
        ]
        
        self._write_sheet_headers(ws, headers)
        
        row = 2
        for roster in brigade.roster_ids:
            ws[f'A{row}'] = roster.partner_id.name or ''
            ws[f'B{row}'] = roster.email or ''
            ws[f'C{row}'] = roster.phone_display or ''
            ws[f'D{row}'] = dict(roster.partner_id._fields['gb_gender'].selection).get(roster.gender, '') if roster.gender else ''
            ws[f'E{row}'] = roster.birthdate.strftime('%Y-%m-%d') if roster.birthdate else ''
            ws[f'F{row}'] = 'Yes' if roster.spanish_speaker else 'No'
            ws[f'G{row}'] = roster.passport_no or ''
            ws[f'H{row}'] = roster.passport_expiry.strftime('%Y-%m-%d') if roster.passport_expiry else ''
            ws[f'I{row}'] = roster.citizenship or ''
            ws[f'J{row}'] = dict(roster.partner_id._fields['gb_tshirt_size'].selection).get(roster.tshirt_size, '') if roster.tshirt_size else ''
            ws[f'K{row}'] = roster.brigade_role or ''
            ws[f'L{row}'] = 'Yes' if roster.sa else 'No'
            ws[f'M{row}'] = roster.diet or ''
            ws[f'N{row}'] = roster.medical_condition or ''
            ws[f'O{row}'] = roster.medications or ''
            ws[f'P{row}'] = roster.allergy or ''
            ws[f'Q{row}'] = roster.emergency_contact_id.name if roster.emergency_contact_id else ''
            ws[f'R{row}'] = roster.emergency_contact_email or ''
            row += 1
        
        self._auto_adjust_columns(ws)
    
    def _create_staff_sheet(self, wb, brigade):
        """Create Staff sheet."""
        ws = wb.create_sheet('Staff')
        
        headers = [
            'Name', 'Role', 'Gender', 'Diet', 'Allergies',
            'Professional Registration', 'Start DateTime', 'End DateTime',
            'Notes'
        ]
        
        self._write_sheet_headers(ws, headers)
        
        row = 2
        for staff in brigade.staff_ids:
            ws[f'A{row}'] = staff.person_id.name or ''
            ws[f'B{row}'] = dict(staff._fields['staff_role'].selection).get(staff.staff_role, '') if staff.staff_role else ''
            ws[f'C{row}'] = dict(staff.person_id._fields['gb_gender'].selection).get(staff.gender, '') if staff.gender else ''
            ws[f'D{row}'] = staff.diet or ''
            ws[f'E{row}'] = staff.allergy or ''
            ws[f'F{row}'] = staff.professional_registration or ''
            ws[f'G{row}'] = staff.start_datetime.strftime('%Y-%m-%d %H:%M') if staff.start_datetime else ''
            ws[f'H{row}'] = staff.end_datetime.strftime('%Y-%m-%d %H:%M') if staff.end_datetime else ''
            ws[f'I{row}'] = staff.internal_note or ''
            row += 1
        
        self._auto_adjust_columns(ws)
    
    def _create_arrivals_sheet(self, wb, brigade):
        """Create Arrivals sheet."""
        ws = wb.create_sheet('Arrivals')
        
        headers = [
            'Title', 'Flight Number', 'Arrival DateTime', 'Through SAP',
            'Arrival Hotel', 'Hotel City/Time', '# Pax', 'Passengers',
            'Special Transport', 'Extra Charge'
        ]
        
        self._write_sheet_headers(ws, headers)
        
        row = 2
        for arrival in brigade.arrival_ids:
            ws[f'A{row}'] = arrival.title or ''
            ws[f'B{row}'] = arrival.flight_number or ''
            ws[f'C{row}'] = arrival.date_time_arrival.strftime('%Y-%m-%d %H:%M') if arrival.date_time_arrival else ''
            ws[f'D{row}'] = arrival.flight_through_sap or ''
            ws[f'E{row}'] = arrival.arrival_hotel_id.name if arrival.arrival_hotel_id else ''
            ws[f'F{row}'] = arrival.arrival_hotel_city_time or ''
            ws[f'G{row}'] = arrival.n_pax
            ws[f'H{row}'] = ', '.join(arrival.passenger_ids.mapped('partner_id.name'))
            ws[f'I{row}'] = 'Yes' if arrival.special_transport else 'No'
            ws[f'J{row}'] = arrival.extra_charge or ''
            row += 1
        
        self._auto_adjust_columns(ws)
    
    def _create_departures_sheet(self, wb, brigade):
        """Create Departures sheet."""
        ws = wb.create_sheet('Departures')
        
        headers = [
            'Title', 'Flight Number', 'Departure DateTime', 'Through SAP',
            'Departure Hotel', 'Hotel City', '# Pax', 'Passengers',
            'Special Transport', 'Extra Charge'
        ]
        
        self._write_sheet_headers(ws, headers)
        
        row = 2
        for departure in brigade.departure_ids:
            ws[f'A{row}'] = departure.title or ''
            ws[f'B{row}'] = departure.flight_number or ''
            ws[f'C{row}'] = departure.date_time_departure.strftime('%Y-%m-%d %H:%M') if departure.date_time_departure else ''
            ws[f'D{row}'] = departure.flight_through_sap or ''
            ws[f'E{row}'] = departure.departure_hotel_id.name if departure.departure_hotel_id else ''
            ws[f'F{row}'] = departure.departure_hotel_city or ''
            ws[f'G{row}'] = departure.n_pax
            ws[f'H{row}'] = ', '.join(departure.passenger_ids.mapped('partner_id.name'))
            ws[f'I{row}'] = 'Yes' if departure.special_transport else 'No'
            ws[f'J{row}'] = departure.extra_charge or ''
            row += 1
        
        self._auto_adjust_columns(ws)
    
    def _create_hotels_sheet(self, wb, brigade):
        """Create Hotels sheet."""
        ws = wb.create_sheet('Hotels')
        
        headers = [
            'Hotel', 'Check-in Date', 'Check-out Date', 'Stay Nights',
            '# Rooms', 'Room Distribution', 'Total Guests', 'Notes'
        ]
        
        self._write_sheet_headers(ws, headers)
        
        row = 2
        for booking in brigade.hotel_booking_ids:
            ws[f'A{row}'] = booking.hotel_id.name if booking.hotel_id else ''
            ws[f'B{row}'] = booking.checkin_date.strftime('%Y-%m-%d') if booking.checkin_date else ''
            ws[f'C{row}'] = booking.checkout_date.strftime('%Y-%m-%d') if booking.checkout_date else ''
            ws[f'D{row}'] = int(booking.stay_nights)
            ws[f'E{row}'] = booking.total_rooms
            ws[f'F{row}'] = booking.room_distribution or ''
            ws[f'G{row}'] = booking.total_guests
            ws[f'H{row}'] = booking.notes or ''
            row += 1
        
        self._auto_adjust_columns(ws)
    
    def _create_transport_sheet(self, wb, brigade):
        """Create Transport sheet."""
        ws = wb.create_sheet('Transport')
        
        headers = [
            'Transport Name', 'Type', 'Provider', 'Start Date', 'End Date',
            'Origin', 'Destination', '# Passengers', 'Cost', 'Notes'
        ]
        
        self._write_sheet_headers(ws, headers)
        
        row = 2
        for transport in brigade.transport_ids:
            ws[f'A{row}'] = transport.name or ''
            ws[f'B{row}'] = dict(transport._fields['transport_type'].selection).get(transport.transport_type, '') if transport.transport_type else ''
            ws[f'C{row}'] = transport.provider_id.name if transport.provider_id else ''
            ws[f'D{row}'] = transport.start_datetime.strftime('%Y-%m-%d %H:%M') if transport.start_datetime else ''
            ws[f'E{row}'] = transport.end_datetime.strftime('%Y-%m-%d %H:%M') if transport.end_datetime else ''
            ws[f'F{row}'] = transport.origin or ''
            ws[f'G{row}'] = transport.destination or ''
            ws[f'H{row}'] = transport.passenger_count
            ws[f'I{row}'] = transport.cost or 0.0
            ws[f'J{row}'] = transport.notes or ''
            row += 1
        
        self._auto_adjust_columns(ws)
    
    def _create_activities_sheet(self, wb, brigade):
        """Create Activities/Itinerary sheet."""
        ws = wb.create_sheet('Activities')
        
        headers = [
            'Activity Name', 'Tags', 'Start DateTime', 'End DateTime',
            'Place', 'Responsible', '# Participants', 'Notes'
        ]
        
        self._write_sheet_headers(ws, headers)
        
        row = 2
        for activity in brigade.activity_ids:
            ws[f'A{row}'] = activity.name or ''
            ws[f'B{row}'] = ', '.join(activity.tag_ids.mapped('name'))
            ws[f'C{row}'] = activity.start_datetime.strftime('%Y-%m-%d %H:%M') if activity.start_datetime else ''
            ws[f'D{row}'] = activity.end_datetime.strftime('%Y-%m-%d %H:%M') if activity.end_datetime else ''
            ws[f'E{row}'] = activity.place or ''
            ws[f'F{row}'] = activity.responsible_id.name if activity.responsible_id else ''
            ws[f'G{row}'] = activity.participant_count
            ws[f'H{row}'] = activity.notes or ''
            row += 1
        
        self._auto_adjust_columns(ws)
    
    def _create_programs_sheet(self, wb, brigade):
        """Create Programs sheet."""
        ws = wb.create_sheet('Programs')
        
        headers = [
            'Program', 'Start Date', 'End Date', 'Community',
            'Location', 'Coordinator', 'Notes'
        ]
        
        self._write_sheet_headers(ws, headers)
        
        row = 2
        for program in brigade.program_line_ids:
            ws[f'A{row}'] = program.program_id.name if program.program_id else ''
            ws[f'B{row}'] = program.start_date.strftime('%Y-%m-%d') if program.start_date else ''
            ws[f'C{row}'] = program.end_date.strftime('%Y-%m-%d') if program.end_date else ''
            ws[f'D{row}'] = program.community_id.name if program.community_id else ''
            ws[f'E{row}'] = program.location or ''
            ws[f'F{row}'] = program.coordinator_id.name if program.coordinator_id else ''
            ws[f'G{row}'] = program.notes or ''
            row += 1
        
        self._auto_adjust_columns(ws)
    
    def _create_statistics_sheet(self, wb, brigade):
        """Create Statistics sheet with computed fields."""
        ws = wb.create_sheet('Statistics')
        
        # Title
        ws['A1'] = 'BRIGADE STATISTICS'
        ws['A1'].font = Font(bold=True, size=14)
        ws.merge_cells('A1:B1')
        
        row = 3
        
        # Get computed stats
        stats_data = [
            ('Communities', brigade.community_names or ''),
            ('# Arrivals', str(brigade.arrival_count)),
            ('# Departures', str(brigade.departure_count)),
            ('# Hotel Blocks', str(brigade.hotel_booking_count)),
            ('Total Hotel Nights', str(brigade.total_stay_nights)),
            ('Total Staff', str(brigade.staff_count)),
            ('Medical Staff', str(brigade.medical_staff_count)),
            ('Dental Staff', str(brigade.dental_staff_count)),
            ('Logistics Staff', str(brigade.logistics_staff_count)),
            ('Translators/Interpreters', str(brigade.translator_staff_count)),
        ]
        
        for label, value in stats_data:
            ws[f'A{row}'] = label
            ws[f'A{row}'].font = Font(bold=True)
            ws[f'A{row}'].fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
            ws[f'B{row}'] = value
            row += 1
        
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 50
    
    def _write_sheet_headers(self, ws, headers):
        """Write headers to worksheet with styling."""
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
    
    def _auto_adjust_columns(self, ws):
        """Auto-adjust column widths based on content."""
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            
            for cell in column:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 50)  # Max width of 50
            ws.column_dimensions[column_letter].width = adjusted_width
