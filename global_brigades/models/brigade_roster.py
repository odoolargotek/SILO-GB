# -*- coding: utf-8 -*-

# LT Brigade Module - Roster Model
# Largotek SRL - Juan Luis Garvía - www.largotek.com
# License: LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import api, fields, models


class GBBrigadeRoster(models.Model):
    """Global Brigades - Roster (participants/volunteers)."""
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

    sa_notified = fields.Datetime(
        string="S.A. Notified",
        readonly=True,
        help="Date and time when the S.A. notification email was sent to the emergency contact.",
    )

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

    # =========================
    # EMERGENCY CONTACT
    # =========================
    emergency_contact_id = fields.Many2one(
        "res.partner",
        string="Emergency Contact",
        related="partner_id.gb_emergency_contact_id",
        store=False,
        readonly=True,
        help="Emergency contact automatically loaded from partner profile.",
    )

    emergency_contact_email = fields.Char(
        string="Emergency Contact Email",
        related="emergency_contact_id.email",
        store=False,
        readonly=True,
    )

    # =========================
    # OTHER INFORMATION
    # =========================
    other_information = fields.Text(
        string="Other Information",
        help="Additional information or notes about this participant (e.g., special requirements, travel details, etc.).",
    )

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

    # =========================
    # ONCHANGE METHODS
    # =========================

    @api.onchange('partner_id')
    def _onchange_partner_id_brigade_role(self):
        """
        Auto-fill brigade_role from partner's default brigade role.
        Converts the selection value to its readable label.
        """
        for rec in self:
            if rec.partner_id and rec.partner_id.gb_brigade_role:
                selection_field = self.env['res.partner']._fields.get('gb_brigade_role')
                if selection_field and hasattr(selection_field, 'selection'):
                    selection_dict = dict(selection_field.selection)
                    role_label = selection_dict.get(rec.partner_id.gb_brigade_role, rec.partner_id.gb_brigade_role)
                    rec.brigade_role = role_label

    # =========================
    # COMPUTE METHODS
    # =========================

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
        records = super().create(vals_list)
        brigades = records.mapped('brigade_id')
        for brigade in brigades:
            brigade._renumber_roster()
        return records

    def write(self, vals):
        result = super().write(vals)
        if 'sequence' in vals:
            brigades = self.mapped('brigade_id')
            for brigade in brigades:
                brigade._renumber_roster()
        return result

    def unlink(self):
        brigades = self.mapped('brigade_id')
        result = super().unlink()
        for brigade in brigades:
            brigade._renumber_roster()
        return result
