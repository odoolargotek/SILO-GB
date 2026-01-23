# -*- coding: utf-8 -*-
# License LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class GBBrigadeTransport(models.Model):
    _name = "gb.brigade.transport"
    _description = "Global Brigades - Brigade Transport"
    _order = "date_time, id"

    # ---------------------------------------------------------
    # Relaciones base
    # ---------------------------------------------------------
    brigade_id = fields.Many2one(
        "gb.brigade",
        string="Brigade",
        required=True,
        ondelete="cascade",
    )

    title = fields.Char(
        string="Title / Ref",
        required=True,
        help="Internal name, e.g. 'Airport → Compound - Arrival Day'.",
    )

    date_time = fields.Datetime(
        string="Date / Time",
        help="Planned date and time for this transport.",
    )

    # Proveedor del transporte
    provider_id = fields.Many2one(
        "gb.transport.provider",
        string="Transport Provider",
        help="Provider who will supply the vehicles for this movement.",
    )

    # Vehículo principal en la cabecera (informativo + usado en totales si no hay líneas)
    vehicle_id = fields.Many2one(
        "gb.transport.vehicle",
        string="Vehicle",
        domain="[('provider_id', '=', provider_id)]",
        help="Main vehicle for this transport movement.",
    )

    origin = fields.Char(
        string="Origin",
        help="Origin place or meeting point for this transport.",
    )

    destination = fields.Char(
        string="Destination",
        help="Destination place for this transport.",
    )

    notes = fields.Text(string="Notes")

    # ---------------------------------------------------------
    # Pasajeros (cabecera)
    # ---------------------------------------------------------
    passenger_ids = fields.Many2many(
        "gb.brigade.roster",
        "gb_transport_roster_rel",
        "transport_id",
        "roster_id",
        string="Passengers",
        help="Brigade roster people for this transport movement.",
    )

    staff_passenger_ids = fields.Many2many(
        "gb.brigade.staff",
        "gb_transport_staff_rel",
        "transport_id",
        "staff_id",
        string="Staff Passengers",
        help="Staff members that will travel in this transport movement.",
    )

    # Lista combinada de todos los pasajeros (Roster + Staff) como partners
    transport_passenger_partner_ids = fields.Many2many(
        "res.partner",
        "gb_transport_passenger_partner_rel",
        "transport_id",
        "partner_id",
        string="All Passengers",
        compute="_compute_transport_passenger_partner_ids",
        store=False,
        readonly=True,
        help="Combined list of all passengers (Roster + Staff) as partners.",
    )

    @api.depends("passenger_ids.partner_id", "staff_passenger_ids.person_id")
    def _compute_transport_passenger_partner_ids(self):
        for rec in self:
            roster_partners = rec.passenger_ids.mapped("partner_id")
            staff_partners = rec.staff_passenger_ids.mapped("person_id")
            rec.transport_passenger_partner_ids = roster_partners | staff_partners


    n_pax = fields.Integer(
        string="# Pax",
        compute="_compute_n_pax",
        store=False,
    )

    # ---------------------------------------------------------
    # Vehículos (líneas) y totales
    # ---------------------------------------------------------
    vehicle_line_ids = fields.One2many(
        "gb.brigade.transport.line",
        "transport_id",
        string="Vehicle Assignments",
        copy=True,
    )

    vehicle_count = fields.Integer(
        string="# Vehicles",
        compute="_compute_totals",
        store=False,
    )

    total_seats = fields.Integer(
        string="Total Seats",
        compute="_compute_totals",
        store=False,
    )

    total_assigned_pax = fields.Integer(
        string="Assigned Pax",
        compute="_compute_totals",
        store=False,
    )

    remaining_seats = fields.Integer(
        string="Free Seats",
        compute="_compute_totals",
        store=False,
    )

    # ---------------------------------------------------------
    # Cálculos
    # ---------------------------------------------------------
    @api.depends("passenger_ids", "staff_passenger_ids")
    def _compute_n_pax(self):
        for rec in self:
            rec.n_pax = len(rec.passenger_ids) + len(rec.staff_passenger_ids)

    @api.depends("passenger_ids.partner_id", "staff_passenger_ids.person_id")
    def _compute_transport_passenger_partner_ids(self):
        """
        Construye una lista combinada de contactos (res.partner)
        a partir de:
        - passenger_ids.partner_id  (roster)
        - staff_passenger_ids.person_id  (staff)
        Solo para visualización (read-only).
        """
        for rec in self:
            partners = self.env["res.partner"]
            if rec.passenger_ids:
                partners |= rec.passenger_ids.mapped("partner_id")
            if rec.staff_passenger_ids:
                partners |= rec.staff_passenger_ids.mapped("person_id")
            rec.transport_passenger_partner_ids = partners

    @api.depends(
        "vehicle_line_ids.capacity",
        "vehicle_line_ids.total_pax",
        "vehicle_id.capacity",
        "n_pax",
    )
    def _compute_totals(self):
        """
        Si hay líneas de vehículo, usamos esas.
        Si no hay líneas, usamos el vehículo de cabecera (vehicle_id).
        """
        for rec in self:
            if rec.vehicle_line_ids:
                vehicles = rec.vehicle_line_ids
                total_seats = sum(vehicles.mapped("capacity"))
                total_pax = sum(vehicles.mapped("total_pax"))
                rec.vehicle_count = len(vehicles)
                rec.total_seats = total_seats
                rec.total_assigned_pax = total_pax
                rec.remaining_seats = max(total_seats - total_pax, 0)
            else:
                capacity = rec.vehicle_id.capacity or 0 if rec.vehicle_id else 0
                rec.vehicle_count = 1 if rec.vehicle_id else 0
                rec.total_seats = capacity
                rec.total_assigned_pax = rec.n_pax
                rec.remaining_seats = max(capacity - rec.n_pax, 0)

    # ---------------------------------------------------------
    # Onchanges ligeros
    # ---------------------------------------------------------
    @api.onchange("vehicle_id")
    def _onchange_vehicle_id(self):
        """Si elegimos vehículo con proveedor, sincronizamos provider_id."""
        for rec in self:
            if rec.vehicle_id and rec.vehicle_id.provider_id:
                rec.provider_id = rec.vehicle_id.provider_id

    # ---------------------------------------------------------
    # Wizard de pasajeros (Roster + Staff)
    # ---------------------------------------------------------
    def action_open_passenger_wizard(self):
        """Open passenger selection wizard (reuses gb.passenger.list.wizard)."""
        self.ensure_one()
        if not self.brigade_id or not (
            self.brigade_id.roster_ids or self.brigade_id.staff_ids
        ):
            raise UserError(
                _(
                    "The brigade roster is empty.\n\n"
                    "First add participants in the 'ROSTER' tab and/or "
                    "temporary staff in the 'Temp Staff' tab, "
                    "and then reopen the passenger list."
                )
            )
        return {
            "type": "ir.actions.act_window",
            "name": _("Passenger list"),
            "res_model": "gb.passenger.list.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_brigade_id": self.brigade_id.id,
                "default_passenger_ids": [(6, 0, self.passenger_ids.ids)],
                "default_staff_ids": [(6, 0, self.staff_passenger_ids.ids)],
            },
        }

    def action_add_all_passengers(self):
        """Add the whole brigade roster + staff to this transport movement."""
        for rec in self:
            if rec.brigade_id:
                rec.passenger_ids = [(6, 0, rec.brigade_id.roster_ids.ids)]
                rec.staff_passenger_ids = [(6, 0, rec.brigade_id.staff_ids.ids)]
        return True


class GBBrigadeTransportLine(models.Model):
    _name = "gb.brigade.transport.line"
    _description = "Global Brigades - Transport Vehicle Assignment"
    _order = "sequence, id"

    transport_id = fields.Many2one(
        "gb.brigade.transport",
        string="Transport",
        required=True,
        ondelete="cascade",
    )

    sequence = fields.Integer(string="Sequence", default=10)

    vehicle_id = fields.Many2one(
        "gb.transport.vehicle",
        string="Vehicle",
        required=True,
        help="Vehicle used for this transport.",
    )

    provider_id = fields.Many2one(
        "gb.transport.provider",
        related="vehicle_id.provider_id",
        string="Provider",
        store=False,
        readonly=True,
    )

    capacity = fields.Integer(
        string="Capacity",
        related="vehicle_id.capacity",
        store=False,
        readonly=True,
    )

    roster_passenger_ids = fields.Many2many(
        "gb.brigade.roster",
        "gb_transport_line_roster_rel",
        "line_id",
        "roster_id",
        string="Roster Passengers",
        domain="[('id', 'in', available_roster_ids)]",
        help="Brigade roster people assigned to this vehicle.",
    )

    # Campo computado para filtrar roster ya asignados
    available_roster_ids = fields.Many2many(
        "gb.brigade.roster",
        compute="_compute_available_roster_ids",
        store=False,
        help="Roster members not yet assigned to other vehicles in this transport.",
    )

    staff_passenger_ids = fields.Many2many(
        "gb.brigade.staff",
        "gb_transport_line_staff_rel",
        "line_id",
        "staff_id",
        string="Staff Passengers",
        domain="[('id', 'in', available_staff_ids)]",
        help="Staff members assigned to this vehicle.",
    )

    # Campo computado para filtrar staff ya asignados
    available_staff_ids = fields.Many2many(
        "gb.brigade.staff",
        compute="_compute_available_staff_ids",
        store=False,
        help="Staff members not yet assigned to other vehicles in this transport.",
    )

    total_pax = fields.Integer(
        string="Total Pax",
        compute="_compute_total_pax",
        store=False,
    )

    remaining_seats = fields.Integer(
        string="Free Seats",
        compute="_compute_remaining_seats",
        store=False,
    )

    @api.depends("roster_passenger_ids", "staff_passenger_ids")
    def _compute_total_pax(self):
        for rec in self:
            rec.total_pax = len(rec.roster_passenger_ids) + len(rec.staff_passenger_ids)

    @api.depends("capacity", "total_pax")
    def _compute_remaining_seats(self):
        for rec in self:
            capacity = rec.capacity or 0
            rec.remaining_seats = max(capacity - (rec.total_pax or 0), 0)

    @api.depends(
        "transport_id",
        "transport_id.brigade_id",
        "transport_id.brigade_id.roster_ids",
        "transport_id.vehicle_line_ids",
        "transport_id.vehicle_line_ids.roster_passenger_ids",
        "roster_passenger_ids",
    )
    def _compute_available_roster_ids(self):
        """
        Filtra el roster disponible:
        - Todos los del roster de la brigada
        - MENOS los ya asignados en OTRAS líneas de vehículo de este transporte
        - MÁS los pasajeros actuales (para poder editarlos)
        """
        for rec in self:
            if not rec.transport_id or not rec.transport_id.brigade_id:
                rec.available_roster_ids = self.env["gb.brigade.roster"]
                continue

            # Todo el roster de la brigada
            all_roster = rec.transport_id.brigade_id.roster_ids

            # Ya asignados en OTRAS líneas de vehículo
            other_lines = rec.transport_id.vehicle_line_ids.filtered(lambda line: line.id != rec.id)
            already_assigned = other_lines.mapped("roster_passenger_ids")

            # Disponibles = Todos - Ya asignados + Pasajeros actuales
            available = (all_roster - already_assigned) | rec.roster_passenger_ids
            rec.available_roster_ids = available

    @api.depends(
        "transport_id",
        "transport_id.brigade_id",
        "transport_id.brigade_id.staff_ids",
        "transport_id.vehicle_line_ids",
        "transport_id.vehicle_line_ids.staff_passenger_ids",
        "staff_passenger_ids",
    )
    def _compute_available_staff_ids(self):
        """
        Filtra el staff disponible:
        - Todos los del staff de la brigada
        - MENOS los ya asignados en OTRAS líneas de vehículo de este transporte
        - MÁS los pasajeros actuales (para poder editarlos)
        """
        for rec in self:
            if not rec.transport_id or not rec.transport_id.brigade_id:
                rec.available_staff_ids = self.env["gb.brigade.staff"]
                continue

            # Todo el staff de la brigada
            all_staff = rec.transport_id.brigade_id.staff_ids

            # Ya asignados en OTRAS líneas de vehículo
            other_lines = rec.transport_id.vehicle_line_ids.filtered(lambda line: line.id != rec.id)
            already_assigned = other_lines.mapped("staff_passenger_ids")

            # Disponibles = Todos - Ya asignados + Pasajeros actuales
            available = (all_staff - already_assigned) | rec.staff_passenger_ids
            rec.available_staff_ids = available
