# -*- coding: utf-8 -*-
# License LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import api, fields, models


class GBHotelOffer(models.Model):
    _name = "gb.hotel.offer"
    _description = "Hotel / Alojamiento para Brigadas"
    _order = "partner_id, name"

    # -----------------------------
    # Datos generales del hotel
    # -----------------------------

    name = fields.Char(
        string="Referencia / Nombre interno",
        required=True,
        help="Referencia corta para esta oferta de alojamiento."
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Proveedor / Hotel",
        required=True,
        domain="[('is_company', '=', True)]",
        help="Empresa / hotel que provee el alojamiento."
    )

    phone = fields.Char(
        string="Teléfono",
        related="partner_id.phone",
        readonly=True,
    )

    email = fields.Char(
        string="Email",
        related="partner_id.email",
        readonly=True,
    )

    street = fields.Char(
        string="Dirección",
        related="partner_id.street",
        readonly=True,
    )

    city = fields.Char(
        string="Ciudad",
        related="partner_id.city",
        readonly=True,
    )

    # -----------------------------
    # Habitaciones detalladas
    # -----------------------------

    room_line_ids = fields.One2many(
        "gb.hotel.offer.room",
        "offer_id",
        string="Habitaciones",
        help="Inventario detallado de habitaciones disponibles en este hotel."
    )

    # -----------------------------
    # Resumen calculado
    # -----------------------------

    total_rooms = fields.Integer(
        string="Total Habitaciones",
        compute="_compute_totals",
        store=False,
        help="Cantidad de habitaciones cargadas en la pestaña Habitaciones."
    )

    total_pax = fields.Integer(
        string="Total Pax (estimado)",
        compute="_compute_totals",
        store=False,
        help="Capacidad estimada sumando las habitaciones (según tipo)."
    )

    @api.depends("room_line_ids", "room_line_ids.capacity_guess")
    def _compute_totals(self):
        for rec in self:
            rooms = rec.room_line_ids
            rec.total_rooms = len(rooms)
            rec.total_pax = sum(r.capacity_guess or 0 for r in rooms)


class GBHotelOfferRoom(models.Model):
    _name = "gb.hotel.offer.room"
    _description = "Habitación ofrecida en el hotel"
    _order = "room_number, id"

    offer_id = fields.Many2one(
        "gb.hotel.offer",
        string="Oferta de Hotel",
        required=True,
        ondelete="cascade",
    )

    room_number = fields.Char(
        string="Hab./Identificador",
        required=True,
        help="Ej: 101, Cabaña 2, Bloque A - Hab 3."
    )

    room_type = fields.Selection(
        [
            ("single", "Single"),
            ("double", "Doble"),
            ("triple", "Triple"),
            ("quad", "Cuádruple"),
            ("dorm", "Compartida / Dormitorio"),
            ("other", "Otro"),
        ],
        string="Tipo",
        required=True,
        help="Clasificación rápida de la habitación.",
    )

    bed_setup = fields.Char(
        string="Camas",
        required=True,
        help="Ej: '1 matrimonial + 1 simple', '3 camas simples', 'literas 2x2'."
    )

    notes = fields.Char(
        string="Notas",
        help="Restricciones, a quién se sugiere alojar acá, etc."
    )

    capacity_guess = fields.Integer(
        string="Capacidad Estimada (pax)",
        compute="_compute_capacity_guess",
        store=False,
        help="Estimación rápida según tipo. Se usa para el total pax arriba."
    )

    @api.depends("room_type")
    def _compute_capacity_guess(self):
        """
        Estimación rápida de cuántas personas caben en esta habitación.
        Esto lo usamos sólo para el resumen total_pax.
        """
        for rec in self:
            if rec.room_type == "single":
                rec.capacity_guess = 1
            elif rec.room_type == "double":
                rec.capacity_guess = 2
            elif rec.room_type == "triple":
                rec.capacity_guess = 3
            elif rec.room_type == "quad":
                rec.capacity_guess = 4
            elif rec.room_type == "dorm":
                rec.capacity_guess = 6  # asumimos dormitorio aprox 6 pax
            else:
                rec.capacity_guess = 1  # fallback para "other"
