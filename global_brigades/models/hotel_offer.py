# -*- coding: utf-8 -*-

# License LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import api, fields, models, _


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
        help="Referencia corta para esta oferta de alojamiento.",
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Proveedor / Hotel",
        required=True,
        domain="[('is_company', '=', True)]",
        help="Empresa / hotel que provee el alojamiento.",
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
        help="Inventario detallado de habitaciones disponibles en este hotel.",
    )

    # -----------------------------
    # Resumen calculado
    # -----------------------------
    total_rooms = fields.Integer(
        string="Total Habitaciones",
        compute="_compute_totals",
        store=False,
        help="Cantidad de habitaciones cargadas en la pestaña Habitaciones.",
    )

    total_pax = fields.Integer(
        string="Total Pax (estimado)",
        compute="_compute_totals",
        store=False,
        help="Suma de Pax por habitación.",
    )

    @api.depends("room_line_ids", "room_line_ids.pax_per_room")
    def _compute_totals(self):
        """Suma simple de pax_per_room."""
        for rec in self:
            rooms = rec.room_line_ids
            rec.total_rooms = len(rooms)
            rec.total_pax = sum((r.pax_per_room or 0) for r in rooms)


class GBHotelOfferRoom(models.Model):
    _name = "gb.hotel.offer.room"
    _description = "Habitación ofrecida en el hotel"
    _order = "sequence, room_number, id"
    _rec_name = "room_number"  # Usar Hab./Identificador como nombre visible

    offer_id = fields.Many2one(
        "gb.hotel.offer",
        string="Oferta de Hotel",
        required=True,
        ondelete="cascade",
    )

    # Para ordenar con drag & drop en la lista
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Orden manual de la habitación dentro de la oferta.",
    )

    room_number = fields.Char(
        string="Hab./Identificador",
        required=True,
        help="Ej: 101, Cabaña 2, Bloque A - Hab 3.",
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
        string="Camas (detalle)",
        help="Texto libre: '3 camas simples', '1 matrimonial + 1 simple', etc.",
    )

    # NUEVO: campo manual de capacidad
    pax_per_room = fields.Integer(
        string="Pax por habitación",
        help="Número de personas que se planea alojar en esta habitación.",
    )

    notes = fields.Char(
        string="Notas",
        help="Restricciones, a quién se sugiere alojar acá, etc.",
    )

    def name_get(self):
        """
        Mostrar un nombre amigable en los Many2one:
        por defecto, solo Hab./Identificador (room_number).
        """
        result = []
        for rec in self:
            name = rec.room_number or _("Room")
            result.append((rec.id, name))
        return result
