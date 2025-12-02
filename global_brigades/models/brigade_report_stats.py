# -*- coding: utf-8 -*-
# License LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import models, fields, api


class GBBrigadeReportStats(models.Model):
    _inherit = "gb.brigade"

    # Comunidades cubiertas por la brigada (desde las líneas de programa)
    community_names = fields.Char(
        string="Communities",
        compute="_compute_community_names",
        store=False,
    )

    # Contadores de vuelos
    arrival_count = fields.Integer(
        string="# Arrivals",
        compute="_compute_flight_counts",
        store=False,
    )
    departure_count = fields.Integer(
        string="# Departures",
        compute="_compute_flight_counts",
        store=False,
    )

    # Estadísticas de hoteles / rooming
    hotel_booking_count = fields.Integer(
        string="# Hotel Blocks",
        compute="_compute_hotel_stats",
        store=False,
    )
    total_stay_nights = fields.Integer(
        string="Total Nights",
        compute="_compute_hotel_stats",
        store=False,
        help="Total number of nights across all hotel bookings for this brigade.",
    )

    # Staff: totales y por tipo
    staff_count = fields.Integer(
        string="Total Staff",
        compute="_compute_staff_role_counts",
        store=False,
    )
    medical_staff_count = fields.Integer(
        string="Medical Staff",
        compute="_compute_staff_role_counts",
        store=False,
    )
    dental_staff_count = fields.Integer(
        string="Dental Staff",
        compute="_compute_staff_role_counts",
        store=False,
    )
    logistics_staff_count = fields.Integer(
        string="Logistics Staff",
        compute="_compute_staff_role_counts",
        store=False,
    )
    translator_staff_count = fields.Integer(
        string="Translators / Interpreters",
        compute="_compute_staff_role_counts",
        store=False,
    )

    # ---------------- COMPUTES ----------------

    @api.depends("program_line_ids.community_id")
    def _compute_community_names(self):
        for rec in self:
            names = rec.program_line_ids.mapped("community_id.name")
            # Únicos + ordenados, ignorando vacíos
            names = sorted({n for n in names if n})
            rec.community_names = ", ".join(names)

    @api.depends("arrival_ids", "departure_ids")
    def _compute_flight_counts(self):
        for rec in self:
            rec.arrival_count = len(rec.arrival_ids)
            rec.departure_count = len(rec.departure_ids)

    @api.depends("hotel_booking_ids.stay_nights")
    def _compute_hotel_stats(self):
        for rec in self:
            rec.hotel_booking_count = len(rec.hotel_booking_ids)
            rec.total_stay_nights = int(sum(rec.hotel_booking_ids.mapped("stay_nights") or [0]))

    @api.depends("staff_ids.staff_role")
    def _compute_staff_role_counts(self):
        # Agrupación simple por tipo de rol. Se puede ajustar la lista luego si GB
        # quiere otros grupos o etiquetas.
        MEDICAL_ROLES = {
            "doctor",
            "doctor_1",
            "doctor_2",
            "doctor_3",
            "doctor_4",
            "doctor_5",
            "doctor_extra",
            "doctor_de_cobertura",
            "doctor_on_call",
            "pediatrician",
            "obgyn",
            "nurse",
            "paramedic",
            "physiotherapist",
        }
        DENTAL_ROLES = {
            "dentist_1",
            "dentist_2",
            "dentist_3",
            "dentist_4",
        }
        LOGISTICS_ROLES = {
            "driver",
            "driver_extra",
            "coord_assistant_1",
            "coord_assistant_2",
            "coord_assistant_3",
            "coord_assistant_4",
            "coord_assistant_5",
            "coord_assistant_extra",
            "emergency_vehicle",
        }
        TRANSLATOR_ROLES = {
            "translator",
            "translator_1",
            "translator_2",
            "interpreter",
        }

        for rec in self:
            staff = rec.staff_ids
            rec.staff_count = len(staff)
            rec.medical_staff_count = sum(1 for s in staff if s.staff_role in MEDICAL_ROLES)
            rec.dental_staff_count = sum(1 for s in staff if s.staff_role in DENTAL_ROLES)
            rec.logistics_staff_count = sum(1 for s in staff if s.staff_role in LOGISTICS_ROLES)
            rec.translator_staff_count = sum(1 for s in staff if s.staff_role in TRANSLATOR_ROLES)
