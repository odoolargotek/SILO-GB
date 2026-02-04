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

    # =========================
    # LAST HOTEL BOOKING INFO
    # =========================
    last_hotel_booking_id = fields.Many2one(
        "gb.brigade.hotel.booking",
        string="Last Hotel Booking",
        compute="_compute_last_hotel_booking",
        store=False,
        help="Most recent hotel booking where this person is assigned.",
    )

    last_booking_check_in = fields.Date(
        string="Last Check-In",
        compute="_compute_last_hotel_booking",
        store=False,
        help="Check-in date of last hotel booking.",
    )

    last_booking_check_out = fields.Date(
        string="Last Check-Out",
        compute="_compute_last_hotel_booking",
        store=False,
        help="Check-out date of last hotel booking.",
    )

    last_booking_hotel = fields.Char(
        string="Last Hotel",
        compute="_compute_last_hotel_booking",
        store=False,
        help="Hotel name of last booking.",
    )

    def _normalize_brigade_role(self, role_value):
        """
        Intenta normalizar un valor de brigade_role en texto plano
        a uno de los valores válidos del campo Selection gb_brigade_role.
        
        Returns:
            str: Valor normalizado (clave técnica) o el valor original si no se reconoce
        """
        if not role_value:
            return role_value
            
        # Obtener las opciones válidas del campo Selection
        Partner = self.env['res.partner']
        valid_options = dict(Partner._fields['gb_brigade_role'].selection)
        
        # Normalizar el texto de entrada
        role_str = str(role_value).strip().lower()
        
        # Primero intentar coincidencia exacta (sin considerar mayúsculas)
        for key, label in valid_options.items():
            if role_str == key.lower():
                return key
            if role_str == label.lower():
                return key
                
        # Si no hay coincidencia exacta, devolver el valor original
        return role_value

    @api.depends("partner_id.mobile", "partner_id.phone")
    def _compute_phone_display(self):
        for rec in self:
            mobile = rec.partner_id.mobile or ""
            phone = rec.partner_id.phone or ""
            if mobile and phone and mobile != phone:
                rec.phone_display = f"{mobile} / {phone}"
            else:
                rec.phone_display = mobile or phone or ""

    def _compute_last_hotel_booking(self):
        """
        Computes the last hotel booking where this roster entry appears.
        Shows check-in, check-out, and hotel name for reference.
        """
        for rec in self:
            if not rec.brigade_id:
                rec.last_hotel_booking_id = False
                rec.last_booking_check_in = False
                rec.last_booking_check_out = False
                rec.last_booking_hotel = False
                continue

            # Find bookings where this roster is assigned
            bookings = self.env["gb.brigade.hotel.booking"].search(
                [
                    ("brigade_id", "=", rec.brigade_id.id),
                    ("assignment_ids.occupant_ids", "in", rec.id),
                ],
                order="check_in_date desc, id desc",
                limit=1,
            )

            if bookings:
                booking = bookings[0]
                rec.last_hotel_booking_id = booking.id
                rec.last_booking_check_in = booking.check_in_date
                rec.last_booking_check_out = booking.check_out_date
                rec.last_booking_hotel = booking.partner_id.name if booking.partner_id else ""
            else:
                rec.last_hotel_booking_id = False
                rec.last_booking_check_in = False
                rec.last_booking_check_out = False
                rec.last_booking_hotel = False

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to sync brigade_role with partner's gb_brigade_role"""
        for vals in vals_list:
            # Normalizar brigade_role si existe
            if 'brigade_role' in vals and vals.get('brigade_role'):
                normalized_role = self._normalize_brigade_role(vals['brigade_role'])
                vals['brigade_role'] = normalized_role
                
                # Actualizar el gb_brigade_role del partner
                if 'partner_id' in vals and vals['partner_id']:
                    partner = self.env['res.partner'].browse(vals['partner_id'])
                    if partner.exists():
                        partner.write({'gb_brigade_role': normalized_role})
        
        records = super().create(vals_list)
        # Renumerar después de crear
        brigades = records.mapped('brigade_id')
        for brigade in brigades:
            brigade._renumber_roster()
        return records

    def write(self, vals):
        """Override write to sync brigade_role with partner's gb_brigade_role"""
        # Normalizar brigade_role si se está actualizando
        if 'brigade_role' in vals and vals.get('brigade_role'):
            normalized_role = self._normalize_brigade_role(vals['brigade_role'])
            vals['brigade_role'] = normalized_role
            
            # Actualizar el gb_brigade_role del partner para todos los registros
            for rec in self:
                if rec.partner_id:
                    rec.partner_id.write({'gb_brigade_role': normalized_role})
        
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

# ... (rest of the file remains the same)
