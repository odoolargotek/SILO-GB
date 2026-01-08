# -*- coding: utf-8 -*-
# License LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import api, fields, models, _
import io
import base64
from datetime import datetime

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    openpyxl = None


class GBBrigadeGeneralReport(models.Model):
    """Model to generate comprehensive Brigade General Report in Excel format"""
    _name = "gb.brigade.general.report"
    _description = "Brigade General Report - Excel Export"

    brigade_id = fields.Many2one(
        "gb.brigade",
        string="Brigade",
        required=True,
        ondelete="cascade",
    )

    report_date = fields.Datetime(
        string="Report Date",
        default=lambda self: fields.Datetime.now(),
    )

    excel_file = fields.Binary(
        string="Excel File",
        readonly=True,
    )

    excel_filename = fields.Char(
        string="Filename",
        readonly=True,
    )

    def generate_excel_report(self):
        """Generate the Excel report with all brigade information"""
        if not openpyxl:
            raise ValueError(_("openpyxl library is required. Please install it: pip install openpyxl"))

        self.ensure_one()
        brigade = self.brigade_id

        # Create workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "General Ficha"

        # Define styles
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        section_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        section_font = Font(bold=True, size=10)
        label_font = Font(bold=True, size=10)
        border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin")
        )
        center_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        left_alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)

        # Set column widths
        ws.column_dimensions["A"].width = 25
        ws.column_dimensions["B"].width = 40

        current_row = 1

        # ===== TITLE =====
        ws[f"A{current_row}"].value = "BRIGADE GENERAL REPORT - FICHA GENERAL"
        ws[f"A{current_row}"].font = Font(bold=True, size=12)
        ws.merge_cells(f"A{current_row}:B{current_row}")
        current_row += 2

        # ===== SECTION 1: GENERALIDADES =====
        ws[f"A{current_row}"].value = "GENERALIDADES"
        ws[f"A{current_row}"].fill = section_fill
        ws[f"A{current_row}"].font = section_font
        ws.merge_cells(f"A{current_row}:B{current_row}")
        current_row += 1

        # Add data rows
        report_data = [
            ("Brigade Code", brigade.external_brigade_code or brigade.brigade_code),
            ("Chapter Name", brigade.name),
            ("Arrival Date", brigade.arrival_date.strftime("%Y-%m-%d") if brigade.arrival_date else ""),
            ("Departure Date", brigade.departure_date.strftime("%Y-%m-%d") if brigade.departure_date else ""),
            ("Official Program", dict(brigade._fields['brigade_program'].selection).get(brigade.brigade_program, "")),
            ("Brigade Type", dict(brigade._fields['brigade_type'].selection).get(brigade.brigade_type, "")),
        ]

        for label, value in report_data:
            ws[f"A{current_row}"].value = label
            ws[f"A{current_row}"].font = label_font
            ws[f"B{current_row}"].value = value
            current_row += 1

        current_row += 1

        # ===== SECTION 2: COORDINATORS =====
        ws[f"A{current_row}"].value = "STAFF CONTACTS"
        ws[f"A{current_row}"].fill = section_fill
        ws[f"A{current_row}"].font = section_font
        ws.merge_cells(f"A{current_row}:B{current_row}")
        current_row += 1

        # Lead Coordinator
        ws[f"A{current_row}"].value = "Lead Coordinator"
        ws[f"A{current_row}"].font = label_font
        ws[f"B{current_row}"].value = brigade.coordinator_id.name if brigade.coordinator_id else ""
        current_row += 1
        ws[f"A{current_row}"].value = "  WhatsApp Number"
        ws[f"B{current_row}"].value = brigade.coordinator_id.mobile if brigade.coordinator_id else ""
        current_row += 1

        # Program Advisor
        ws[f"A{current_row}"].value = "Program Advisor"
        ws[f"A{current_row}"].font = label_font
        ws[f"B{current_row}"].value = brigade.program_associate_id.name if brigade.program_associate_id else ""
        current_row += 1
        ws[f"A{current_row}"].value = "  WhatsApp Number"
        ws[f"B{current_row}"].value = brigade.program_associate_id.mobile if brigade.program_associate_id else ""
        current_row += 1

        # Compound Supervisor
        ws[f"A{current_row}"].value = "Compound Supervisor"
        ws[f"A{current_row}"].font = label_font
        ws[f"B{current_row}"].value = brigade.compound_manager_id.name if brigade.compound_manager_id else ""
        current_row += 1
        ws[f"A{current_row}"].value = "  WhatsApp Number"
        ws[f"B{current_row}"].value = brigade.compound_manager_id.mobile if brigade.compound_manager_id else ""
        current_row += 1

        current_row += 1

        # ===== SECTION 3: COMPOUND TIMES =====
        ws[f"A{current_row}"].value = "COMPOUND TIMING"
        ws[f"A{current_row}"].fill = section_fill
        ws[f"A{current_row}"].font = section_font
        ws.merge_cells(f"A{current_row}:B{current_row}")
        current_row += 1

        ws[f"A{current_row}"].value = "Arrival Time to Compound"
        ws[f"A{current_row}"].font = label_font
        arrival_time = brigade.arrival_time_compound.strftime("%Y-%m-%d %H:%M") if brigade.arrival_time_compound else ""
        ws[f"B{current_row}"].value = arrival_time
        current_row += 1

        ws[f"A{current_row}"].value = "Departure Time from Compound"
        ws[f"A{current_row}"].font = label_font
        departure_time = brigade.departure_time_compound.strftime("%Y-%m-%d %H:%M") if brigade.departure_time_compound else ""
        ws[f"B{current_row}"].value = departure_time
        current_row += 1

        current_row += 1

        # ===== SECTION 4: ADDITIONAL INFO =====
        if brigade.extra_info:
            ws[f"A{current_row}"].value = "ADDITIONAL INFORMATION"
            ws[f"A{current_row}"].fill = section_fill
            ws[f"A{current_row}"].font = section_font
            ws.merge_cells(f"A{current_row}:B{current_row}")
            current_row += 1
            ws[f"A{current_row}"].value = brigade.extra_info
            ws[f"A{current_row}"].alignment = left_alignment
            ws.merge_cells(f"A{current_row}:B{current_row}")
            current_row += 2

        # ===== PROGRAMS SHEET =====
        if brigade.program_line_ids:
            ws_programs = wb.create_sheet("Programs")
            ws_programs.column_dimensions["A"].width = 20
            ws_programs.column_dimensions["B"].width = 20
            ws_programs.column_dimensions["C"].width = 15
            ws_programs.column_dimensions["D"].width = 15
            ws_programs.column_dimensions["E"].width = 30

            prog_row = 1
            # Headers
            headers = ["Community", "Program", "Start Date", "End Date", "Coordinator / Notes"]
            for idx, header in enumerate(headers, 1):
                cell = ws_programs.cell(row=prog_row, column=idx)
                cell.value = header
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_alignment
                cell.border = border

            prog_row += 1
            for program_line in brigade.program_line_ids:
                ws_programs.cell(row=prog_row, column=1).value = program_line.community_id.name or program_line.location or ""
                ws_programs.cell(row=prog_row, column=2).value = program_line.program_id.name if program_line.program_id else ""
                ws_programs.cell(row=prog_row, column=3).value = program_line.start_date.strftime("%Y-%m-%d") if program_line.start_date else ""
                ws_programs.cell(row=prog_row, column=4).value = program_line.end_date.strftime("%Y-%m-%d") if program_line.end_date else ""
                ws_programs.cell(row=prog_row, column=5).value = f"{program_line.coordinator_id.name if program_line.coordinator_id else ''} - {program_line.notes or ''}"
                prog_row += 1

        # ===== ARRIVALS SHEET =====
        if brigade.arrival_ids:
            ws_arrivals = wb.create_sheet("Arrivals")
            ws_arrivals.column_dimensions["A"].width = 15
            ws_arrivals.column_dimensions["B"].width = 12
            ws_arrivals.column_dimensions["C"].width = 18
            ws_arrivals.column_dimensions["D"].width = 20
            ws_arrivals.column_dimensions["E"].width = 30
            ws_arrivals.column_dimensions["F"].width = 25

            arr_row = 1
            headers = ["Title", "Flight #", "Arrival Time", "Arrival Hotel", "# Pax", "Notes"]
            for idx, header in enumerate(headers, 1):
                cell = ws_arrivals.cell(row=arr_row, column=idx)
                cell.value = header
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_alignment
                cell.border = border

            arr_row += 1
            for arrival in brigade.arrival_ids:
                ws_arrivals.cell(row=arr_row, column=1).value = arrival.title
                ws_arrivals.cell(row=arr_row, column=2).value = arrival.flight_number or ""
                arr_time = arrival.date_time_arrival.strftime("%Y-%m-%d %H:%M") if arrival.date_time_arrival else ""
                ws_arrivals.cell(row=arr_row, column=3).value = arr_time
                ws_arrivals.cell(row=arr_row, column=4).value = arrival.arrival_hotel_id.partner_id.name if arrival.arrival_hotel_id else ""
                ws_arrivals.cell(row=arr_row, column=5).value = len(arrival.passenger_ids)
                ws_arrivals.cell(row=arr_row, column=6).value = arrival.extra_charge or ""
                arr_row += 1

        # ===== DEPARTURES SHEET =====
        if brigade.departure_ids:
            ws_departures = wb.create_sheet("Departures")
            ws_departures.column_dimensions["A"].width = 15
            ws_departures.column_dimensions["B"].width = 12
            ws_departures.column_dimensions["C"].width = 18
            ws_departures.column_dimensions["D"].width = 20
            ws_departures.column_dimensions["E"].width = 30
            ws_departures.column_dimensions["F"].width = 25

            dep_row = 1
            headers = ["Title", "Flight #", "Departure Time", "Departure Hotel", "# Pax", "Notes"]
            for idx, header in enumerate(headers, 1):
                cell = ws_departures.cell(row=dep_row, column=idx)
                cell.value = header
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_alignment
                cell.border = border

            dep_row += 1
            for departure in brigade.departure_ids:
                ws_departures.cell(row=dep_row, column=1).value = departure.title
                ws_departures.cell(row=dep_row, column=2).value = departure.flight_number or ""
                dep_time = departure.date_time_departure.strftime("%Y-%m-%d %H:%M") if departure.date_time_departure else ""
                ws_departures.cell(row=dep_row, column=3).value = dep_time
                ws_departures.cell(row=dep_row, column=4).value = departure.departure_hotel_id.partner_id.name if departure.departure_hotel_id else ""
                ws_departures.cell(row=dep_row, column=5).value = len(departure.passenger_ids)
                ws_departures.cell(row=dep_row, column=6).value = departure.extra_charge or ""
                dep_row += 1

        # ===== STAFF SHEET =====
        if brigade.staff_ids:
            ws_staff = wb.create_sheet("Staff")
            ws_staff.column_dimensions["A"].width = 20
            ws_staff.column_dimensions["B"].width = 15
            ws_staff.column_dimensions["C"].width = 12
            ws_staff.column_dimensions["D"].width = 20
            ws_staff.column_dimensions["E"].width = 15
            ws_staff.column_dimensions["F"].width = 15
            ws_staff.column_dimensions["G"].width = 20
            ws_staff.column_dimensions["H"].width = 20
            ws_staff.column_dimensions["I"].width = 20
            ws_staff.column_dimensions["J"].width = 25

            staff_row = 1
            headers = ["Name", "WhatsApp", "Gender", "Brigade Role", "Start Date", "End Date", "Diet", "Allergy", "Professional Reg.", "Internal Notes"]
            for idx, header in enumerate(headers, 1):
                cell = ws_staff.cell(row=staff_row, column=idx)
                cell.value = header
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_alignment
                cell.border = border

            staff_row += 1
            for staff in brigade.staff_ids:
                ws_staff.cell(row=staff_row, column=1).value = staff.person_id.name if staff.person_id else ""
                ws_staff.cell(row=staff_row, column=2).value = staff.person_id.mobile if staff.person_id else ""
                ws_staff.cell(row=staff_row, column=3).value = dict(staff._fields['gender'].selection).get(staff.gender, "") if staff.gender else ""
                ws_staff.cell(row=staff_row, column=4).value = dict(staff._fields['staff_role'].selection).get(staff.staff_role, "") if staff.staff_role else ""
                start = staff.start_datetime.strftime("%Y-%m-%d") if staff.start_datetime else ""
                ws_staff.cell(row=staff_row, column=5).value = start
                end = staff.end_datetime.strftime("%Y-%m-%d") if staff.end_datetime else ""
                ws_staff.cell(row=staff_row, column=6).value = end
                ws_staff.cell(row=staff_row, column=7).value = staff.diet or ""
                ws_staff.cell(row=staff_row, column=8).value = staff.allergy or ""
                ws_staff.cell(row=staff_row, column=9).value = staff.professional_registration or ""
                ws_staff.cell(row=staff_row, column=10).value = staff.internal_note or ""
                staff_row += 1

        # ===== HOTELS SHEET =====
        if brigade.hotel_booking_ids:
            ws_hotels = wb.create_sheet("Hotels")
            ws_hotels.column_dimensions["A"].width = 20
            ws_hotels.column_dimensions["B"].width = 15
            ws_hotels.column_dimensions["C"].width = 15
            ws_hotels.column_dimensions["D"].width = 12
            ws_hotels.column_dimensions["E"].width = 25

            hotel_row = 1
            headers = ["Hotel", "Check-In", "Check-Out", "Nights", "Notes"]
            for idx, header in enumerate(headers, 1):
                cell = ws_hotels.cell(row=hotel_row, column=idx)
                cell.value = header
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_alignment
                cell.border = border

            hotel_row += 1
            for hotel_booking in brigade.hotel_booking_ids:
                ws_hotels.cell(row=hotel_row, column=1).value = hotel_booking.partner_id.name if hotel_booking.partner_id else ""
                ws_hotels.cell(row=hotel_row, column=2).value = hotel_booking.check_in_date.strftime("%Y-%m-%d") if hotel_booking.check_in_date else ""
                ws_hotels.cell(row=hotel_row, column=3).value = hotel_booking.check_out_date.strftime("%Y-%m-%d") if hotel_booking.check_out_date else ""
                ws_hotels.cell(row=hotel_row, column=4).value = hotel_booking.stay_nights
                ws_hotels.cell(row=hotel_row, column=5).value = hotel_booking.note or ""
                hotel_row += 1

        # Save to binary
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        excel_data = base64.b64encode(output.read())

        self.excel_file = excel_data
        self.excel_filename = f"Brigade_Report_{brigade.brigade_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return {
            "type": "ir.actions.act_window_close",
        }
