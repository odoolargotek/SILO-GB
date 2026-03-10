# -*- coding: utf-8 -*-

# LT Brigade Module - Activity Models
# Largotek SRL - Juan Luis Garvía - www.largotek.com
# License: LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import api, fields, models, _


class GBActivityTag(models.Model):
    """Activity Tag / Type for itinerary activities."""
    _name = "gb.activity.tag"
    _description = "Activity Tag / Type"
    _order = "name"
    
    name = fields.Char(string="Tag", required=True)
    color = fields.Integer(string="Color Index")


class GBBrigadeActivity(models.Model):
    """Brigade Activity / Itinerary entry."""
    _name = "gb.brigade.activity"
    _description = "Global Brigades - Brigade Activity / Itinerary Entry"
    _order = "start_datetime, id"
    
    brigade_id = fields.Many2one(
        "gb.brigade",
        string="Brigade",
        required=True,
        ondelete="cascade",
        help="Which brigade this activity belongs to.",
    )
    
    name = fields.Char(string="Nombre de la actividad", required=True)
    
    tag_ids = fields.Many2many(
        "gb.activity.tag",
        "gb_activity_tag_rel",
        "activity_id",
        "tag_id",
        string="Tipo de actividad",
        help="Labels / categories for this activity (clinic, travel, orientation, etc.).",
    )
    
    start_datetime = fields.Datetime(string="Inicio", help="Start datetime for this activity.")
    end_datetime = fields.Datetime(string="Fin", help="End datetime for this activity.")
    
    place = fields.Char(string="Lugar", help="Location where the activity takes place.")
    
    responsible_id = fields.Many2one(
        "res.partner",
        string="Responsable",
        help="Main person in charge of this activity.",
    )
    
    participant_ids = fields.Many2many(
        "gb.brigade.roster",
        "gb_activity_participant_rel",
        "activity_id",
        "roster_id",
        string="Participantes",
        help="Participants attending this activity.",
    )
    
    participant_count = fields.Integer(
        string="N°",
        compute="_compute_participant_count",
        store=False,
        help="How many participants are assigned to this activity.",
    )
    
    notes = fields.Text(string="Notas", help="Any notes / logistics / reminders for this activity.")
    
    @api.depends("participant_ids")
    def _compute_participant_count(self):
        for rec in self:
            rec.participant_count = len(rec.participant_ids)
    
    def action_add_all_participants(self):
        """Button 'Todos': adds all brigade roster to the activity."""
        for rec in self:
            if rec.brigade_id:
                all_roster = rec.brigade_id.roster_ids
                rec.participant_ids = [(6, 0, all_roster.ids)]
        return True
    
    def action_open_add_participants_wizard(self):
        """
        Button 'Seleccionar': opens existing wizard
        to manually select participants.
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Seleccionar Participantes"),
            "res_model": "gb.add.participants.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_activity_id": self.id,
            },
        }
