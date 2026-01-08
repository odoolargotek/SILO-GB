# -*- coding: utf-8 -*-
# License LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import base64
import io
from datetime import datetime

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    raise ImportError("Please install openpyxl: pip install openpyxl")


class GBBrigade(models.Model):
    _name = "gb.brigade"
    _description = "Global Brigades - Brigade / Chapter"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_date desc, name"

    # ... (resto del código existente del modelo gb.brigade)
    # Solo agregamos el nuevo método al final:

    def action_export_rooming_list(self):
        """
        Generate and download Rooming List Excel for this brigade.
        """
        self.ensure_one()

        # Get all rooming assignments for this brigade
        rooming_recs = self.env["gb.brigade.rooming"].search(
            [("brigade_id", "=", self.id)],
            order="date_night, hotel_offer_id"
        )

        if not rooming_recs:
            raise UserError(_("No rooming assignments found for this brigade. "
                            "Please create rooming records in the 'Hoteles / Rooming' tab first."))

        # Build Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "Rooming List"

        # === STYLES ===
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        border_thin = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin")
        )

        # === TITLE ===
        ws.merge_cells("A1:I1")
        title_cell = ws["A1"]
        title_cell.value = f"ROOMING LIST - {self.name}"
        title_cell.font = Font(bold=True, size=14)
        title_cell.alignment = Alignment(horizontal="center", vertical="center")

        # === HEADERS (Row 3) ===
        headers = [
            "Night/Date",
            "Hotel",
            "City",
            "Room Number",
            "Room Type",
            "Bed Setup",
            "Occupant Name",
            "Role",
            "Notes"
        ]
        for col_num, header_text in enumerate(headers, start=1):
            cell = ws.cell(row=3, column=col_num)
            cell.value = header_text
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = border_thin

        # === DATA ROWS ===
        row_idx = 4
        for rooming in rooming_recs:
            hotel_name = rooming.partner_id.name if rooming.partner_id else ""
            city = rooming.city or ""
            night_date = rooming.date_night.strftime("%Y-%m-%d") if rooming.date_night else ""
            rooming_notes = rooming.note or ""

            if not rooming.line_ids:
                # No room lines defined, show at least the hotel/date
                for col_num in range(1, len(headers) + 1):
                    cell = ws.cell(row=row_idx, column=col_num)
                    cell.border = border_thin
                    cell.alignment = Alignment(vertical="center")

                ws.cell(row=row_idx, column=1).value = night_date
                ws.cell(row=row_idx, column=2).value = hotel_name
                ws.cell(row=row_idx, column=3).value = city
                ws.cell(row=row_idx, column=9).value = rooming_notes
                row_idx += 1
                continue

            for line in rooming.line_ids:
                room_number = line.room_number or ""
                room_type_val = dict(line.hotel_room_id._fields["room_type"].selection).get(
                    line.room_type, line.room_type or ""
                ) if line.room_type else ""
                bed_setup = line.bed_setup or ""
                line_notes = line.internal_notes or ""

                if not line.occupant_ids:
                    # Empty room line
                    for col_num in range(1, len(headers) + 1):
                        cell = ws.cell(row=row_idx, column=col_num)
                        cell.border = border_thin
                        cell.alignment = Alignment(vertical="center")

                    ws.cell(row=row_idx, column=1).value = night_date
                    ws.cell(row=row_idx, column=2).value = hotel_name
                    ws.cell(row=row_idx, column=3).value = city
                    ws.cell(row=row_idx, column=4).value = room_number
                    ws.cell(row=row_idx, column=5).value = room_type_val
                    ws.cell(row=row_idx, column=6).value = bed_setup
                    ws.cell(row=row_idx, column=9).value = f"{rooming_notes} {line_notes}".strip()
                    row_idx += 1
                    continue

                # One row per occupant
                for occupant in line.occupant_ids:
                    occupant_name = occupant.partner_id.name if occupant.partner_id else ""
                    role = occupant.role or ""

                    for col_num in range(1, len(headers) + 1):
                        cell = ws.cell(row=row_idx, column=col_num)
                        cell.border = border_thin
                        cell.alignment = Alignment(vertical="center")

                    ws.cell(row=row_idx, column=1).value = night_date
                    ws.cell(row=row_idx, column=2).value = hotel_name
                    ws.cell(row=row_idx, column=3).value = city
                    ws.cell(row=row_idx, column=4).value = room_number
                    ws.cell(row=row_idx, column=5).value = room_type_val
                    ws.cell(row=row_idx, column=6).value = bed_setup
                    ws.cell(row=row_idx, column=7).value = occupant_name
                    ws.cell(row=row_idx, column=8).value = role
                    ws.cell(row=row_idx, column=9).value = f"{rooming_notes} {line_notes}".strip()
                    row_idx += 1

        # === COLUMN WIDTHS ===
        ws.column_dimensions["A"].width = 12  # Night/Date
        ws.column_dimensions["B"].width = 25  # Hotel
        ws.column_dimensions["C"].width = 15  # City
        ws.column_dimensions["D"].width = 12  # Room Number
        ws.column_dimensions["E"].width = 12  # Room Type
        ws.column_dimensions["F"].width = 15  # Bed Setup
        ws.column_dimensions["G"].width = 25  # Occupant Name
        ws.column_dimensions["H"].width = 12  # Role
        ws.column_dimensions["I"].width = 30  # Notes

        # === SAVE TO MEMORY ===
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        excel_data = base64.b64encode(output.read())

        # === CREATE ATTACHMENT AND RETURN DOWNLOAD ACTION ===
        filename = f"Rooming_List_{self.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        attachment = self.env["ir.attachment"].create({
            "name": filename,
            "type": "binary",
            "datas": excel_data,
            "res_model": self._name,
            "res_id": self.id,
            "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        })

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
            "target": "self",
        }
