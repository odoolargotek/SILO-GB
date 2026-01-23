# -*- coding: utf-8 -*-

# LT Brigade Module - Mejoras Odoo 18
# Largotek SRL - Juan Luis Garvía - www.largotek.com
# License: LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
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
    _description = "Global Brigades - Chapter / Brigade"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    # =========================
    # CAMPO ACTIVE (para archivar)
    # =========================
    active = fields.Boolean(
        string="Active",
        default=True,
        help="If unchecked, this brigade will be archived and hidden from main views.",
        tracking=True,
    )

    # =========================
    # IDENTIFICACIÓN BÁSICA
    # =========================
    external_brigade_code = fields.Char(
        string="Brigade Code",
        help="External reference / code from CRM or other system.",
        tracking=True,
    )

    brigade_code = fields.Char(
        string="Internal Code",
        readonly=True,
        copy=False,
        default="/",
        tracking=True,
    )

    name = fields.Char(string="CHAPTER NAME", required=True, tracking=True)
    arrival_date = fields.Date(string="Arrival Date", tracking=True)
    departure_date = fields.Date(string="Departure Date", tracking=True)

    # =========================
    # ESTADO OPERATIVO
    # =========================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("planned", "Planned"),
            ("ready", "Ready"),
            ("in_field", "In Field"),
            ("completed", "Completed"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        required=True,
        help="Operational state of the Brigade",
        tracking=True,
    )

    brigade_type = fields.Selection(
        [
            ("onsite", "In Person"),
            ("virtual", "Virtual"),
        ],
        string="Brigade Type",
        default="onsite",
        required=True,
        help="If set to Virtual, logistics sections should not be used.",
        tracking=True,
    )

    brigade_restriction = fields.Selection(
        [
            ("no_restrictions", "No Restrictions"),
            ("darien_golfo", "Darien & Golfo de Mosquito"),
            ("este_darien", "Este y Darien"),
            ("solo_darien", "Solo Darien"),
            ("otros", "Otros"),
        ],
        string="Restrictions",
        help="Geographic / operational restrictions.",
        tracking=True,
    )

    brigade_program = fields.Selection(
        [
            ("medical", "Medical"),
            ("dental", "Dental"),
            ("business", "Business"),
            ("water", "Water"),
            ("public_health", "Public Health"),
            ("engineering", "Engineering"),
            ("squads", "Squads"),
        ],
        string="Official Program",
        help="Main official program.",
        tracking=True,
    )

    # =========================
    # LT ITINERARY SIMPLE
    # =========================
    lt_itinerary_link = fields.Char(
        string="Itinerary Link",
        help="Pegar link de GDrive o cualquier URL.",
    )

    lt_itinerary_locked = fields.Boolean(
        string="Bloquear Link",
        default=False,
    )

    lt_itinerary_url = fields.Char(
        string="Itinerary URL",
        compute="_compute_lt_itinerary_url",
        store=True,
        readonly=True,
    )

    # =========================
    # BUSINESS / TIER
    # =========================
    business_client_id = fields.Many2one(
        "res.partner",
        string="Business Client",
        help="Client when program is Business.",
        tracking=True,
    )

    business_profile_link = fields.Char(
        string="Business Profile Link",
        related="business_client_id.business_profile_link",
        readonly=True,
    )

    @api.onchange("brigade_program")
    def _onchange_brigade_program_business_client(self):
        for record in self:
            if record.brigade_program != "business":
                record.business_client_id = False

    brigade_tier = fields.Selection(
        [
            ("sustainable", "Sustainable"),
            ("empowered", "Empowered"),
            ("scaled", "Scaled"),
        ],
        string="Brigade Tier",
        help="Tier: Sustainable(14-25), Empowered(26-39), Scaled(40+).",
        tracking=True,
    )

    # =========================
    # CONTADORES UNIFICADOS
    # =========================
    volunteer_count = fields.Integer(
        string="Volunteers", compute="_compute_counts"
    )
    program_count = fields.Integer(
        string="Programs", compute="_compute_counts"
    )
    activity_count = fields.Integer(
        string="Activities", compute="_compute_counts"
    )
    transport_count = fields.Integer(
        string="Transports", compute="_compute_counts"
    )

    # =========================
    # KPI COUNTS (simplified)
    # =========================
    staff_count = fields.Integer(
        string="Staff Count",
        compute="_compute_kpi_counts",
        store=False,
        help="Total number of staff members assigned.",
    )
    total_participants = fields.Integer(
        string="Total Participants",
        compute="_compute_kpi_counts",
        store=False,
        help="Total participants (Roster + Staff).",
    )

    university_logo = fields.Image(string="University Logo")
    compound_manager_id = fields.Many2one(
        "res.partner", string="COMPOUND SUPERVISOR", tracking=True,
    )
    arrival_time_compound = fields.Datetime(
        string="Arrival time to Compound"
    )
    departure_time_compound = fields.Datetime(
        string="Departure time from Compound"
    )
    coordinator_id = fields.Many2one(
        "res.partner", string="LEAD COORDINATOR", tracking=True,
    )
    program_associate_id = fields.Many2one(
        "res.partner", string="PROGRAM ADVISOR", tracking=True,
    )

    chapter_leader_ids = fields.Many2many(
        "gb.brigade.roster",
        "gb_brigade_chapter_leader_rel",
        "brigade_id",
        "roster_id",
        string="Chapter Leader(s)",
    )
    chapter_president_faculty_ids = fields.Many2many(
        "gb.brigade.roster",
        "gb_brigade_chapter_president_faculty_rel",
        "brigade_id",
        "roster_id",
        string="Chapter President / Faculty",
    )
    professor_chaperone_ids = fields.Many2many(
        "gb.brigade.roster",
        "gb_brigade_professor_chaperone_rel",
        "brigade_id",
        "roster_id",
        string="Professor / Chaperone",
    )

    extra_info = fields.Text(string="Additional Information")

    # =========================
    # ONE2MANY RELACIONES
    # =========================
    program_line_ids = fields.One2many(
        "gb.brigade.program", "brigade_id", string="Programs"
    )
    roster_ids = fields.One2many(
        "gb.brigade.roster", "brigade_id", string="Roster"
    )
    arrival_ids = fields.One2many(
        "gb.brigade.arrival", "brigade_id", string="Arrivals"
    )
    departure_ids = fields.One2many(
        "gb.brigade.departure", "brigade_id", string="Departures"
    )
    staff_ids = fields.One2many(
        "gb.brigade.staff", "brigade_id", string="Temp Staff"
    )
    # RENAMED: activity_ids -> brigade_activity_ids to avoid conflict with mail.activity.mixin
    brigade_activity_ids = fields.One2many(
        "gb.brigade.activity", "brigade_id", string="Activities"
    )
    hotel_booking_ids = fields.One2many(
        "gb.brigade.hotel.booking", "brigade_id", string="Hotel"
    )
    transport_ids = fields.One2many(
        "gb.brigade.transport", "brigade_id", string="Transport"
    )

    _sql_constraints = [
        (
            "chapter_code_uniq",
            "unique(brigade_code)",
            "Brigade Code must be unique!",
        ),
    ]

    # =========================
    # COMPUTES / CONSTRAINS
    # =========================
    @api.depends("roster_ids", "program_line_ids", "brigade_activity_ids", "transport_ids")
    def _compute_counts(self):
        for rec in self:
            rec.volunteer_count = len(rec.roster_ids)
            rec.program_count = len(rec.program_line_ids)
            rec.activity_count = len(rec.brigade_activity_ids)
            rec.transport_count = len(rec.transport_ids)

    @api.depends("volunteer_count", "staff_ids")
    def _compute_kpi_counts(self):
        """Compute simplified KPI counts for brigade."""
        for rec in self:
            staff_total = len(rec.staff_ids)
            rec.staff_count = staff_total
            rec.total_participants = rec.volunteer_count + staff_total

    @api.constrains(
        "brigade_type",
        "transport_ids",
        "hotel_booking_ids",
        "arrival_ids",
        "departure_ids",
    )
    def _check_virtual_no_logistics(self):
        for rec in self:
            if rec.brigade_type == "virtual" and (
                rec.transport_ids
                or rec.hotel_booking_ids
                or rec.arrival_ids
                or rec.departure_ids
            ):
                raise ValidationError(
                    _("Virtual brigades cannot have logistics records.")
                )

    # =========================
    # ITINERARY URL (compute)
    # =========================
    @api.depends("lt_itinerary_link")
    def _compute_lt_itinerary_url(self):
        for rec in self:
            if rec.lt_itinerary_link:
                url = rec.lt_itinerary_link.strip()
                if not (url.startswith("http://") or url.startswith("https://")):
                    url = "https://" + url
                rec.lt_itinerary_url = url
            else:
                rec.lt_itinerary_url = False


    # =========================
    # WRITE / CREATE / ACTIONS
    # =========================

    def write(self, vals):
        if "lt_itinerary_link" in vals:
            for rec in self:
                if rec.lt_itinerary_locked:
                    raise ValidationError(
                        _("Itinerary Link está BLOQUEADO. Desactiva el switch primero.")
                    )
        result = super().write(vals)
        # Renumerar roster y staff después de guardar
        for rec in self:
            rec._renumber_roster()
            rec._renumber_staff()
        return result

    @api.model
    def create(self, vals):
        code = vals.get("brigade_code") or "/"
        if code == "/":
            next_code = self.env["ir.sequence"].next_by_code("gb.brigade.code")
            if not next_code:
                raise ValidationError(
                    _(
                        "No se pudo obtener la secuencia 'gb.brigade.code'. "
                        "Verifica que 'sequence.xml' esté cargado en el manifest."
                    )
                )
            vals["brigade_code"] = next_code
        record = super().create(vals)
        # Renumerar roster y staff después de crear
        record._renumber_roster()
        record._renumber_staff()
        return record

    def _renumber_roster(self):
        """Renumber all roster entries based on sequence."""
        self.ensure_one()
        roster_sorted = self.roster_ids.sorted(key=lambda r: (r.sequence, r.id))
        for idx, roster in enumerate(roster_sorted, start=1):
            if roster.line_number != idx:
                roster.write({'line_number': idx})

    def _renumber_staff(self):
        """Renumber all staff entries based on sequence."""
        self.ensure_one()
        staff_sorted = self.staff_ids.sorted(key=lambda s: (s.sequence, s.start_datetime or datetime.min, s.id))
        for idx, staff in enumerate(staff_sorted, start=1):
            if staff.line_number != idx:
                staff.write({'line_number': idx})

    def open_form_action(self):
        """Abre el formulario de la brigada desde la vista lista."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Brigade"),
            "res_model": "gb.brigade",
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
        }

    def action_open_roster_import_wizard(self):
        """
        Abre el wizard de importación de Roster desde Excel.
        (Odoo 18 safe: NO usa active_id en XML)
        """
        self.ensure_one()
        action = self.env.ref(
            "global_brigades.action_gb_roster_import_wizard"
        ).read()[0]
        action["context"] = dict(
            self.env.context,
            default_brigade_id=self.id,
        )
        return action

    def action_export_rooming_list(self):
        """
        Generate and download Rooming List Excel for this brigade.
        Reads from gb.brigade.hotel.booking (check-in/check-out ranges)
        and shows detailed passenger assignments (one row per person per stay).
        """
        self.ensure_one()

        # Get all hotel bookings for this brigade
        booking_recs = self.env["gb.brigade.hotel.booking"].search(
            [("brigade_id", "=", self.id)],
            order="check_in_date, check_out_date, id"
        )

        if not booking_recs:
            raise UserError(_(
                "No hotel bookings/rooming assignments found for this brigade. "
                "Please create hotel bookings in the 'Hotels / Rooming' tab first."
            ))

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
        center_alignment = Alignment(horizontal="center", vertical="center")

        # === TITLE ===
        ws.merge_cells("A1:J1")
        title_cell = ws["A1"]
        title_cell.value = f"ROOMING LIST - {self.name}"
        title_cell.font = Font(bold=True, size=14)
        title_cell.alignment = Alignment(horizontal="center", vertical="center")

        # === HEADERS (Row 3) ===
        headers = [
            "Check-In",
            "Check-Out",
            "Nights",
            "Hotel",
            "City",
            "Room #",
            "Room Type",
            "Beds",
            "Passenger Name",
            "Type",
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
        for booking in booking_recs:
            check_in_str = booking.check_in_date.strftime("%Y-%m-%d") if booking.check_in_date else ""
            check_out_str = booking.check_out_date.strftime("%Y-%m-%d") if booking.check_out_date else ""
            nights = booking.stay_nights or 0
            hotel_name = booking.partner_id.name if booking.partner_id else ""
            city = booking.city or ""

            # Collect all passengers for this booking (Roster + Staff)
            all_passengers = []

            # From assignment_ids (Roster)
            for line in booking.assignment_ids:
                for occupant in line.occupant_ids:
                    room_number = line.room_number or ""
                    room_type_val = dict(line.hotel_room_id._fields["room_type"].selection).get(
                        line.room_type, line.room_type or ""
                    ) if line.room_type else ""
                    bed_setup = line.bed_setup or ""
                    occupant_name = occupant.partner_id.name if occupant.partner_id else ""
                    ptype = "Roster"

                    all_passengers.append({
                        "check_in": check_in_str,
                        "check_out": check_out_str,
                        "nights": nights,
                        "hotel": hotel_name,
                        "city": city,
                        "room_number": room_number,
                        "room_type": room_type_val,
                        "bed_setup": bed_setup,
                        "name": occupant_name,
                        "type": ptype,
                    })

            # From staff_assignment_ids (Staff)
            for sline in booking.staff_assignment_ids:
                for staff_occupant in sline.occupant_staff_ids:
                    room_number = sline.room_number or ""
                    room_type_val = dict(sline.hotel_room_id._fields["room_type"].selection).get(
                        sline.room_type, sline.room_type or ""
                    ) if sline.room_type else ""
                    bed_setup = sline.bed_setup or ""
                    staff_name = staff_occupant.person_id.name if staff_occupant.person_id else ""
                    ptype = "Staff"

                    all_passengers.append({
                        "check_in": check_in_str,
                        "check_out": check_out_str,
                        "nights": nights,
                        "hotel": hotel_name,
                        "city": city,
                        "room_number": room_number,
                        "room_type": room_type_val,
                        "bed_setup": bed_setup,
                        "name": staff_name,
                        "type": ptype,
                    })

            # If no passengers assigned, still show the booking header
            if not all_passengers:
                for col_num in range(1, len(headers) + 1):
                    cell = ws.cell(row=row_idx, column=col_num)
                    cell.border = border_thin
                    cell.alignment = center_alignment

                ws.cell(row=row_idx, column=1).value = check_in_str
                ws.cell(row=row_idx, column=2).value = check_out_str
                ws.cell(row=row_idx, column=3).value = nights
                ws.cell(row=row_idx, column=4).value = hotel_name
                ws.cell(row=row_idx, column=5).value = city
                row_idx += 1
            else:
                # One row per passenger
                for pax in all_passengers:
                    for col_num in range(1, len(headers) + 1):
                        cell = ws.cell(row=row_idx, column=col_num)
                        cell.border = border_thin
                        cell.alignment = center_alignment if col_num <= 8 else Alignment(vertical="center")

                    ws.cell(row=row_idx, column=1).value = pax["check_in"]
                    ws.cell(row=row_idx, column=2).value = pax["check_out"]
                    ws.cell(row=row_idx, column=3).value = pax["nights"]
                    ws.cell(row=row_idx, column=4).value = pax["hotel"]
                    ws.cell(row=row_idx, column=5).value = pax["city"]
                    ws.cell(row=row_idx, column=6).value = pax["room_number"]
                    ws.cell(row=row_idx, column=7).value = pax["room_type"]
                    ws.cell(row=row_idx, column=8).value = pax["bed_setup"]
                    ws.cell(row=row_idx, column=9).value = pax["name"]
                    ws.cell(row=row_idx, column=10).value = pax["type"]
                    row_idx += 1

        # === COLUMN WIDTHS ===
        ws.column_dimensions["A"].width = 12  # Check-In
        ws.column_dimensions["B"].width = 12  # Check-Out
        ws.column_dimensions["C"].width = 8   # Nights
        ws.column_dimensions["D"].width = 25  # Hotel
        ws.column_dimensions["E"].width = 15  # City
        ws.column_dimensions["F"].width = 10  # Room #
        ws.column_dimensions["G"].width = 12  # Room Type
        ws.column_dimensions["H"].width = 15  # Beds
        ws.column_dimensions["I"].width = 25  # Passenger Name
        ws.column_dimensions["J"].width = 10  # Type

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

    def action_export_transport_list(self):
        """
        Generate and download Transport Assignments Excel for this brigade.
        Shows passenger assignments by vehicle.
        """
        self.ensure_one()

        # Get all transport records for this brigade
        transport_recs = self.env["gb.brigade.transport"].search(
            [("brigade_id", "=", self.id)],
            order="date_time, id"
        )

        if not transport_recs:
            raise UserError(_("No transport records found for this brigade. "
                            "Please create transport records first."))

        # Build Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "Transport Assignments"

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
        ws.merge_cells("A1:K1")
        title_cell = ws["A1"]
        title_cell.value = f"TRANSPORT ASSIGNMENTS - {self.name}"
        title_cell.font = Font(bold=True, size=14)
        title_cell.alignment = Alignment(horizontal="center", vertical="center")

        # === HEADERS (Row 3) ===
        headers = [
            "Date/Time",
            "Transport Title",
            "Origin",
            "Destination",
            "Vehicle",
            "Provider",
            "Capacity",
            "Passenger Name",
            "Type",
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
        for transport in transport_recs:
            date_time = transport.date_time.strftime("%Y-%m-%d %H:%M") if transport.date_time else ""
            title = transport.title or ""
            origin = transport.origin or ""
            destination = transport.destination or ""
            transport_notes = transport.notes or ""

            if not transport.vehicle_line_ids:
                # No vehicle lines defined - show header vehicle if exists
                vehicle_name = transport.vehicle_id.name if transport.vehicle_id else ""
                provider_name = transport.provider_id.name if transport.provider_id else ""
                capacity = transport.vehicle_id.capacity if transport.vehicle_id else 0

                # Get all passengers (roster + staff)
                all_passengers = []
                for roster in transport.passenger_ids:
                    all_passengers.append({
                        'name': roster.partner_id.name if roster.partner_id else '',
                        'type': 'Roster',
                        'role': roster.brigade_role or ''
                    })
                for staff in transport.staff_passenger_ids:
                    all_passengers.append({
                        'name': staff.person_id.name if staff.person_id else '',
                        'type': 'Staff',
                        'role': dict(staff._fields['staff_role'].selection).get(staff.staff_role, staff.staff_role or '')
                    })

                if not all_passengers:
                    # No passengers at all
                    for col_num in range(1, len(headers) + 1):
                        cell = ws.cell(row=row_idx, column=col_num)
                        cell.border = border_thin
                        cell.alignment = Alignment(vertical="center")

                    ws.cell(row=row_idx, column=1).value = date_time
                    ws.cell(row=row_idx, column=2).value = title
                    ws.cell(row=row_idx, column=3).value = origin
                    ws.cell(row=row_idx, column=4).value = destination
                    ws.cell(row=row_idx, column=5).value = vehicle_name
                    ws.cell(row=row_idx, column=6).value = provider_name
                    ws.cell(row=row_idx, column=7).value = capacity
                    ws.cell(row=row_idx, column=11).value = transport_notes
                    row_idx += 1
                else:
                    # One row per passenger
                    for pax in all_passengers:
                        for col_num in range(1, len(headers) + 1):
                            cell = ws.cell(row=row_idx, column=col_num)
                            cell.border = border_thin
                            cell.alignment = Alignment(vertical="center")

                        ws.cell(row=row_idx, column=1).value = date_time
                        ws.cell(row=row_idx, column=2).value = title
                        ws.cell(row=row_idx, column=3).value = origin
                        ws.cell(row=row_idx, column=4).value = destination
                        ws.cell(row=row_idx, column=5).value = vehicle_name
                        ws.cell(row=row_idx, column=6).value = provider_name
                        ws.cell(row=row_idx, column=7).value = capacity
                        ws.cell(row=row_idx, column=8).value = pax['name']
                        ws.cell(row=row_idx, column=9).value = pax['type']
                        ws.cell(row=row_idx, column=10).value = pax['role']
                        ws.cell(row=row_idx, column=11).value = transport_notes
                        row_idx += 1
                continue

            # Process vehicle lines
            for line in transport.vehicle_line_ids:
                vehicle_name = line.vehicle_id.name if line.vehicle_id else ""
                provider_name = line.provider_id.name if line.provider_id else ""
                capacity = line.capacity or 0

                # Get passengers for this vehicle
                vehicle_passengers = []
                for roster in line.roster_passenger_ids:
                    vehicle_passengers.append({
                        'name': roster.partner_id.name if roster.partner_id else '',
                        'type': 'Roster',
                        'role': roster.brigade_role or ''
                    })
                for staff in line.staff_passenger_ids:
                    vehicle_passengers.append({
                        'name': staff.person_id.name if staff.person_id else '',
                        'type': 'Staff',
                        'role': dict(staff._fields['staff_role'].selection).get(staff.staff_role, staff.staff_role or '')
                    })

                if not vehicle_passengers:
                    # Empty vehicle
                    for col_num in range(1, len(headers) + 1):
                        cell = ws.cell(row=row_idx, column=col_num)
                        cell.border = border_thin
                        cell.alignment = Alignment(vertical="center")

                    ws.cell(row=row_idx, column=1).value = date_time
                    ws.cell(row=row_idx, column=2).value = title
                    ws.cell(row=row_idx, column=3).value = origin
                    ws.cell(row=row_idx, column=4).value = destination
                    ws.cell(row=row_idx, column=5).value = vehicle_name
                    ws.cell(row=row_idx, column=6).value = provider_name
                    ws.cell(row=row_idx, column=7).value = capacity
                    ws.cell(row=row_idx, column=11).value = transport_notes
                    row_idx += 1
                else:
                    # One row per passenger
                    for pax in vehicle_passengers:
                        for col_num in range(1, len(headers) + 1):
                            cell = ws.cell(row=row_idx, column=col_num)
                            cell.border = border_thin
                            cell.alignment = Alignment(vertical="center")

                        ws.cell(row=row_idx, column=1).value = date_time
                        ws.cell(row=row_idx, column=2).value = title
                        ws.cell(row=row_idx, column=3).value = origin
                        ws.cell(row=row_idx, column=4).value = destination
                        ws.cell(row=row_idx, column=5).value = vehicle_name
                        ws.cell(row=row_idx, column=6).value = provider_name
                        ws.cell(row=row_idx, column=7).value = capacity
                        ws.cell(row=row_idx, column=8).value = pax['name']
                        ws.cell(row=row_idx, column=9).value = pax['type']
                        ws.cell(row=row_idx, column=10).value = pax['role']
                        ws.cell(row=row_idx, column=11).value = transport_notes
                        row_idx += 1

        # === COLUMN WIDTHS ===
        ws.column_dimensions["A"].width = 16  # Date/Time
        ws.column_dimensions["B"].width = 25  # Transport Title
        ws.column_dimensions["C"].width = 20  # Origin
        ws.column_dimensions["D"].width = 20  # Destination
        ws.column_dimensions["E"].width = 20  # Vehicle
        ws.column_dimensions["F"].width = 20  # Provider
        ws.column_dimensions["G"].width = 10  # Capacity
        ws.column_dimensions["H"].width = 25  # Passenger Name
        ws.column_dimensions["I"].width = 10  # Type
        ws.column_dimensions["J"].width = 20  # Role
        ws.column_dimensions["K"].width = 30  # Notes

        # === SAVE TO MEMORY ===
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        excel_data = base64.b64encode(output.read())

        # === CREATE ATTACHMENT AND RETURN DOWNLOAD ACTION ===
        filename = f"Transport_List_{self.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
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

# ===========================================================
# Program Lines (PROGRAMS tab)
# ===========================================================
class GBBrigadeProgram(models.Model):
    _name = "gb.brigade.program"
    _description = "Brigade Program Line"
    _order = "sequence, id"

    brigade_id = fields.Many2one(
        "gb.brigade",
        string="Brigade",
        ondelete="cascade",
        required=True,
    )

    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Order of this program line in the list.",
    )

    program_id = fields.Many2one(
        "gb.program",
        string="Program",
        required=True,
        help="Program type (Medical, Dental, Business, etc.) for this line.",
    )

    start_date = fields.Date(
        string="Start Date",
        help="When this program begins for this brigade.",
    )

    end_date = fields.Date(
        string="End Date",
        help="When this program ends for this brigade.",
    )

    # NUEVO: selección de comunidad desde el nuevo modelo
    community_id = fields.Many2one(
        "gb.community",
        string="Community",
        help="Community where this program activity will take place.",
    )

    # Seguimos usando el campo location para guardar el nombre de la comunidad
    location = fields.Char(
        string="Location / Community / Site",
        help="Where this program activity will take place.",
    )

    coordinator_id = fields.Many2one(
        "res.partner",
        string="Program Lead / Coordinator",
        help="Main staff contact for this program line.",
    )

    notes = fields.Char(
        string="Notes / Focus Area",
        help="Extra notes about this program line (focus, goals, etc.).",
    )

    @api.onchange("community_id")
    def _onchange_community_id(self):
        """Cuando se elige una comunidad, copiamos el nombre al campo location."""
        for rec in self:
            rec.location = rec.community_id.name or False

# ===========================================================
# Roster (participantes / voluntarios)
# ===========================================================

class GBBrigadeRoster(models.Model):
    _name = "gb.brigade.roster"
    _description = "Global Brigades - Roster"
    _rec_name = "partner_id"
    _order = "sequence, id"

    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Order for sorting",
    )

    line_number = fields.Integer(
        string="N",
        default=0,
        help="Line number (1, 2, 3...), automatically calculated",
    )

    brigade_id = fields.Many2one(
        "gb.brigade",
        string="Brigade",
        required=True,
        ondelete="cascade",
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Name",
        required=True,
    )

    email = fields.Char(
        string="Email",
        related="partner_id.email",
        store=False,
        readonly=True,
    )

    phone_display = fields.Char(
        string="Phone Number",
        compute="_compute_phone_display",
        help="Concatenates Mobile and Phone if available.",
    )

    gender = fields.Selection(
        related="partner_id.gb_gender",
        readonly=True,
        store=False,
    )

    birthdate = fields.Date(
        related="partner_id.gb_birthdate",
        readonly=True,
        store=False,
    )

    spanish_speaker = fields.Boolean(
        string="Spanish Speaker",
        related="partner_id.gb_spanish_speaker",
        readonly=True,
        store=False,
    )

    passport_no = fields.Char(
        related="partner_id.gb_passport_no",
        readonly=True,
        store=False,
    )

    passport_expiry = fields.Date(
        related="partner_id.gb_passport_expiry",
        readonly=True,
        store=False,
    )

    citizenship = fields.Char(
        related="partner_id.gb_citizenship",
        readonly=True,
        store=False,
    )

    tshirt_size = fields.Selection(
        related="partner_id.gb_tshirt_size",
        readonly=True,
        store=False,
    )

    brigade_role = fields.Char(string="Role in Brigade")
    sa = fields.Boolean(string="S.A.")

    # Estos vienen desde res.partner (gb_diet, gb_medical_condition, gb_medications, gb_allergy)
    diet = fields.Char(
        string="Diet / Restrictions",
        related="partner_id.gb_diet",
        store=False,
        readonly=True,
    )

    medical_condition = fields.Char(
        string="Medical Condition",
        related="partner_id.gb_medical_condition",
        store=False,
        readonly=True,
    )

    medications = fields.Text(
        string="Medications",
        related="partner_id.gb_medications",
        store=False,
        readonly=True,
    )

    allergy = fields.Char(
        string="Allergies",
        related="partner_id.gb_allergy",
        store=False,
        readonly=True,
    )

    emergency_contact_id = fields.Many2one(
        "res.partner",
        string="Emergency Contact",
    )

    emergency_contact_email = fields.Char(
        string="Emergency Contact Email",
        related="emergency_contact_id.email",
        store=False,
        readonly=True,
    )

    # NUEVO: Campo de notas al final
    notes = fields.Text(
        string="Notes",
        help="Additional notes or observations about this roster participant.",
    )

    @api.depends("partner_id.mobile", "partner_id.phone")
    def _compute_phone_display(self):
        for rec in self:
            mobile = rec.partner_id.mobile or ""
            phone = rec.partner_id.phone or ""
            if mobile and phone and mobile != phone:
                rec.phone_display = f"{mobile} / {phone}"
            else:
                rec.phone_display = mobile or phone or ""

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # Renumerar después de crear
        brigades = records.mapped('brigade_id')
        for brigade in brigades:
            brigade._renumber_roster()
        return records

    def write(self, vals):
        result = super().write(vals)
        # Renumerar después de escribir
        if 'sequence' in vals:
            brigades = self.mapped('brigade_id')
            for brigade in brigades:
                brigade._renumber_roster()
        return result

    def unlink(self):
        brigades = self.mapped('brigade_id')
        result = super().unlink()
        # Renumerar después de borrar
        for brigade in brigades:
            brigade._renumber_roster()
        return result

# ===========================================================
# Arrivals (Warning only, no blocking)
# ===========================================================

class GBBrigadeArrival(models.Model):
    _name = "gb.brigade.arrival"
    _description = "Global Brigades - Arrival Info"
    _order = "date_time_arrival, id"

    brigade_id = fields.Many2one(
        "gb.brigade",
        string="Brigade",
        required=True,
        ondelete="cascade",
    )

    title = fields.Char(string="Airline", required=True)
    flight_number = fields.Char(string="Flight #")
    date_time_arrival = fields.Datetime(string="Arrival DateTime")
    flight_through_sap = fields.Char(string="Through SAP / Stopover")

    arrival_hotel_id = fields.Many2one(
        "gb.hotel.offer",
        string="Arrival Hotel",
    )

    arrival_hotel_city_time = fields.Char(
        string="Arrival Hotel Notes (City / Time)",
    )

    passenger_ids = fields.Many2many(
        "gb.brigade.roster",
        "gb_arrival_roster_rel",
        "arrival_id",
        "roster_id",
        string="Passengers",
    )

    available_passenger_ids = fields.Many2many(
        "gb.brigade.roster",
        compute="_compute_available_passenger_ids",
        store=False,
    )

    n_pax = fields.Integer(
        string="# Pax",
        compute="_compute_n_pax",
        store=False,
    )

    special_transport = fields.Boolean(string="Special Transport Needed?")
    extra_charge = fields.Char(string="Extra Charge / Notes")

    # ---------------- COMPUTES ----------------

    @api.depends("passenger_ids")
    def _compute_n_pax(self):
        for rec in self:
            rec.n_pax = len(rec.passenger_ids)

    @api.depends("brigade_id", "brigade_id.roster_ids",
                 "brigade_id.arrival_ids.passenger_ids", "passenger_ids")
    def _compute_available_passenger_ids(self):
        for rec in self:
            if not rec.brigade_id:
                rec.available_passenger_ids = False
                continue

            all_roster = rec.brigade_id.roster_ids
            other_arrivals_passengers = rec.brigade_id.arrival_ids.filtered(
                lambda a: a.id != rec.id
            ).mapped("passenger_ids")

            used = other_arrivals_passengers
            available = (all_roster - used) | rec.passenger_ids
            rec.available_passenger_ids = available

    # ---------------- WARNING ONLY ----------------

    @api.onchange("passenger_ids")
    def _onchange_passenger_ids_duplicates(self):
        """
        Warning only (no constraint). User can still save.
        """
        for rec in self:
            if not rec.brigade_id or not rec.passenger_ids:
                continue

            passenger_ids = rec.passenger_ids.ids
            Arrival = self.env["gb.brigade.arrival"]

            other_arrivals = Arrival.search([
                ("brigade_id", "=", rec.brigade_id.id),
                ("id", "!=", rec.id),
                ("passenger_ids", "in", passenger_ids),
            ])

            if not other_arrivals:
                continue

            conflicts = {}
            for other in other_arrivals:
                common = other.passenger_ids.filtered(
                    lambda p: p.id in passenger_ids
                )
                for p in common:
                    conflicts.setdefault(
                        p.partner_id.name or p.display_name, []
                    ).append(
                        _("Arrival: %(title)s (%(date)s)") % {
                            "title": other.title or "",
                            "date": fields.Datetime.to_string(
                                other.date_time_arrival
                            ) if other.date_time_arrival else "",
                        }
                    )

            if conflicts:
                lines = []
                for name, entries in conflicts.items():
                    lines.append(f"- {name}: " + "; ".join(entries))

                message = (
                    "These passengers already appear in another Arrival of this brigade:\n"
                    + "\n".join(lines)
                )

                return {
                    "warning": {
                        "title": _("Passenger already in another Arrival"),
                        "message": message,
                    }
                }

# ===========================================================
# Departures (Warning only, no blocking)
# ===========================================================

class GBBrigadeDeparture(models.Model):
    _name = "gb.brigade.departure"
    _description = "Global Brigades - Departure Info"
    _order = "date_time_departure, id"

    brigade_id = fields.Many2one(
        "gb.brigade",
        string="Brigade",
        required=True,
        ondelete="cascade",
    )

    title = fields.Char(string="Airline", required=True)
    flight_number = fields.Char(string="Flight #")
    date_time_departure = fields.Datetime(string="Departure DateTime")
    flight_through_sap = fields.Char(string="Through SAP / Stopover")

    departure_hotel_id = fields.Many2one(
        "gb.hotel.offer",
        string="Departure Hotel",
    )

    departure_hotel_city = fields.Char(
        string="Departure Hotel Notes (City)",
    )

    passenger_ids = fields.Many2many(
        "gb.brigade.roster",
        "gb_departure_roster_rel",
        "departure_id",
        "roster_id",
        string="Passengers",
    )

    available_passenger_ids = fields.Many2many(
        "gb.brigade.roster",
        compute="_compute_available_passenger_ids",
        store=False,
    )

    n_pax = fields.Integer(
        string="# Pax",
        compute="_compute_n_pax",
        store=False,
    )

    special_transport = fields.Boolean(string="Special Transport Needed?")
    extra_charge = fields.Char(string="Extra Charge / Notes")

    # ---------------- COMPUTES ----------------

    @api.depends("passenger_ids")
    def _compute_n_pax(self):
        for rec in self:
            rec.n_pax = len(rec.passenger_ids)

    @api.depends("brigade_id", "brigade_id.roster_ids",
                 "brigade_id.departure_ids.passenger_ids", "passenger_ids")
    def _compute_available_passenger_ids(self):
        for rec in self:
            if not rec.brigade_id:
                rec.available_passenger_ids = False
                continue

            all_roster = rec.brigade_id.roster_ids
            other_departures_passengers = rec.brigade_id.departure_ids.filtered(
                lambda d: d.id != rec.id
            ).mapped("passenger_ids")

            used = other_departures_passengers
            available = (all_roster - used) | rec.passenger_ids
            rec.available_passenger_ids = available

    # ---------------- WARNING ONLY ----------------

    @api.onchange("passenger_ids")
    def _onchange_passenger_ids_duplicates(self):
        """
        Warning only (no constraint). User can still save.
        """
        for rec in self:
            if not rec.brigade_id or not rec.passenger_ids:
                continue

            passenger_ids = rec.passenger_ids.ids
            Departure = self.env["gb.brigade.departure"]

            other_departures = Departure.search([
                ("brigade_id", "=", rec.brigade_id.id),
                ("id", "!=", rec.id),
                ("passenger_ids", "in", passenger_ids),
            ])

            if not other_departures:
                continue

            conflicts = {}
            for other in other_departures:
                common = other.passenger_ids.filtered(
                    lambda p: p.id in passenger_ids
                )
                for p in common:
                    conflicts.setdefault(
                        p.partner_id.name or p.display_name, []
                    ).append(
                        _("Departure: %(title)s (%(date)s)") % {
                            "title": other.title or "",
                            "date": fields.Datetime.to_string(
                                other.date_time_departure
                            ) if other.date_time_departure else "",
                        }
                    )

            if conflicts:
                lines = []
                for name, entries in conflicts.items():
                    lines.append(f"- {name}: " + "; ".join(entries))

                message = (
                    "These passengers already appear in another Departure of this brigade:\n"
                    + "\n".join(lines)
                )

                return {
                    "warning": {
                        "title": _("Passenger already in another Departure"),
                        "message": message,
                    }
                }

# ===========================================================
# Staff temporal
# ===========================================================

class GBBrigadeStaff(models.Model):
    _name = 'gb.brigade.staff'
    _description = 'Brigade Staff Assignment'
    _order = 'sequence, start_datetime, person_id'
    _rec_name = 'name'

    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Order for sorting",
    )

    line_number = fields.Integer(
        string="N",
        default=0,
        help="Line number (1, 2, 3...), automatically calculated",
    )

    # Nombre "humano" que usaremos en checkboxes, tags, etc.
    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
    )

    brigade_id = fields.Many2one(
        'gb.brigade',
        string='Brigade',
        required=True,
        ondelete='cascade',
    )

    person_id = fields.Many2one(
        'res.partner',
        string='Person',
        required=True,
        help='Person (contact) assigned as staff member in this brigade.',
    )

    # Datos traídos desde el contacto
    gender = fields.Selection(
        related='person_id.gb_gender',
        string='Gender',
        readonly=True,
    )

    diet = fields.Char(
        related='person_id.gb_diet',
        string='Diet',
        readonly=True,
    )

    allergy = fields.Char(
        related='person_id.gb_allergy',
        string='Allergy',
        readonly=True,
    )

    # CORREGIDO: Ahora lee directamente del campo gb_professional_registration
    professional_registration = fields.Char(
        string='Professional Registration',
        related='person_id.gb_professional_registration',
        readonly=True,
        store=False,
        help='Professional registration number from contact profile.',
    )

    # NUEVO: Brigade Role desde el contacto
    brigade_role_default = fields.Selection(
        related='person_id.gb_brigade_role',
        string='Brigade Role',
        readonly=True,
        store=False,
        help='Default brigade role from contact profile.',
    )

    staff_role = fields.Selection(
        [
            ('driver', 'DRIVER'),
            ('operations_coord', 'OPERATIONS COORDINATOR'),
            ('interpreter_1', 'INTERPRETER 1'),
            ('interpreter_2', 'INTERPRETER 2'),
            ('interpreter_3', 'INTERPRETER 3'),
            ('interpreter_4', 'INTERPRETER 4'),
            ('interpreter_5', 'INTERPRETER 5'),
            ('interpreter_extra', 'INTERPRETER EXTRA'),
            ('doctor_1', 'DOCTOR 1'),
            ('doctor_2', 'DOCTOR 2'),
            ('doctor_3', 'DOCTOR 3'),
            ('doctor_4', 'DOCTOR 4'),
            ('dentist_1', 'DENTIST 1'),
            ('dentist_2', 'DENTIST 2'),
            ('dentist_3', 'DENTIST 3'),
            ('dentist_4', 'DENTIST 4'),
            ('pharmacist', 'PHARMACIST'),
            ('cashier', 'CASHIER'),
            ('nutritionist', 'NUTRITIONIST'),
            ('public_health_tech', 'PUBLIC HEALTH TECHNICIAN'),
            ('paramedic', 'PARAMEDIC'),
            ('water_technician', 'WATER TECHNICIAN'),
            ('optometrist', 'OPTOMETRIST'),
            ('nurse', 'NURSE'),
            ('obgyn', 'OB/GYN'),
            ('pa_visit', 'PA VISIT'),
            ('emergency_vehicle', 'EMERGENCY VEHICLE'),
            ('physiotherapist', 'PHYSIOTHERAPIST'),
            ('doctor_de_cobertura', 'DOCTOR DE COBERTURA'),
            ('doctor_on_call', 'DOCTOR ON CALL'),
            ('coord_assistant_1', 'COORDINATION ASSISTANT 1'),
            ('coord_assistant_2', 'COORDINATION ASSISTANT 2'),
            ('coord_assistant_3', 'COORDINATION ASSISTANT 3'),
            ('coord_assistant_4', 'COORDINATION ASSISTANT 4'),
            ('coord_assistant_5', 'COORDINATION ASSISTANT 5'),
            ('coord_assistant_extra', 'COORDINATION ASSISTANT EXTRA'),
            ('counselor_1', 'COUNSELOR 1'),
            ('counselor_2', 'COUNSELOR 2'),
            ('counselor_3', 'COUNSELOR 3'),
            ('lead_coord_1', 'LEAD COORDINATOR 1'),
            ('lead_coord_2', 'LEAD COORDINATOR 2'),
            ('lead_coord_3', 'LEAD COORDINATOR 3'),
            ('lead_coord_4', 'LEAD COORDINATOR 4'),
            ('lead_coord_5', 'LEAD COORDINATOR 5'),
            ('lead_coord_extra', 'LEAD COORDINATOR EXTRA'),
            ('psychologist', 'PSYCHOLOGIST'),
            ('therapist', 'THERAPIST'),
            ('other', 'OTHER / NOTES IN FIELD'),
        ],
        string='Role',
        help='Role of this person during the brigade.',
    )

    # Fechas propias de la brigada
    start_datetime = fields.Datetime(
        string='Start Date/Time',
        help='Date and time when this person starts working with the brigade.',
    )

    end_datetime = fields.Datetime(
        string='End Date/Time',
        help='Date and time when this person stops working with the brigade.',
    )

    # Campo antiguo (compatibilidad, opcional en vistas)
    diet_allergy_note = fields.Char(
        string='Diet / Allergy / Notes',
        help='Relevant dietary restrictions, allergies or short notes.',
    )

    internal_note = fields.Text(
        string='Internal Notes',
        help='Internal notes for GB staff (not shown externally).',
    )

    provider_id = fields.Many2one(
        'res.partner',
        string='Provider',
        help='Optional provider record, kept for backwards compatibility.',
    )

    @api.depends('person_id', 'person_id.name', 'provider_id', 'provider_id.name', 'staff_role')
    def _compute_name(self):
        """Nombre amigable para staff: 'Juan Pérez (LEAD COORDINATOR 1)'."""
        selection_dict = dict(self._fields['staff_role'].selection)
        for rec in self:
            base = rec.person_id.name or rec.provider_id.name or ""
            role_label = selection_dict.get(rec.staff_role, rec.staff_role or "")
            if base and role_label:
                rec.name = f"{base} ({role_label})"
            else:
                rec.name = base or role_label or _("Staff #%s") % rec.id

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # Renumerar después de crear
        brigades = records.mapped('brigade_id')
        for brigade in brigades:
            brigade._renumber_staff()
        return records

    def write(self, vals):
        result = super().write(vals)
        # Renumerar después de escribir
        if 'sequence' in vals:
            brigades = self.mapped('brigade_id')
            for brigade in brigades:
                brigade._renumber_staff()
        return result

    def unlink(self):
        brigades = self.mapped('brigade_id')
        result = super().unlink()
        # Renumerar después de borrar
        for brigade in brigades:
            brigade._renumber_staff()
        return result

    def name_get(self):
        res = []
        selection_dict = dict(self._fields['staff_role'].selection)
        for rec in self:
            base = rec.person_id.name or rec.provider_id.name or ""
            role_label = selection_dict.get(rec.staff_role, rec.staff_role or "")
            if base and role_label:
                name = f"{base} ({role_label})"
            else:
                name = base or role_label or _("Staff #%s") % rec.id
            res.append((rec.id, name))
        return res


# ===========================================================
# Activity Tag (for itinerary activities)
# ===========================================================

class GBActivityTag(models.Model):
    _name = "gb.activity.tag"
    _description = "Activity Tag / Type"
    _order = "name"
    
    name = fields.Char(string="Tag", required=True)
    color = fields.Integer(string="Color Index")

# ===========================================================
# Brigade Activity / Itinerary entry
# ===========================================================

class GBBrigadeActivity(models.Model):
    _name = "gb.brigade.activity"
    _description = "Global Brigades - Brigade Activity / Itinerary Entry"
    _order = "start_datetime, id"
    
    brigade_id = fields.Many2one(
        "gb.brigade",
        string="Brigade",
        required=True,
        ondelete="cascade",
        help="Which brigade this activity belongs to.",
    )
    
    name = fields.Char(string="Nombre de la actividad", required=True)
    
    tag_ids = fields.Many2many(
        "gb.activity.tag",
        "gb_activity_tag_rel",
        "activity_id",
        "tag_id",
        string="Tipo de actividad",
        help="Labels / categories for this activity (clinic, travel, orientation, etc.).",
    )
    
    start_datetime = fields.Datetime(string="Inicio", help="Start datetime for this activity.")
    end_datetime = fields.Datetime(string="Fin", help="End datetime for this activity.")
    
    place = fields.Char(string="Lugar", help="Location where the activity takes place.")
    
    responsible_id = fields.Many2one(
        "res.partner",
        string="Responsable",
        help="Main person in charge of this activity.",
    )
    
    participant_ids = fields.Many2many(
        "gb.brigade.roster",
        "gb_activity_participant_rel",
        "activity_id",
        "roster_id",
        string="Participantes",
        help="Participants attending this activity.",
    )
    
    participant_count = fields.Integer(
        string="N°",
        compute="_compute_participant_count",
        store=False,
        help="How many participants are assigned to this activity.",
    )
    
    notes = fields.Text(string="Notas", help="Any notes / logistics / reminders for this activity.")
    
    @api.depends("participant_ids")
    def _compute_participant_count(self):
        for rec in self:
            rec.participant_count = len(rec.participant_ids)
    
    def action_add_all_participants(self):
        """Botón 'Todos': mete todo el roster de la brigada en la actividad."""
        for rec in self:
            if rec.brigade_id:
                all_roster = rec.brigade_id.roster_ids
                rec.participant_ids = [(6, 0, all_roster.ids)]
        return True
    
    def action_open_add_participants_wizard(self):
        """
        Botón 'Seleccionar': abre el wizard existente
        para marcar participantes manualmente.
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Seleccionar Participantes"),
            "res_model": "gb.add.participants.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_activity_id": self.id,
            },
        }
