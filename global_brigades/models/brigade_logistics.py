# -*- coding: utf-8 -*-

# LT Brigade Module - Logistics Models (Arrivals & Departures)
# Largotek SRL - Juan Luis Garvía - www.largotek.com
# License: LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import api, fields, models, _


class GBBrigadeArrival(models.Model):
    """Global Brigades - Arrival Info (Warning only, no blocking)."""
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

    @api.onchange("passenger_ids")
    def _onchange_passenger_ids_duplicates(self):
        """Warning only (no constraint). User can still save."""
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


class GBBrigadeDeparture(models.Model):
    """Global Brigades - Departure Info (Warning only, no blocking)."""
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

    @api.onchange("passenger_ids")
    def _onchange_passenger_ids_duplicates(self):
        """Warning only (no constraint). User can still save."""
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
