# -*- coding: utf-8 -*-
# License LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import api, fields, models, _
from odoo.exceptions import UserError


def _time_slots_15min():
    """Genera slots de hora cada 15 minutos: 00:00, 00:15, ..., 23:45"""
    slots = []
    for h in range(24):
        for m in range(0, 60, 15):
            val = f"{h:02d}:{m:02d}"
            slots.append((val, val))
    return slots


class GBBrigadeTransport(models.Model):
    _name = "gb.brigade.transport"
    _description = "Global Brigades - Brigade Transport"
    _order = "date, time_slot, id"

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
        help="Internal name, e.g. 'Airport -> Compound - Arrival Day'.",
    )

    # ----------------------------------------------------------
    # CAMPO LEGADO - conservado para no perder datos historicos
    # Se puede eliminar en version 18.0.1.0.7 tras confirmar
    # que la migracion fue exitosa.
    # ----------------------------------------------------------
    date_time = fields.Datetime(
        string="Date/Time (legacy)",
        help="Deprecated. Use 'date' + 'time_slot' instead. Kept for migration safety.",
    )

    # ----------------------------------------------------------
    # NUEVOS CAMPOS: fecha y hora separados, sin timezone
    # ----------------------------------------------------------
    date = fields.Date(
        string="Date",
        help="Transport date in Panama time. Not affected by user timezone.",
    )

    time_slot = fields.Selection(
        selection=_time_slots_15min(),
        string="Time (Panama)",
        help="Departure/arrival time in Panama time (UTC-5). "
             "This value is never recalculated or shifted by timezone profiles.",
    )

    date_time_display = fields.Char(
        string="Date / Time",
        compute="_compute_date_time_display",
        store=True,
        readonly=True,
        help="Combined date and time for display and ordering.",
    )

    @api.depends("date", "time_slot")
    def _compute_date_time_display(self):
        for rec in self:
            if rec.date and rec.time_slot:
                rec.date_time_display = f"{rec.date} {rec.time_slot}"
            elif rec.date:
                rec.date_time_display = str(rec.date)
            else:
                rec.date_time_display = False

    # Proveedor del transporte
    provider_id = fields.Many2one(
        "gb.transport.provider",
        string="Transport Provider",
        help="Provider who will supply the vehicles for this movement.",
    )

    # Vehiculo principal en la cabecera (informativo + usado en totales si no hay lineas)
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

    n_pax = fields.Integer(
        string="# Pax",
        compute="_compute_n_pax",
        store=False,
    )

    # ---------------------------------------------------------
    # Vehiculos (lineas) y totales
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
    # Calculos
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
        Solo para visualizacion (read-only).
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
        Si hay lineas de vehiculo, usamos esas.
        Si no hay lineas, usamos el vehiculo de cabecera (vehicle_id).
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
        """Si elegimos vehiculo con proveedor, sincronizamos provider_id."""
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
        - MENOS los ya asignados en OTRAS lineas de vehiculo de este transporte
        - MAS los pasajeros actuales (para poder editarlos)
        """
        for rec in self:
            if not rec.transport_id or not rec.transport_id.brigade_id:
                rec.available_roster_ids = self.env["gb.brigade.roster"]
                continue

            all_roster = rec.transport_id.brigade_id.roster_ids
            other_lines = rec.transport_id.vehicle_line_ids.filtered(lambda line: line.id != rec.id)
            already_assigned = other_lines.mapped("roster_passenger_ids")
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
        - MENOS los ya asignados en OTRAS lineas de vehiculo de este transporte
        - MAS los pasajeros actuales (para poder editarlos)
        """
        for rec in self:
            if not rec.transport_id or not rec.transport_id.brigade_id:
                rec.available_staff_ids = self.env["gb.brigade.staff"]
                continue

            all_staff = rec.transport_id.brigade_id.staff_ids
            other_lines = rec.transport_id.vehicle_line_ids.filtered(lambda line: line.id != rec.id)
            already_assigned = other_lines.mapped("staff_passenger_ids")
            available = (all_staff - already_assigned) | rec.staff_passenger_ids
            rec.available_staff_ids = available
