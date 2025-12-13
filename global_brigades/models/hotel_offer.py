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
        help="Capacidad estimada sumando las habitaciones.",
    )

    @api.depends("room_line_ids", "room_line_ids.capacity_guess")
    def _compute_totals(self):
        """
        Suma simple de la capacidad estimada de cada habitación.
        """
        for rec in self:
            rooms = rec.room_line_ids
            rec.total_rooms = len(rooms)
            rec.total_pax = sum((r.capacity_guess or 0) for r in rooms)


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

    # Texto libre donde el usuario escribe: "10", "12 camas", etc.
    bed_setup = fields.Char(
        string="Camas (detalle)",
        help="Ej: '1', '2', '3 camas simples', '1 matrimonial + 1 simple', etc.",
    )

    # Número de camas (técnico, sincronizado con bed_setup)
    beds = fields.Integer(
        string="Beds",
        help="Número de camas reales en la habitación, extraído de 'Camas (detalle)'.",
    )

    # Capacidad estimada usada para el total
    capacity_guess = fields.Integer(
        string="Capacidad Estimada (pax)",
        compute="_compute_capacity_guess",
        store=False,
        help="Capacidad estimada según el número escrito en 'Camas (detalle)'.",
    )

    notes = fields.Char(
        string="Notas",
        help="Restricciones, a quién se sugiere alojar acá, etc.",
    )

    @api.depends("bed_setup")
    def _compute_capacity_guess(self):
        """
        La capacidad estimada es el primer número que aparezca en 'Camas (detalle)'.
        Si no hay número, la capacidad se queda en 0.
        """
        for rec in self:
            rec.capacity_guess = 0
            if not rec.bed_setup:
                continue
            digits = "".join(ch if ch.isdigit() else " " for ch in rec.bed_setup)
            parts = [p for p in digits.split() if p]
            if parts:
                try:
                    rec.capacity_guess = int(parts[0])
                except ValueError:
                    rec.capacity_guess = 0

    @api.onchange("bed_setup")
    def _onchange_bed_setup_set_beds(self):
        """
        Mantiene 'beds' sincronizado con el primer número de 'Camas (detalle)'.
        Sirve solo como ayuda visual; el total se calcula con capacity_guess.
        """
        for rec in self:
            rec.beds = 0
            if not rec.bed_setup:
                continue
            digits = "".join(ch if ch.isdigit() else " " for ch in rec.bed_setup)
            parts = [p for p in digits.split() if p]
            if parts:
                try:
                    rec.beds = int(parts[0])
                except ValueError:
                    rec.beds = 0

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
