# -*- coding: utf-8 -*-
# License LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import api, fields, models


class GBProgram(models.Model):
    _name = "gb.program"
    _description = "Global Brigades - Program Catalog"
    _order = "name"

    name = fields.Char(string="Program Name", required=True)
    code = fields.Char(string="Code")
    active = fields.Boolean(default=True)
    description = fields.Text(string="Description")

    # (opcional) definir un coordinador por defecto del programa
    default_coordinator_id = fields.Many2one(
        "res.partner",
        string="Default Coordinator",
        help="Default staff contact for this program."
    )

    _sql_constraints = [
        ("gb_program_code_uniq", "unique(code)", "Program code must be unique.")
    ]
