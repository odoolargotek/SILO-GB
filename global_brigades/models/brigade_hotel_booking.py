# -*- coding: utf-8 -*-
# License LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import api, fields, models


class GBBrigadeHotelBooking(models.Model):
    _name = "gb.brigade.hotel.booking"
    _description = "Brigade Hotel Booking / Rooming Assignment"
    _order = "check_in_date, id"

    # -----------------
    # Relaciones base
    # -----------------
    brigade_id = fields.Many2one(
        "gb.brigade",
        string="Brigade",
        required=True,
        ondelete="cascade",
    )
    hotel_offer_id = fields.Many2one(
        "gb.hotel.offer",
        string="Hotel Offer",
        required=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Hotel (Partner)",
        related="hotel_offer_id.partner_id",
        readonly=True,
        store=False,
    )
    city = fields.Char(
        string="City",
        related="hotel_offer_id.city",
        readonly=True,
        store=False,
    )

    # -----------------
    # Fechas / notas
    # -----------------
    check_in_date = fields.Date(string="Check In", required=True)
    check_out_date = fields.Date(string="Check Out", required=True)
    stay_nights = fields.Integer(
        string="Nights",
        compute="_compute_stay_nights",
        store=False,
    )
    note = fields.Char(string="Notes")

    # -----------------
    # Líneas de asignación (ROSTER)
    # -----------------
    assignment_ids = fields.One2many(
        "gb.brigade.hotel.booking.line",
        "booking_id",
        string="Room Assignments (Roster)",
        copy=True,
    )

    # -----------------
    # Líneas de asignación (STAFF)
    # -----------------
    staff_assignment_ids = fields.One2many(
        "gb.brigade.hotel.booking.staff.line",
        "booking_id",
        string="Room Assignments (Staff)",
        copy=True,
    )

    # -----------------
    # Métricas ROSTER
    # -----------------
    roster_total = fields.Integer(string="Roster Total", compute="_compute_totals_all", store=False)
    assigned_people = fields.Integer(string="Assigned (Roster)", compute="_compute_totals_all", store=False)
    unassigned_people = fields.Integer(string="Not Assigned (Roster)", compute="_compute_totals_all", store=False)

    # -----------------
    # Métricas STAFF
    # -----------------
    staff_roster_total = fields.Integer(string="Roster Total (Staff)", compute="_compute_totals_all", store=False)
    staff_assigned_people = fields.Integer(string="Assigned (Staff)", compute="_compute_totals_all", store=False)
    staff_unassigned_people = fields.Integer(string="Not Assigned (Staff)", compute="_compute_totals_all", store=False)

    # -----------------
    # Métricas TOTALES (Roster + Staff)
    # -----------------
    total_headcount = fields.Integer(string="Roster Total (All)", compute="_compute_totals_all", store=False)
    total_assigned_people = fields.Integer(string="Assigned (All)", compute="_compute_totals_all", store=False)
    total_unassigned_people = fields.Integer(string="Not Assigned (All)", compute="_compute_totals_all", store=False)

    # -----------------
    # Displays A/T para la vista de Brigada -> Hoteles/Rooming
    # -----------------
    roster_assigned_total_display = fields.Char(
        string="Roster (A/T)",
        compute="_compute_totals_all",
        store=False,
        help="Assigned/Total for roster, e.g., 3/9",
    )
    staff_assigned_total_display = fields.Char(
        string="Staff (A/T)",
        compute="_compute_totals_all",
        store=False,
        help="Assigned/Total for staff, e.g., 2/6",
    )
    overall_assigned_total_display = fields.Char(
        string="Total (A/T)",
        compute="_compute_totals_all",
        store=False,
        help="Assigned/Total overall, e.g., 5/15",
    )

    # -----------------
    # Cómputos
    # -----------------
    def _compute_stay_nights(self):
        for rec in self:
            nights = 0
            if rec.check_in_date and rec.check_out_date:
                delta = fields.Date.from_string(rec.check_out_date) - fields.Date.from_string(rec.check_in_date)
                nights = delta.days if delta.days > 0 else 0
            rec.stay_nights = nights

    @api.depends(
        "brigade_id",
        "brigade_id.roster_ids",
        "brigade_id.staff_ids",
        "assignment_ids",
        "assignment_ids.occupant_ids",
        "staff_assignment_ids",
        "staff_assignment_ids.occupant_staff_ids",
    )
    def _compute_totals_all(self):
        """
        Calcula métricas separadas para Roster y Staff, y luego Totales,
        y alimenta los displays A/T para usar en la vista de brigada.
        """
        for rec in self:
            # --- ROSTER ---
            brigade_roster = rec.brigade_id.roster_ids if rec.brigade_id else self.env["gb.brigade.roster"]
            roster_all_ids = set(brigade_roster.ids)

            roster_assigned_ids = set()
            for line in rec.assignment_ids:
                roster_assigned_ids.update(line.occupant_ids.ids)

            rec.roster_total = len(roster_all_ids)
            rec.assigned_people = len(roster_assigned_ids)
            rec.unassigned_people = max(rec.roster_total - rec.assigned_people, 0)

            # --- STAFF ---
            brigade_staff = rec.brigade_id.staff_ids if rec.brigade_id else self.env["gb.brigade.staff"]
            staff_all_ids = set(brigade_staff.ids)

            staff_assigned_ids = set()
            for sline in rec.staff_assignment_ids:
                staff_assigned_ids.update(sline.occupant_staff_ids.ids)

            rec.staff_roster_total = len(staff_all_ids)
            rec.staff_assigned_people = len(staff_assigned_ids)
            rec.staff_unassigned_people = max(rec.staff_roster_total - rec.staff_assigned_people, 0)

            # --- TOTALES ---
            rec.total_headcount = rec.roster_total + rec.staff_roster_total
            rec.total_assigned_people = rec.assigned_people + rec.staff_assigned_people
            rec.total_unassigned_people = rec.unassigned_people + rec.staff_unassigned_people

            # --- DISPLAYS A/T ---
            rec.roster_assigned_total_display = f"{rec.assigned_people}/{rec.roster_total}"
            rec.staff_assigned_total_display = f"{rec.staff_assigned_people}/{rec.staff_roster_total}"
            rec.overall_assigned_total_display = f"{rec.total_assigned_people}/{rec.total_headcount}"

    # -----------------
    # Botones/Acciones
    # -----------------
    def action_open_rooming_detail(self):
        """
        Abre el formulario en modal desde la lista de 'Hoteles / Rooming' de la brigada.
        """
        self.ensure_one()
        view = self.env.ref("global_brigades.view_gb_brigade_hotel_booking_form")
        return {
            "type": "ir.actions.act_window",
            "name": "Rooming Assignment",
            "res_model": "gb.brigade.hotel.booking",
            "view_mode": "form",
            "view_id": view.id,
            "res_id": self.id,
            "target": "new",
            "context": {"form_view_initial_mode": "edit"},
        }

    def action_save_and_close(self):
        """
        Botón 'Guardar' del modal: el form ya hace write antes de entrar aquí.
        Solo cerramos la ventana.
        """
        self.ensure_one()
        return {"type": "ir.actions.act_window_close"}


class GBBrigadeHotelBookingLine(models.Model):
    _name = "gb.brigade.hotel.booking.line"
    _description = "Room Assignment for a Brigade Hotel Stay (Roster)"
    _order = "hotel_room_id, id"

    booking_id = fields.Many2one(
        "gb.brigade.hotel.booking",
        string="Hotel Booking",
        required=True,
        ondelete="cascade",
        help="Parent hotel stay block.",
    )

    hotel_room_id = fields.Many2one(
        "gb.hotel.offer.room",
        string="Room",
        required=True,
        domain="[('offer_id', '=', parent.hotel_offer_id), ('id', 'in', available_room_ids)]",
        help="Room from the selected Hotel Offer.",
    )

    room_number = fields.Char(
        related="hotel_room_id.room_number",
        string="Room #",
        readonly=True,
        store=False,
    )
    room_type = fields.Selection(
        related="hotel_room_id.room_type",
        string="Type",
        readonly=True,
        store=False,
    )
    bed_setup = fields.Char(
        related="hotel_room_id.bed_setup",
        string="Beds",
        readonly=True,
        store=False,
    )

    occupant_ids = fields.Many2many(
        "gb.brigade.roster",
        "gb_brigade_hotel_booking_line_roster_rel",
        "line_id",
        "roster_id",
        string="Occupants",
        domain="[('id', 'in', available_roster_ids)]",
        help="People from this Brigade's Roster that will sleep in this room for this stay.",
    )

    # Campo computado para filtrar roster ya asignados
    available_roster_ids = fields.Many2many(
        "gb.brigade.roster",
        compute="_compute_available_roster_ids",
        store=False,
        help="Roster members not yet assigned to other rooms in this booking.",
    )

    # Campo computado para filtrar habitaciones ya asignadas
    available_room_ids = fields.Many2many(
        "gb.hotel.offer.room",
        compute="_compute_available_room_ids",
        store=False,
        help="Rooms not yet assigned to other lines in this booking (Roster + Staff).",
    )

    pax_count = fields.Integer(
        string="# Pax",
        compute="_compute_pax_count",
        store=False,
        help="How many people are in this room.",
    )

    @api.depends("occupant_ids")
    def _compute_pax_count(self):
        for rec in self:
            rec.pax_count = len(rec.occupant_ids)

    @api.depends(
        "booking_id",
        "booking_id.brigade_id",
        "booking_id.brigade_id.roster_ids",
        "booking_id.assignment_ids",
        "booking_id.assignment_ids.occupant_ids",
        "occupant_ids",
    )
    def _compute_available_roster_ids(self):
        """
        Filtra el roster disponible:
        - Todos los del roster de la brigada
        - MENOS los ya asignados en OTRAS líneas de este booking
        - MÁS los ocupantes actuales (para poder editarlos)
        """
        for rec in self:
            if not rec.booking_id or not rec.booking_id.brigade_id:
                rec.available_roster_ids = self.env["gb.brigade.roster"]
                continue

            # Todo el roster de la brigada
            all_roster = rec.booking_id.brigade_id.roster_ids

            # Ya asignados en OTRAS líneas
            other_lines = rec.booking_id.assignment_ids.filtered(lambda line: line.id != rec.id)
            already_assigned = other_lines.mapped("occupant_ids")

            # Disponibles = Todos - Ya asignados + Ocupantes actuales
            available = (all_roster - already_assigned) | rec.occupant_ids
            rec.available_roster_ids = available

    @api.depends(
        "booking_id",
        "booking_id.hotel_offer_id",
        "booking_id.hotel_offer_id.room_ids",
        "booking_id.assignment_ids",
        "booking_id.assignment_ids.hotel_room_id",
        "booking_id.staff_assignment_ids",
        "booking_id.staff_assignment_ids.hotel_room_id",
        "hotel_room_id",
    )
    def _compute_available_room_ids(self):
        """
        Filtra las habitaciones disponibles:
        - Todas las habitaciones del hotel offer
        - MENOS las ya asignadas en OTRAS líneas de Roster
        - MENOS las ya asignadas en líneas de Staff
        - MÁS la habitación actual (para poder editarla)
        """
        for rec in self:
            if not rec.booking_id or not rec.booking_id.hotel_offer_id:
                rec.available_room_ids = self.env["gb.hotel.offer.room"]
                continue

            # Todas las habitaciones del hotel offer
            all_rooms = rec.booking_id.hotel_offer_id.room_ids

            # Ya asignadas en OTRAS líneas de Roster (no esta)
            other_roster_lines = rec.booking_id.assignment_ids.filtered(lambda line: line.id != rec.id)
            already_assigned_roster = other_roster_lines.mapped("hotel_room_id")

            # Ya asignadas en líneas de Staff
            already_assigned_staff = rec.booking_id.staff_assignment_ids.mapped("hotel_room_id")

            # Ya asignadas = unión de ambas
            already_assigned = already_assigned_roster | already_assigned_staff

            # Disponibles = Todas - Ya asignadas + Habitación actual
            available = (all_rooms - already_assigned) | rec.hotel_room_id
            rec.available_room_ids = available


class GBBrigadeHotelBookingStaffLine(models.Model):
    _name = "gb.brigade.hotel.booking.staff.line"
    _description = "Room Assignment for a Brigade Hotel Stay (Staff)"
    _order = "hotel_room_id, id"

    booking_id = fields.Many2one(
        "gb.brigade.hotel.booking",
        string="Hotel Booking",
        required=True,
        ondelete="cascade",
    )

    hotel_room_id = fields.Many2one(
        "gb.hotel.offer.room",
        string="Room",
        required=True,
        domain="[('offer_id', '=', parent.hotel_offer_id), ('id', 'in', available_room_ids)]",
        help="Room from the selected Hotel Offer.",
    )

    room_number = fields.Char(
        related="hotel_room_id.room_number",
        string="Room #",
        readonly=True,
        store=False,
    )
    room_type = fields.Selection(
        related="hotel_room_id.room_type",
        string="Type",
        readonly=True,
        store=False,
    )
    bed_setup = fields.Char(
        related="hotel_room_id.bed_setup",
        string="Beds",
        readonly=True,
        store=False,
    )

    occupant_staff_ids = fields.Many2many(
        "gb.brigade.staff",
        "gb_brigade_hotel_booking_staff_line_rel",
        "line_id",
        "staff_id",
        string="Occupants",
        domain="[('id', 'in', available_staff_ids)]",
        help="Temporary staff that will sleep in this room for this stay.",
    )

    # Campo computado para filtrar staff ya asignados
    available_staff_ids = fields.Many2many(
        "gb.brigade.staff",
        compute="_compute_available_staff_ids",
        store=False,
        help="Staff members not yet assigned to other rooms in this booking.",
    )

    # Campo computado para filtrar habitaciones ya asignadas
    available_room_ids = fields.Many2many(
        "gb.hotel.offer.room",
        compute="_compute_available_room_ids",
        store=False,
        help="Rooms not yet assigned to other lines in this booking (Staff + Roster).",
    )

    pax_count = fields.Integer(
        string="# Pax",
        compute="_compute_pax_count",
        store=False,
    )

    @api.depends("occupant_staff_ids")
    def _compute_pax_count(self):
        for rec in self:
            rec.pax_count = len(rec.occupant_staff_ids)

    @api.depends(
        "booking_id",
        "booking_id.brigade_id",
        "booking_id.brigade_id.staff_ids",
        "booking_id.staff_assignment_ids",
        "booking_id.staff_assignment_ids.occupant_staff_ids",
        "occupant_staff_ids",
    )
    def _compute_available_staff_ids(self):
        """
        Filtra el staff disponible:
        - Todos los del staff de la brigada
        - MENOS los ya asignados en OTRAS líneas de este booking
        - MÁS los ocupantes actuales (para poder editarlos)
        """
        for rec in self:
            if not rec.booking_id or not rec.booking_id.brigade_id:
                rec.available_staff_ids = self.env["gb.brigade.staff"]
                continue

            # Todo el staff de la brigada
            all_staff = rec.booking_id.brigade_id.staff_ids

            # Ya asignados en OTRAS líneas
            other_lines = rec.booking_id.staff_assignment_ids.filtered(lambda line: line.id != rec.id)
            already_assigned = other_lines.mapped("occupant_staff_ids")

            # Disponibles = Todos - Ya asignados + Ocupantes actuales
            available = (all_staff - already_assigned) | rec.occupant_staff_ids
            rec.available_staff_ids = available

    @api.depends(
        "booking_id",
        "booking_id.hotel_offer_id",
        "booking_id.hotel_offer_id.room_ids",
        "booking_id.assignment_ids",
        "booking_id.assignment_ids.hotel_room_id",
        "booking_id.staff_assignment_ids",
        "booking_id.staff_assignment_ids.hotel_room_id",
        "hotel_room_id",
    )
    def _compute_available_room_ids(self):
        """
        Filtra las habitaciones disponibles:
        - Todas las habitaciones del hotel offer
        - MENOS las ya asignadas en líneas de Roster
        - MENOS las ya asignadas en OTRAS líneas de Staff (no esta)
        - MÁS la habitación actual (para poder editarla)
        """
        for rec in self:
            if not rec.booking_id or not rec.booking_id.hotel_offer_id:
                rec.available_room_ids = self.env["gb.hotel.offer.room"]
                continue

            # Todas las habitaciones del hotel offer
            all_rooms = rec.booking_id.hotel_offer_id.room_ids

            # Ya asignadas en líneas de Roster
            already_assigned_roster = rec.booking_id.assignment_ids.mapped("hotel_room_id")

            # Ya asignadas en OTRAS líneas de Staff (no esta)
            other_staff_lines = rec.booking_id.staff_assignment_ids.filtered(lambda line: line.id != rec.id)
            already_assigned_staff = other_staff_lines.mapped("hotel_room_id")

            # Ya asignadas = unión de ambas
            already_assigned = already_assigned_roster | already_assigned_staff

            # Disponibles = Todas - Ya asignadas + Habitación actual
            available = (all_rooms - already_assigned) | rec.hotel_room_id
            rec.available_room_ids = available
