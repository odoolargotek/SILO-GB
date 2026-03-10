# -*- coding: utf-8 -*-

# LT Brigade Module - Program Models
# Largotek SRL - Juan Luis Garvía - www.largotek.com
# License: LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import api, fields, models


class GBProgramTopic(models.Model):
    """Program Topic / Tag for classifying programs."""
    _name = "gb.program.topic"
    _description = "Program Topic / Tag"
    _order = "name"

    name = fields.Char(
        string="Topic Name",
        required=True,
        help="Name of the topic (e.g., Water Sanitation, Maternal Health, Nutrition, etc.)",
    )

    color = fields.Integer(
        string="Color Index",
        help="Color code for visual identification in tags",
    )

    description = fields.Text(
        string="Description",
        help="Optional description of what this topic covers",
    )

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Topic name must be unique!')
    ]


class GBBrigadeProgram(models.Model):
    """Brigade Program Line - Programs tab."""
    _name = "gb.brigade.program"
    _description = "Brigade Program Line"
    _order = "sequence, id"

    brigade_id = fields.Many2one(
        "gb.brigade",
        string="Brigade",
        ondelete="cascade",
        required=True,
    )

    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Order of this program line in the list.",
    )

    program_id = fields.Many2one(
        "gb.program",
        string="Program",
        required=True,
        help="Program type (Medical, Dental, Business, etc.) for this line.",
    )

    start_date = fields.Date(
        string="Start Date",
        help="When this program begins for this brigade.",
    )

    end_date = fields.Date(
        string="End Date",
        help="When this program ends for this brigade.",
    )

    community_id = fields.Many2one(
        "gb.community",
        string="Community",
        help="Community where this program activity will take place.",
    )

    location = fields.Char(
        string="Location / Community / Site",
        help="Where this program activity will take place.",
    )

    coordinator_id = fields.Many2one(
        "res.partner",
        string="Program Lead / Coordinator",
        help="Main staff contact for this program line.",
    )

    notes = fields.Char(
        string="Notes / Focus Area",
        help="Extra notes about this program line (focus, goals, etc.).",
    )

    topic_ids = fields.Many2many(
        "gb.program.topic",
        "gb_brigade_program_topic_rel",
        "program_id",
        "topic_id",
        string="Topic",
        help="Topics or focus areas for this program (e.g., Water Sanitation, Maternal Health, etc.)",
    )

    @api.onchange("community_id")
    def _onchange_community_id(self):
        """Auto-fill location field when community is selected."""
        for rec in self:
            rec.location = rec.community_id.name or False
