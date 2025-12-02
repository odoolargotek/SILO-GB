# -*- coding: utf-8 -*-
# Passenger list wizard and helpers

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class GBPassengerListWizard(models.TransientModel):
    _name = "gb.passenger.list.wizard"
    _description = "Select passengers from Brigade Roster / Staff"

    brigade_id = fields.Many2one(
        "gb.brigade",
        string="Brigade",
        required=True,
        readonly=True,
    )

    # Pasajeros desde el ROSTER (voluntarios / estudiantes)
    passenger_ids = fields.Many2many(
        comodel_name="gb.brigade.roster",
        relation="gb_passenger_list_wiz_roster_rel",
        column1="wizard_id",
        column2="roster_id",
        string="Roster Passengers",
        domain="[('brigade_id', '=', brigade_id)]",
        help="Select passengers from the brigade roster.",
    )

    # Pasajeros STAFF seleccionados (modelo gb.brigade.staff)
    # Tabla de relación NUEVA para evitar conflictos de FK:
    #   gb_passenger_list_wiz_staff_rel2
    staff_ids = fields.Many2many(
        comodel_name="gb.brigade.staff",
        relation="gb_passenger_list_wiz_staff_rel2",
        column1="wizard_id",
        column2="staff_id",
        string="Staff Passengers",
        domain="[('brigade_id', '=', brigade_id)]",
        help="Select staff members that will also travel (only used for Transport).",
    )

    # ------------------------------------------------------------------
    # Botones del wizard
    # ------------------------------------------------------------------
    def action_select_all(self):
        """Marcar todos los pasajeros del roster (y staff en transporte)."""
        for wizard in self:
            if not wizard.brigade_id:
                continue

            # Siempre marcamos todo el roster
            wizard.passenger_ids = [(6, 0, wizard.brigade_id.roster_ids.ids)]

            # Si el wizard viene desde transporte, también marcamos todo el staff
            active_model = self.env.context.get("active_model")
            if active_model == "gb.brigade.transport":
                wizard.staff_ids = [(6, 0, wizard.brigade_id.staff_ids.ids)]
        return True

    def action_clear_all(self):
        """Desmarcar todos los pasajeros (roster + staff)."""
        for wizard in self:
            wizard.passenger_ids = [(5, 0, 0)]
            wizard.staff_ids = [(5, 0, 0)]
        return True

    def action_apply(self):
        """
        Aplicar la selección al Arrival/Departure/Transport activo.

        - Arrivals / Departures: solo usan roster (comportamiento original).
        - Transport: usa roster en passenger_ids y staff en staff_passenger_ids.
        """
        self.ensure_one()
        active_model = self.env.context.get("active_model")
        active_id = self.env.context.get("active_id")
        if not active_model or not active_id:
            return {"type": "ir.actions.act_window_close"}

        rec = self.env[active_model].browse(active_id).exists()
        if not rec:
            return {"type": "ir.actions.act_window_close"}

        # Caso 1: Arrivals / Departures (se mantiene lógica original)
        if active_model in ("gb.brigade.arrival", "gb.brigade.departure"):
            rec.passenger_ids = [(6, 0, self.passenger_ids.ids)]

        # Caso 2: Transport - soporta roster + staff
        elif active_model == "gb.brigade.transport":
            # Cabecera del transporte: pasajeros desde ROSTER
            if "passenger_ids" in rec._fields:
                rec.passenger_ids = [(6, 0, self.passenger_ids.ids)]

            # Si el modelo tiene campo staff_passenger_ids, lo alimentamos
            if "staff_passenger_ids" in rec._fields:
                rec.staff_passenger_ids = [(6, 0, self.staff_ids.ids)]

        # Otros modelos que pudieran reutilizar el wizard en el futuro
        else:
            # Comportamiento conservador: solo roster
            if "passenger_ids" in rec._fields:
                rec.passenger_ids = [(6, 0, self.passenger_ids.ids)]

        return {"type": "ir.actions.act_window_close"}


class GBBrigadeArrival(models.Model):
    _inherit = "gb.brigade.arrival"

    def action_open_passenger_wizard(self):
        """Botón 'Seleccionar' en arrivals."""
        self.ensure_one()
        if not self.brigade_id or not self.brigade_id.roster_ids:
            raise UserError(
                _(
                    "El roster de esta brigada está vacío.\n\n"
                    "Primero agregue participantes en la pestaña 'ROSTER' "
                    "y luego vuelva a abrir la lista de pasajeros."
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
            },
        }

    def action_add_all_passengers(self):
        """Botón 'Todos' en arrivals: mete todo el roster en passenger_ids."""
        for rec in self:
            if rec.brigade_id:
                rec.passenger_ids = [(6, 0, rec.brigade_id.roster_ids.ids)]
        return True


class GBBrigadeDeparture(models.Model):
    _inherit = "gb.brigade.departure"

    def action_open_passenger_wizard(self):
        """Botón 'Seleccionar' en departures."""
        self.ensure_one()
        if not self.brigade_id or not self.brigade_id.roster_ids:
            raise UserError(
                _(
                    "El roster de esta brigada está vacío.\n\n"
                    "Primero agregue participantes en la pestaña 'ROSTER' "
                    "y luego vuelva a abrir la lista de pasajeros."
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
            },
        }

    def action_add_all_passengers(self):
        """Botón 'Todos' en departures: mete todo el roster en passenger_ids."""
        for rec in self:
            if rec.brigade_id:
                rec.passenger_ids = [(6, 0, rec.brigade_id.roster_ids.ids)]
        return True
