# -*- coding: utf-8 -*-
# License LGPL-3.0

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AddParticipantsWizard(models.TransientModel):
    _name = "gb.add.participants.wizard"
    _description = "Add Participants to Activity"

    activity_id = fields.Many2one(
        "gb.brigade.activity",
        string="Activity",
        required=True,
    )

    brigade_id = fields.Many2one(
        "gb.brigade",
        string="Brigade",
        related="activity_id.brigade_id",
        store=False,
        readonly=True,
    )

    participant_ids = fields.Many2many(
        "gb.brigade.roster",
        "gb_add_participants_wizard_rel",
        "wizard_id",
        "roster_id",
        string="Select Participants",
        domain="[('brigade_id', '=', brigade_id)]",
        help="Select participants from the current Brigade Roster.",
    )

    @api.model
    def default_get(self, fields_list):
        """
        Pre-cargar el wizard con los que ya están asignados
        en la actividad actual.
        """
        res = super().default_get(fields_list)
        active_activity = self.env.context.get("default_activity_id")
        if active_activity:
            activity = self.env["gb.brigade.activity"].browse(active_activity)
            res["activity_id"] = activity.id
            res["participant_ids"] = [(6, 0, activity.participant_ids.ids)]
        return res

    def action_add_selected(self):
        """
        Botón 'Add Selected' en el wizard:
        agrega los seleccionados a la actividad.
        """
        self.ensure_one()
        if not self.activity_id:
            raise UserError(_("No activity linked."))

        current_ids = self.activity_id.participant_ids.ids
        new_ids = list(set(current_ids + self.participant_ids.ids))

        self.activity_id.participant_ids = [(6, 0, new_ids)]
        return {"type": "ir.actions.act_window_close"}
