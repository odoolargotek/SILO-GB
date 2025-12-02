# -*- coding: utf-8 -*-
# License LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import api, fields, models


class GBBrigadeRooming(models.Model):
    _name = "gb.brigade.rooming"
    _description = "Global Brigades - Rooming List (asignación hotelera)"
    _order = "date_night, id"

    brigade_id = fields.Many2one(
        "gb.brigade",
        string="Brigade",
        required=True,
        ondelete="cascade",
        help="Brigade / Chapter for this rooming assignment."
    )

    hotel_offer_id = fields.Many2one(
        "gb.hotel.offer",
        string="Hotel Offer",
        required=True,
        help="Which hotel / lodging offer is being used for this brigade night.",
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Hotel (Partner)",
        related="hotel_offer_id.partner_id",
        readonly=True,
        store=False,
        help="Read-only link to the hotel partner for quick reference.",
    )

    city = fields.Char(
        string="City",
        related="hotel_offer_id.city",
        readonly=True,
        store=False,
    )

    date_night = fields.Date(
        string="Night / Check-in Date",
        required=True,
        help="Night this assignment applies to. Example: 2025-10-12 means who sleeps this night."
    )

    note = fields.Char(
        string="Notes",
        help="Special notes for staff, allergies, quiet room, etc."
    )

    line_ids = fields.One2many(
        "gb.brigade.rooming.line",
        "rooming_id",
        string="Room Assignments",
    )

    total_people = fields.Integer(
        string="# Pax",
        compute="_compute_total_people",
        store=False,
        help="How many unique people are assigned in this rooming list."
    )

    @api.depends("line_ids", "line_ids.occupant_ids")
    def _compute_total_people(self):
        for rec in self:
            seen = set()
            for line in rec.line_ids:
                for occ in line.occupant_ids:
                    seen.add(occ.id)
            rec.total_people = len(seen)


class GBBrigadeRoomingLine(models.Model):
    _name = "gb.brigade.rooming.line"
    _description = "Room Assignment Line"
    _order = "hotel_room_id, id"

    rooming_id = fields.Many2one(
        "gb.brigade.rooming",
        string="Rooming Master",
        required=True,
        ondelete="cascade",
    )

    hotel_room_id = fields.Many2one(
        "gb.hotel.offer.room",
        string="Room",
        required=True,
        domain="[('offer_id', '=', parent.hotel_offer_id)]",
        help="Pick one of the rooms defined in this hotel's offer."
    )

    room_number = fields.Char(
        string="Room # / Ref",
        related="hotel_room_id.room_number",
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

    internal_notes = fields.Char(
        string="Internal Notes",
        help="Example: 'Girls only', 'Snorer here', 'Needs A/C'."
    )

    occupant_ids = fields.Many2many(
        "gb.brigade.roster",
        "gb_rooming_roster_rel",
        "room_line_id",
        "roster_id",
        string="Occupants",
        help="Select people from the Brigade Roster that will sleep in this room."
    )

    pax_count = fields.Integer(
        string="# Pax",
        compute="_compute_pax_count",
        store=False,
    )

    @api.depends("occupant_ids")
    def _compute_pax_count(self):
        for rec in self:
            rec.pax_count = len(rec.occupant_ids)
